import os
import secrets
import uuid

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.db.models import Count, F, Q
from core.utils import post_count_subqueries
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import LaravelStylePagination
from core.utils import check_rate_limit, hash_ip
from races.models import Race
from races.serializers import UpcomingRaceSerializer

from .models import Post, PostComment, PostLike
from .serializers import (
    CommentCreateSerializer,
    CommentDeleteSerializer,
    CommentUpdateSerializer,
    PostCommentSerializer,
    PostCreateSerializer,
    PostListSerializer,
    PostSerializer,
    PostUpdateSerializer,
)


class PostListCreateView(APIView):
    """GET /api/v1/posts/ + POST /api/v1/posts/"""

    def get(self, request):
        search = request.query_params.get('search')
        category = request.query_params.get('category')
        sort = request.query_params.get('sort', 'latest')
        comment_count_sq, like_count_sq = post_count_subqueries()
        qs = Post.objects.prefetch_related('races').annotate(
            _comment_count=comment_count_sq,
            _like_count=like_count_sq,
        )

        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )

        if category:
            qs = qs.filter(category=category)

        if sort == 'popular':
            qs = qs.order_by('-view_count', '-created_at')
        else:
            qs = qs.order_by('-created_at')

        paginator = LaravelStylePagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = PostListSerializer(
            page, many=True,
            context={'include_tagged_races': True},
        )

        response_data = paginator.get_paginated_response(serializer.data).data
        response_data['search'] = search
        response_data['category'] = category
        response_data['sort'] = sort

        # Sidebar data
        from datetime import timedelta
        seven_days_ago = timezone.now() - timedelta(days=7)
        popular_qs = Post.objects.prefetch_related('races').annotate(
            _comment_count=comment_count_sq,
            _like_count=like_count_sq,
        ).filter(
            created_at__gte=seven_days_ago,
        ).order_by('-view_count')[:5]
        upcoming_races = Race.objects.upcoming()[:5]

        response_data['sidebar'] = {
            'popularPosts': PostListSerializer(
                popular_qs, many=True,
                context={'include_tagged_races': False},
            ).data,
            'upcomingRaces': UpcomingRaceSerializer(upcoming_races, many=True).data,
        }

        return Response(response_data)

    def post(self, request):
        ip_hash = hash_ip(request)

        # Rate limit: 10/hour
        allowed, _ = check_rate_limit(ip_hash, 'post', 10, 3600)
        if not allowed:
            return Response(
                {'errors': {'post': ['글 작성 제한에 도달했습니다. 잠시 후 다시 시도해주세요.']}},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        is_authenticated = request.user and request.user.is_authenticated
        serializer = PostCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        data = serializer.validated_data

        # Validate image uploads
        images_files = request.FILES.getlist('images')
        if images_files:
            error = self._validate_images(images_files)
            if error:
                return Response(
                    {'errors': {'images': [error]}},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

        password_hash = make_password(data['password']) if data.get('password') else ''

        post = Post.objects.create(
            user=request.user if is_authenticated else None,
            nickname=data.get('nickname') or None,
            title=data['title'],
            content=data['content'],
            category=data.get('category') or None,
            password=password_hash,
            ip_hash=ip_hash,
        )

        # Save images with post_id directory
        if images_files:
            image_paths = self._save_images(images_files, post.id)
            Post.objects.filter(pk=post.pk).update(images=image_paths)
            post.images = image_paths

        # Attach races
        race_ids = data.get('race_ids')
        if race_ids:
            post.races.set(race_ids)

        post.refresh_from_db()
        return Response({
            'success': True,
            'message': '글이 등록되었습니다.',
            'post': PostSerializer(
                post,
                context={'include_tagged_races': True, 'request': request},
            ).data,
            'redirect': f'/posts/{post.id}',
        }, status=status.HTTP_201_CREATED)

    def _validate_images(self, files):
        if len(files) > 5:
            return '이미지는 최대 5개까지 첨부 가능합니다.'
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        max_size = 5 * 1024 * 1024  # 5MB
        for f in files:
            if f.content_type not in allowed_types:
                return '지원되는 이미지 형식: jpeg, png, gif, webp'
            if f.size > max_size:
                return '이미지 크기는 최대 5MB까지 가능합니다.'
        return None

    def _save_images(self, files, post_id):
        save_dir = os.path.join(str(settings.MEDIA_ROOT), 'posts', str(post_id))
        os.makedirs(save_dir, exist_ok=True)
        paths = []
        for f in files:
            ext = os.path.splitext(f.name)[1] or '.jpg'
            filename = f'{uuid.uuid4().hex[:12]}{ext}'
            filepath = os.path.join(save_dir, filename)
            with open(filepath, 'wb') as dest:
                for chunk in f.chunks():
                    dest.write(chunk)
            paths.append(f'posts/{post_id}/{filename}')
        return paths


class PostInlineImageUploadView(APIView):
    """POST /api/v1/posts/upload-image/"""

    ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    MAX_SIZE = 5 * 1024 * 1024  # 5MB

    def post(self, request):
        ip_hash = hash_ip(request)

        # Rate limit: 30/hour
        allowed, _ = check_rate_limit(ip_hash, 'inline_image', 30, 3600)
        if not allowed:
            return Response(
                {'error': '이미지 업로드 제한에 도달했습니다. 잠시 후 다시 시도해주세요.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        image = request.FILES.get('image')
        if not image:
            return Response(
                {'error': '이미지 파일을 선택해주세요.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if image.content_type not in self.ALLOWED_TYPES:
            return Response(
                {'error': '지원되는 이미지 형식: jpeg, png, gif, webp'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if image.size > self.MAX_SIZE:
            return Response(
                {'error': '이미지 크기는 최대 5MB까지 가능합니다.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Save to storage/posts/inline/{YYYY-MM}/{uuid12}.{ext}
        now = timezone.now()
        month_dir = now.strftime('%Y-%m')
        save_dir = os.path.join(str(settings.MEDIA_ROOT), 'posts', 'inline', month_dir)
        os.makedirs(save_dir, exist_ok=True)

        ext = os.path.splitext(image.name)[1].lower() or '.jpg'
        filename = f'{uuid.uuid4().hex[:12]}{ext}'
        filepath = os.path.join(save_dir, filename)

        with open(filepath, 'wb') as dest:
            for chunk in image.chunks():
                dest.write(chunk)

        url = f'/storage/posts/inline/{month_dir}/{filename}'
        return Response({'url': url}, status=status.HTTP_201_CREATED)


class PostAvailableRacesView(APIView):
    """GET /api/v1/posts/races/"""

    def get(self, request):
        races = Race.objects.upcoming()[:100]
        return Response({
            'races': UpcomingRaceSerializer(races, many=True).data,
        })


class PostDetailUpdateDeleteView(APIView):
    """GET/PUT/DELETE /api/v1/posts/{id}/"""

    def get(self, request, pk):
        try:
            post = Post.objects.prefetch_related(
                'races',
                'comments__replies',
            ).get(pk=pk)
        except Post.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Increment view count
        post.increment_view_count()

        # Check like status
        ip_hash = hash_ip(request)
        has_liked = PostLike.objects.filter(post=post, ip_hash=ip_hash).exists()

        # Previous and next posts
        prev_post = Post.objects.filter(created_at__lt=post.created_at).order_by('-created_at').first()
        next_post = Post.objects.filter(created_at__gt=post.created_at).order_by('created_at').first()

        # Sidebar data
        from datetime import timedelta
        seven_days_ago = timezone.now() - timedelta(days=7)
        comment_count_sq, like_count_sq = post_count_subqueries()
        popular_qs = Post.objects.prefetch_related('races').annotate(
            _comment_count=comment_count_sq,
            _like_count=like_count_sq,
        ).filter(
            created_at__gte=seven_days_ago,
        ).order_by('-view_count')[:5]
        upcoming_races = Race.objects.upcoming()[:5]

        return Response({
            'post': PostSerializer(
                post,
                context={
                    'include_tagged_races': True,
                    'include_comments': True,
                    'request': request,
                },
            ).data,
            'hasLiked': has_liked,
            'prevPost': {'id': prev_post.id, 'title': prev_post.title} if prev_post else None,
            'nextPost': {'id': next_post.id, 'title': next_post.title} if next_post else None,
            'sidebar': {
                'popularPosts': PostListSerializer(
                    popular_qs, many=True,
                    context={'include_tagged_races': False},
                ).data,
                'upcomingRaces': UpcomingRaceSerializer(upcoming_races, many=True).data,
            }
        })

    def put(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Check authorization: either authenticated owner or edit token
        is_owner = (
            request.user and request.user.is_authenticated
            and post.user_id and post.user_id == request.user.id
        )

        serializer = PostUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        data = serializer.validated_data
        edit_token = ''

        if not is_owner:
            # Verify edit token for non-owner
            edit_token = data.get('edit_token', '')
            if not edit_token:
                return Response(
                    {'errors': {'password': ['수정 권한이 없습니다.']}},
                    status=status.HTTP_403_FORBIDDEN,
                )
            cache_key = f'edit_token:{post.pk}:{edit_token}'
            if not cache.get(cache_key):
                return Response(
                    {'errors': {'password': ['수정 권한이 없습니다.']}},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Handle images
        existing_images = data.get('existing_images') or []
        new_files = request.FILES.getlist('images')
        total_images = len(existing_images) + len(new_files)
        if total_images > 5:
            return Response(
                {'errors': {'images': ['이미지는 최대 5개까지 첨부 가능합니다.']}},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # Remove old images not in existing_images
        if post.images:
            for old_path in post.images:
                if old_path not in existing_images:
                    full_path = os.path.join(str(settings.MEDIA_ROOT), old_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)

        # Save new images
        new_paths = []
        if new_files:
            save_dir = os.path.join(str(settings.MEDIA_ROOT), 'posts', str(post.pk))
            os.makedirs(save_dir, exist_ok=True)
            for f in new_files:
                ext = os.path.splitext(f.name)[1] or '.jpg'
                filename = f'{uuid.uuid4().hex[:12]}{ext}'
                filepath = os.path.join(save_dir, filename)
                with open(filepath, 'wb') as dest:
                    for chunk in f.chunks():
                        dest.write(chunk)
                new_paths.append(f'posts/{post.pk}/{filename}')

        all_images = existing_images + new_paths

        # Update post
        Post.objects.filter(pk=post.pk).update(
            nickname=data.get('nickname') or None,
            title=data['title'],
            content=data['content'],
            category=data.get('category') or None,
            images=all_images or None,
        )

        # Sync races
        race_ids = data.get('race_ids') or []
        post.races.set(race_ids)

        # Invalidate edit token after successful update
        if not is_owner and edit_token:
            cache.delete(f'edit_token:{post.pk}:{edit_token}')

        post.refresh_from_db()
        return Response({
            'success': True,
            'message': '글이 수정되었습니다.',
            'post': PostSerializer(
                post,
                context={'include_tagged_races': True},
            ).data,
            'redirect': f'/posts/{post.id}',
        })

    def delete(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        is_owner = (
            request.user and request.user.is_authenticated
            and post.user_id and post.user_id == request.user.id
        )

        if not is_owner:
            password = request.data.get('password', '')
            if not post.check_password(password):
                return Response(
                    {'errors': {'password': ['비밀번호가 일치하지 않습니다.']}},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Delete image files
        if post.images:
            for img_path in post.images:
                full_path = os.path.join(str(settings.MEDIA_ROOT), img_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
            # Remove directory
            post_dir = os.path.join(str(settings.MEDIA_ROOT), 'posts', str(post.pk))
            if os.path.isdir(post_dir):
                import shutil
                shutil.rmtree(post_dir, ignore_errors=True)

        post.delete()
        return Response({
            'success': True,
            'message': '글이 삭제되었습니다.',
            'redirect': '/posts',
        })


class PostVerifyPasswordView(APIView):
    """POST /api/v1/posts/{id}/verify-password/"""

    def post(self, request, pk):
        try:
            post = Post.objects.prefetch_related('races').get(pk=pk)
        except Post.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        is_owner = (
            request.user and request.user.is_authenticated
            and post.user_id and post.user_id == request.user.id
        )

        if not is_owner:
            password = request.data.get('password', '')
            if not post.check_password(password):
                return Response(
                    {'errors': {'password': ['비밀번호가 일치하지 않습니다.']}},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Generate edit token (valid for 5 minutes)
        edit_token = secrets.token_hex(32)
        cache.set(f'edit_token:{post.pk}:{edit_token}', True, 300)

        # Available races for tagging
        upcoming_races = Race.objects.upcoming()[:100]
        tagged_race_ids = list(post.races.values_list('id', flat=True))

        # Combine upcoming + already tagged (deduplicated)
        all_race_ids = set(r.id for r in upcoming_races) | set(tagged_race_ids)
        all_races = Race.objects.filter(id__in=all_race_ids).order_by('race_date')

        return Response({
            'success': True,
            'post': PostSerializer(
                post,
                context={'include_tagged_races': True},
            ).data,
            'races': UpcomingRaceSerializer(all_races, many=True).data,
            'editToken': edit_token,
        })


class CommentCreateView(APIView):
    """POST /api/v1/posts/{id}/comments/"""

    def post(self, request, post_id):
        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        ip_hash = hash_ip(request)

        # Rate limit: 10/10min
        allowed, _ = check_rate_limit(ip_hash, 'comment', 10, 600)
        if not allowed:
            return Response(
                {'errors': {'comment': ['댓글 작성 제한에 도달했습니다. 잠시 후 다시 시도해주세요.']}},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        is_authenticated = request.user and request.user.is_authenticated
        serializer = CommentCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        data = serializer.validated_data
        parent_id = data.get('parent_id')

        if parent_id:
            try:
                parent = PostComment.objects.get(pk=parent_id)
            except PostComment.DoesNotExist:
                return Response(
                    {'errors': {'comment': ['잘못된 요청입니다.']}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if parent.post_id != post.pk:
                return Response(
                    {'errors': {'comment': ['잘못된 요청입니다.']}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if parent.parent_id is not None:
                return Response(
                    {'errors': {'comment': ['대댓글에는 답글을 달 수 없습니다.']}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            parent = None

        password_hash = make_password(data['password']) if data.get('password') else ''

        comment = PostComment.objects.create(
            post=post,
            parent=parent,
            user=request.user if is_authenticated else None,
            nickname=data.get('nickname') or None,
            content=data['content'],
            password=password_hash,
            ip_hash=ip_hash,
        )

        return Response({
            'success': True,
            'message': '댓글이 등록되었습니다.',
            'comment': PostCommentSerializer(comment, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


class CommentUpdateDeleteView(APIView):
    """PUT/DELETE /api/v1/posts/{id}/comments/{commentId}/"""

    def put(self, request, post_id, comment_id):
        try:
            comment = PostComment.objects.get(pk=comment_id, post_id=post_id)
        except PostComment.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        is_owner = (
            request.user and request.user.is_authenticated
            and comment.user_id and comment.user_id == request.user.id
        )

        serializer = CommentUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        data = serializer.validated_data

        if not is_owner:
            if not comment.check_password(data.get('password', '')):
                return Response(
                    {'errors': {'password': ['비밀번호가 일치하지 않습니다.']}},
                    status=status.HTTP_403_FORBIDDEN,
                )

        PostComment.objects.filter(pk=comment.pk).update(content=data['content'])
        comment.refresh_from_db()

        return Response({
            'success': True,
            'message': '댓글이 수정되었습니다.',
            'comment': PostCommentSerializer(comment, context={'request': request}).data,
        })

    def delete(self, request, post_id, comment_id):
        try:
            comment = PostComment.objects.get(pk=comment_id, post_id=post_id)
        except PostComment.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        is_owner = (
            request.user and request.user.is_authenticated
            and comment.user_id and comment.user_id == request.user.id
        )

        if not is_owner:
            serializer = CommentDeleteSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            if not comment.check_password(serializer.validated_data.get('password', '')):
                return Response(
                    {'errors': {'password': ['비밀번호가 일치하지 않습니다.']}},
                    status=status.HTTP_403_FORBIDDEN,
                )

        comment.delete()
        return Response({
            'success': True,
            'message': '댓글이 삭제되었습니다.',
        })


class PostLikeToggleView(APIView):
    """POST /api/v1/posts/{id}/like/"""

    def post(self, request, post_id):
        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        ip_hash = hash_ip(request)

        existing = PostLike.objects.filter(post=post, ip_hash=ip_hash).first()
        if existing:
            # Unlike (no rate limit for unlike)
            existing.delete()
            like_count = PostLike.objects.filter(post=post).count()
            return Response({
                'success': True,
                'liked': False,
                'likeCount': like_count,
            })
        else:
            # Like with rate limit: 20/hour
            allowed, _ = check_rate_limit(ip_hash, 'like', 20, 3600)
            if not allowed:
                return Response({
                    'success': False,
                    'message': '추천 횟수 제한에 도달했습니다. 잠시 후 다시 시도해주세요.',
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            PostLike.objects.create(post=post, ip_hash=ip_hash)
            like_count = PostLike.objects.filter(post=post).count()
            return Response({
                'success': True,
                'liked': True,
                'likeCount': like_count,
            })
