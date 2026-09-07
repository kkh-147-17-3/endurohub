from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils import check_rate_limit, hash_ip
from .models import POPUP_CACHE_KEY, Notice, NoticeComment, Popup
from .serializers import (
    NoticeCommentCreateSerializer,
    NoticeCommentDeleteSerializer,
    NoticeCommentSerializer,
    NoticeCommentUpdateSerializer,
    NoticeDetailSerializer,
    NoticeListSerializer,
    PopupSerializer,
)

VALID_TABS = {'notice', 'racenews', 'event', 'urgent'}


def _sort_key(notice):
    """Mirror getSortedNotices() in the frontend:
    pinned first (urgent-pinned before regular pinned), then newest first.
    """
    return (
        0 if notice.pinned else 1,
        0 if (notice.pinned and notice.is_urgent) else 1,
        -notice.published_at.timestamp(),
    )


def _sorted_notices():
    return sorted(Notice.objects.all(), key=_sort_key)


class NoticeListView(APIView):
    """GET /api/v1/notices/?tab= — full sorted list + per-category counts."""

    def get(self, request):
        notices = _sorted_notices()

        counts = {
            'all': len(notices),
            'notice': 0,
            'racenews': 0,
            'event': 0,
            'urgent': 0,
        }
        for n in notices:
            if n.category in counts:
                counts[n.category] += 1

        tab = request.query_params.get('tab')
        if tab in VALID_TABS:
            notices = [n for n in notices if n.category == tab]

        data = NoticeListSerializer(notices, many=True).data
        return Response({'data': data, 'counts': counts})


class NoticeDetailView(APIView):
    """GET /api/v1/notices/<pk>/ — detail + prev/next, increments view count."""

    def get(self, request, pk):
        try:
            notice = Notice.objects.get(pk=pk)
        except Notice.DoesNotExist:
            return Response({'detail': '공지사항을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        return _notice_detail_response(notice, request)


class NoticeSlugDetailView(APIView):
    """GET /api/v1/notices/by-slug/<slug>/ — custom notice page view tracking."""

    def get(self, request, slug):
        try:
            notice = Notice.objects.get(slug=slug)
        except Notice.DoesNotExist:
            return Response({'detail': '공지사항을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        return _notice_detail_response(notice, request)


def _notice_detail_response(notice, request):
    """Increment and serialize a notice shared by numeric and custom routes."""

    notice.increment_view_count()
    notice.view_count += 1  # reflect the increment in this response

    ordered = _sorted_notices()
    idx = next((i for i, n in enumerate(ordered) if n.pk == notice.pk), None)
    prev_notice = ordered[idx - 1] if idx is not None and idx > 0 else None
    next_notice = ordered[idx + 1] if idx is not None and idx < len(ordered) - 1 else None

    def adjacent(n):
        if n is None:
            return None
        return {
            'id': n.id,
            'href': f'/notice/{n.slug}' if n.slug else None,
            'title': n.title,
            'date': n.published_at.strftime('%Y·%m·%d') if n.published_at else '',
        }

    # 이벤트 공지는 배너(Popup)를 달 수 있다 — 상세 상단 히어로로 렌더된다.
    popup = notice.popups.order_by('-priority', '-id').first()

    return Response({
        'notice': NoticeDetailSerializer(notice, context={'request': request}).data,
        'adjacent': {'prev': adjacent(prev_notice), 'next': adjacent(next_notice)},
        'event': PopupSerializer(popup).data if popup else None,
    })


class NoticeCommentCreateView(APIView):
    """POST /api/v1/notices/{id}/comments/"""

    def post(self, request, notice_id):
        try:
            notice = Notice.objects.get(pk=notice_id)
        except Notice.DoesNotExist:
            return Response({'detail': '공지사항을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        ip_hash = hash_ip(request)
        allowed, _ = check_rate_limit(ip_hash, 'comment', 10, 600)
        if not allowed:
            return Response(
                {'errors': {'comment': ['댓글 작성 제한에 도달했습니다. 잠시 후 다시 시도해주세요.']}},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        serializer = NoticeCommentCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        data = serializer.validated_data
        parent_id = data.get('parent_id')
        if parent_id:
            try:
                parent = NoticeComment.objects.get(pk=parent_id)
            except NoticeComment.DoesNotExist:
                return Response({'errors': {'comment': ['잘못된 요청입니다.']}}, status=status.HTTP_400_BAD_REQUEST)
            if parent.notice_id != notice.pk:
                return Response({'errors': {'comment': ['잘못된 요청입니다.']}}, status=status.HTTP_400_BAD_REQUEST)
            if parent.parent_id is not None:
                return Response(
                    {'errors': {'comment': ['대댓글에는 답글을 달 수 없습니다.']}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            parent = None

        is_authenticated = request.user and request.user.is_authenticated
        comment = NoticeComment.objects.create(
            notice=notice,
            parent=parent,
            user=request.user if is_authenticated else None,
            nickname=data.get('nickname') or None,
            content=data['content'],
            password=make_password(data['password']) if data.get('password') else '',
            ip_hash=ip_hash,
        )
        return Response({
            'success': True,
            'message': '댓글이 등록되었습니다.',
            'comment': NoticeCommentSerializer(comment, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


class NoticeCommentUpdateDeleteView(APIView):
    """PUT/DELETE /api/v1/notices/{id}/comments/{commentId}/"""

    @staticmethod
    def get_comment(notice_id, comment_id):
        try:
            return NoticeComment.objects.get(pk=comment_id, notice_id=notice_id)
        except NoticeComment.DoesNotExist:
            return None

    @staticmethod
    def is_owner(request, comment):
        return bool(
            request.user and request.user.is_authenticated
            and comment.user_id and comment.user_id == request.user.id
        )

    def put(self, request, notice_id, comment_id):
        comment = self.get_comment(notice_id, comment_id)
        if not comment:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = NoticeCommentUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        if not self.is_owner(request, comment) and not comment.check_password(serializer.validated_data['password']):
            return Response({'errors': {'password': ['비밀번호가 일치하지 않습니다.']}}, status=status.HTTP_403_FORBIDDEN)

        comment.content = serializer.validated_data['content']
        comment.save(update_fields=['content', 'updated_at'])
        return Response({
            'success': True,
            'message': '댓글이 수정되었습니다.',
            'comment': NoticeCommentSerializer(comment, context={'request': request}).data,
        })

    def delete(self, request, notice_id, comment_id):
        comment = self.get_comment(notice_id, comment_id)
        if not comment:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not self.is_owner(request, comment):
            serializer = NoticeCommentDeleteSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({'errors': serializer.errors}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            if not comment.check_password(serializer.validated_data['password']):
                return Response({'errors': {'password': ['비밀번호가 일치하지 않습니다.']}}, status=status.HTTP_403_FORBIDDEN)

        comment.delete()
        return Response({'success': True, 'message': '댓글이 삭제되었습니다.'})


class PopupActiveView(APIView):
    """GET /api/v1/popups/active/ — 지금 게시기간 안인 팝업 배너 (없으면 null).

    전 페이지의 레이아웃 로드에서 호출되므로 Redis 에 60초 캐시한다.
    관리자에서 저장하면 Popup.save() 가 키를 지우므로 즉시 반영된다.
    """

    CACHE_TTL = 60

    def get(self, request):
        cached = cache.get(POPUP_CACHE_KEY)
        if cached is not None:
            return Response(cached)

        popup = Popup.live()
        payload = {'popup': PopupSerializer(popup).data if popup else None}
        cache.set(POPUP_CACHE_KEY, payload, self.CACHE_TTL)
        return Response(payload)
