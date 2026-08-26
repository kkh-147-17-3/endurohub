from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import POPUP_CACHE_KEY, Notice, Popup
from .serializers import NoticeDetailSerializer, NoticeListSerializer, PopupSerializer

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
                'title': n.title,
                'date': n.published_at.strftime('%Y·%m·%d') if n.published_at else '',
            }

        # 이벤트 공지는 배너(Popup)를 달 수 있다 — 상세 상단 히어로로 렌더된다.
        popup = notice.popups.order_by('-priority', '-id').first()

        return Response({
            'notice': NoticeDetailSerializer(notice).data,
            'adjacent': {'prev': adjacent(prev_notice), 'next': adjacent(next_notice)},
            'event': PopupSerializer(popup).data if popup else None,
        })


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
