import os
import uuid
from collections import defaultdict
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.db.models import Avg, Count, F, Q
from core.utils import post_count_subqueries
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import LaravelStylePagination
from core.utils import check_rate_limit, hash_ip
from posts.models import Post
from posts.serializers import PostListSerializer

from .constants import DISTANCE_CATEGORIES, REGIONS, SPORTS
from .models import DeviceToken, Race, RacePendingChange, Review
from .serializers import (
    DeviceTokenCreateSerializer,
    DeviceTokenSerializer,
    DeviceTokenUpdateSerializer,
    RaceSerializer,
    ReviewCreateSerializer,
    ReviewSerializer,
    UpcomingRaceSerializer,
)


class HomeView(APIView):
    CACHE_KEY = 'home_page_data'
    CACHE_TTL = 300  # 5 minutes

    def get(self, request):
        cached = cache.get(self.CACHE_KEY)
        if cached:
            return Response(cached)

        today = timezone.now().date()

        closing_soon = Race.objects.closing_soon(7).exclude(
            title__contains='(취소)'
        )[:6]

        upcoming_races = Race.objects.upcoming().exclude(
            title__contains='(취소)'
        )[:12]

        recently_added = Race.objects.order_by('-created_at')[:8]

        comment_count_sq, like_count_sq = post_count_subqueries()
        recent_posts = Post.objects.prefetch_related('races').annotate(
            _comment_count=comment_count_sq,
            _like_count=like_count_sq,
        ).order_by('-created_at')[:5]

        sport_counts_qs = Race.objects.upcoming().order_by().values('sport').annotate(
            count=Count('id')
        )
        sport_counts = {item['sport']: item['count'] for item in sport_counts_qs}

        total_upcoming = Race.objects.registration_open().count()

        data = {
            'closingSoon': RaceSerializer(closing_soon, many=True).data,
            'upcomingRaces': RaceSerializer(upcoming_races, many=True).data,
            'recentlyAdded': RaceSerializer(recently_added, many=True).data,
            'recentPosts': PostListSerializer(
                recent_posts, many=True,
                context={'include_tagged_races': True},
            ).data,
            'sportCounts': sport_counts,
            'totalUpcoming': total_upcoming,
        }
        cache.set(self.CACHE_KEY, data, self.CACHE_TTL)
        return Response(data)


class RaceListView(APIView):
    def get(self, request):
        sport = request.query_params.getlist('sport', [])
        if not sport:
            sport_single = request.query_params.get('sport')
            if sport_single:
                sport = [sport_single]

        region = request.query_params.getlist('region', [])
        if not region:
            region_single = request.query_params.get('region')
            if region_single:
                region = [region_single]

        status_filter = request.query_params.getlist('status', [])
        if not status_filter:
            status_single = request.query_params.get('status')
            if status_single:
                status_filter = [status_single]

        name = request.query_params.get('name')
        distance_category = request.query_params.getlist('distance_category', [])
        if not distance_category:
            dc_single = request.query_params.get('distance_category')
            if dc_single:
                distance_category = [dc_single]

        month_from = request.query_params.get('month_from', timezone.now().strftime('%Y-%m'))
        month_to = request.query_params.get('month_to')

        # Mobile-specific params
        upcoming_only = request.query_params.get('upcoming') == 'true'
        closing_soon_only = request.query_params.get('closing_soon') == 'true'
        days = int(request.query_params.get('days', 7))

        qs = Race.objects.all()

        if closing_soon_only:
            qs = Race.objects.closing_soon(days)
        elif upcoming_only:
            qs = Race.objects.upcoming()
        else:
            # Handle closing_soon in status filter specially
            has_closing_soon = 'closing_soon' in status_filter
            regular_statuses = [s for s in status_filter if s != 'closing_soon']

            if has_closing_soon and regular_statuses:
                closing_qs = Race.objects.closing_soon(7)
                status_qs = Race.objects.by_status(regular_statuses)
                qs = (closing_qs | status_qs).distinct()
            elif has_closing_soon:
                qs = Race.objects.closing_soon(7)
            elif regular_statuses:
                qs = qs.by_status(regular_statuses)

            if sport:
                qs = qs.by_sport(sport)
            if region:
                qs = qs.by_region(region)
            if name:
                qs = qs.by_name(name)

            # Distance category only when exactly 1 sport selected
            if distance_category and len(sport) == 1:
                qs = qs.by_distance_category(sport[0], distance_category)

            if not closing_soon_only and not upcoming_only:
                qs = qs.by_month_range(month_from, month_to)

        paginator = LaravelStylePagination()
        per_page = request.query_params.get('per_page')
        if per_page:
            paginator.page_size = min(int(per_page), 100)

        page = paginator.paginate_queryset(qs, request)
        serializer = RaceSerializer(page, many=True)

        response_data = paginator.get_paginated_response(serializer.data).data
        response_data['filters'] = {
            'regions': REGIONS,
            'sports': SPORTS,
            'distanceCategories': DISTANCE_CATEGORIES,
        }
        response_data['applied'] = {
            'sport': sport,
            'region': region,
            'status': status_filter,
            'name': name,
            'distanceCategory': distance_category,
            'monthFrom': month_from,
            'monthTo': month_to,
        }

        return Response(response_data)


class RaceDetailView(APIView):
    def get(self, request, slug):
        try:
            if slug.isdigit():
                race = Race.objects.get(id=int(slug))
            else:
                race = Race.objects.get(slug=slug)
        except Race.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Increment view count
        Race.objects.filter(pk=race.pk).update(view_count=F('view_count') + 1)

        # Related races (slot-based, cached 10min)
        cache_key = f'related_races_{race.id}'
        related_race_slots = cache.get(cache_key)
        if related_race_slots is None:
            related_race_slots = self._get_related_races(race, request)
            cache.set(cache_key, related_race_slots, 600)

        # Related posts
        comment_count_sq, like_count_sq = post_count_subqueries()
        related_posts = Post.objects.filter(
            races=race
        ).annotate(
            _comment_count=comment_count_sq,
            _like_count=like_count_sq,
        ).order_by('-created_at')[:5]

        # Reviews
        reviews = Review.objects.filter(race=race).order_by('-created_at')
        review_stats = reviews.aggregate(
            count=Count('id'),
            average=Avg('rating'),
            average_operation_satisfaction=Avg('operation_satisfaction'),
        )

        # Difficulty distribution
        difficulty_dist = {}
        for entry in reviews.exclude(course_difficulty__isnull=True).values('course_difficulty').annotate(cnt=Count('id')):
            difficulty_dist[entry['course_difficulty']] = entry['cnt']

        # Check if current IP has reviewed
        ip_hash = hash_ip(request)
        has_reviewed = Review.objects.filter(race=race, ip_hash=ip_hash).exists()

        return Response({
            'race': RaceSerializer(race).data,
            'relatedRaces': [
                {
                    'label': slot['label'],
                    'races': RaceSerializer(slot['races'], many=True).data,
                }
                for slot in related_race_slots
            ],
            'relatedPosts': PostListSerializer(
                related_posts, many=True,
                context={'include_tagged_races': True},
            ).data,
            'reviews': ReviewSerializer(reviews, many=True).data,
            'reviewStats': {
                'count': review_stats['count'] or 0,
                'average': round(review_stats['average'] or 0, 1),
                'averageOperationSatisfaction': round(review_stats['average_operation_satisfaction'] or 0, 1),
                'difficultyDistribution': difficulty_dist,
            },
            'hasReviewed': has_reviewed,
        })

    def _get_related_races(self, race, request=None):
        from datetime import timedelta

        slots = []
        exclude_ids = {race.id}
        now = timezone.now().date()

        # Slot 1: 지금 접수 가능한 대회 (same sport, registration open by date)
        slot1_qs = Race.objects.filter(
            sport=race.sport,
            registration_start__lte=now,
            registration_end__gte=now,
        ).exclude(id__in=exclude_ids).order_by('registration_end')[:4]
        slot1_races = list(slot1_qs)
        exclude_ids.update(r.id for r in slot1_races)
        if slot1_races:
            slots.append({'label': '지금 접수 가능한 대회', 'races': slot1_races})

        # Slot 2: same region, 1-3 months later
        if race.region and race.race_date:
            slot2_qs = Race.objects.filter(
                region=race.region,
                race_date__gte=race.race_date + timedelta(days=30),
                race_date__lte=race.race_date + timedelta(days=90),
            ).exclude(id__in=exclude_ids).order_by('race_date')[:4]
            slot2_races = list(slot2_qs)
            exclude_ids.update(r.id for r in slot2_races)
            if slot2_races:
                slots.append({'label': f'{race.region}의 다른 대회', 'races': slot2_races})

        # Slot 3: same timeframe (+-2 weeks), different region
        if race.race_date:
            slot3_qs = Race.objects.filter(
                race_date__gte=race.race_date - timedelta(days=14),
                race_date__lte=race.race_date + timedelta(days=14),
            ).exclude(id__in=exclude_ids).exclude(
                region=race.region,
            ).order_by('race_date')[:4]
            slot3_races = list(slot3_qs)
            exclude_ids.update(r.id for r in slot3_races)
            if slot3_races:
                slots.append({'label': '비슷한 시기에 열리는 대회', 'races': slot3_races})

        # Slot 4: next distance category
        if race.distances and race.sport:
            next_cat = Race.get_next_distance_category(race.distances, race.sport)
            if next_cat:
                label = Race.get_distance_category_label(next_cat, race.sport)
                slot4_qs = Race.objects.filter(
                    sport=race.sport,
                ).exclude(id__in=exclude_ids)
                if hasattr(slot4_qs, 'by_distance_category'):
                    slot4_qs = slot4_qs.by_distance_category(race.sport, next_cat)[:4]
                else:
                    slot4_qs = slot4_qs.none()
                slot4_races = list(slot4_qs)
                if slot4_races and label:
                    slots.append({'label': f'{label} 대회에 도전해보세요', 'races': slot4_races})

        return slots


class RaceYearlyView(APIView):
    def get(self, request, year):
        year = int(year)
        races = Race.objects.filter(
            race_date__year=year,
        ).order_by('race_date')

        grouped = defaultdict(list)
        for race in races:
            month = str(race.race_date.month)
            grouped[month].append(RaceSerializer(race).data)

        return Response({
            'races': dict(grouped),
            'year': year,
            'totalCount': races.count(),
        })


class RaceCalendarView(APIView):
    def get(self, request):
        now = timezone.now()
        year = int(request.query_params.get('year', now.year))
        month = int(request.query_params.get('month', now.month))
        sport = request.query_params.get('sport')

        import calendar
        _, last_day = calendar.monthrange(year, month)
        start_date = f'{year}-{month:02d}-01'
        end_date = f'{year}-{month:02d}-{last_day}'

        qs = Race.objects.filter(
            race_date__gte=start_date,
            race_date__lte=end_date,
        ).order_by('race_date')

        if sport:
            qs = qs.by_sport(sport)

        grouped = defaultdict(list)
        for race in qs:
            date_key = race.race_date.strftime('%Y-%m-%d')
            grouped[date_key].append(RaceSerializer(race).data)

        # Previous / next month
        if month == 1:
            prev_month = {'year': year - 1, 'month': 12}
        else:
            prev_month = {'year': year, 'month': month - 1}

        if month == 12:
            next_month = {'year': year + 1, 'month': 1}
        else:
            next_month = {'year': year, 'month': month + 1}

        return Response({
            'year': year,
            'month': month,
            'startOfMonth': start_date,
            'racesGrouped': dict(grouped),
            'previousMonth': prev_month,
            'nextMonth': next_month,
            'sport': sport,
            'sports': SPORTS,
        })


class RaceSportsView(APIView):
    def get(self, request):
        return Response(SPORTS)


class RaceRegionsView(APIView):
    def get(self, request):
        return Response(REGIONS)


class ReviewCreateView(APIView):
    def post(self, request, slug):
        try:
            if slug.isdigit():
                race = Race.objects.get(id=int(slug))
            else:
                race = Race.objects.get(slug=slug)
        except Race.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        ip_hash = hash_ip(request)

        # Rate limit: 3/hour
        allowed, _ = check_rate_limit(ip_hash, 'review', 3, 3600)
        if not allowed:
            return Response(
                {'errors': {'review': ['리뷰 작성 제한에 도달했습니다. 잠시 후 다시 시도해주세요.']}},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Check duplicate
        if Review.objects.filter(race=race, ip_hash=ip_hash).exists():
            return Response(
                {'errors': {'review': ['이미 이 대회에 리뷰를 작성하셨습니다.']}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ReviewCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        data = serializer.validated_data
        review = Review.objects.create(
            race=race,
            nickname=data.get('nickname') or None,
            rating=data['rating'],
            comment=data['comment'],
            completion_time=data.get('completion_time') or None,
            course_difficulty=data.get('course_difficulty') or None,
            operation_satisfaction=data.get('operation_satisfaction'),
            recommendation_tags=data.get('recommendation_tags') or None,
            ip_hash=ip_hash,
        )

        return Response({
            'success': True,
            'message': '리뷰가 등록되었습니다.',
            'review': ReviewSerializer(review).data,
        }, status=status.HTTP_201_CREATED)


class SitemapView(APIView):
    def get(self, request):
        races = Race.objects.order_by('-updated_at').values('slug', 'updated_at')
        posts = Post.objects.order_by('-updated_at').values('id', 'updated_at')

        now = timezone.now()
        calendar_months = []
        for delta in range(-12, 13):
            month = now.month + delta
            year = now.year
            while month < 1:
                month += 12
                year -= 1
            while month > 12:
                month -= 12
                year += 1
            calendar_months.append({'year': year, 'month': month})

        return Response({
            'races': [
                {'slug': r['slug'], 'updatedAt': r['updated_at']}
                for r in races
            ],
            'posts': [
                {'id': p['id'], 'updatedAt': p['updated_at']}
                for p in posts
            ],
            'calendarMonths': calendar_months,
        })


class DeviceTokenCreateView(APIView):
    def post(self, request):
        serializer = DeviceTokenCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        data = serializer.validated_data
        device, created = DeviceToken.objects.update_or_create(
            token=data['token'],
            defaults={
                'platform': data['platform'],
                'subscribed_sports': data.get('subscribed_sports'),
                'subscribed_regions': data.get('subscribed_regions'),
            },
        )

        return Response({
            'message': '푸시 토큰이 등록되었습니다.',
            'device_token': DeviceTokenSerializer(device).data,
        }, status=status.HTTP_201_CREATED)


class DeviceTokenUpdateView(APIView):
    def put(self, request):
        serializer = DeviceTokenUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        data = serializer.validated_data
        try:
            device = DeviceToken.objects.get(token=data['token'])
        except DeviceToken.DoesNotExist:
            return Response(
                {'message': '등록된 토큰을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if 'subscribed_sports' in data:
            device.subscribed_sports = data['subscribed_sports']
        if 'subscribed_regions' in data:
            device.subscribed_regions = data['subscribed_regions']
        device.save()

        return Response({
            'message': '구독 설정이 업데이트되었습니다.',
            'device_token': DeviceTokenSerializer(device).data,
        })


class DeviceTokenDeleteView(APIView):
    def delete(self, request):
        token = request.data.get('token')
        if not token:
            return Response(
                {'message': '토큰이 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            device = DeviceToken.objects.get(token=token)
        except DeviceToken.DoesNotExist:
            return Response(
                {'message': '등록된 토큰을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        device.delete()
        return Response({'message': '푸시 토큰이 삭제되었습니다.'})


class RaceImageUploadView(APIView):
    def post(self, request, slug):
        # Bearer token auth
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return Response(
                {'message': 'Invalid API key.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        token = auth_header[7:]
        if token != settings.CRAWLER_API_KEY:
            return Response(
                {'message': 'Invalid API key.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            if slug.isdigit():
                race = Race.objects.get(id=int(slug))
            else:
                race = Race.objects.get(slug=slug)
        except Race.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        image_type = request.data.get('type')
        if image_type not in ('main', 'course', 'giveaway'):
            return Response(
                {'errors': {'type': ['type must be main, course, or giveaway']}},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        images = request.FILES.getlist('images')
        if not images or len(images) > 10:
            return Response(
                {'errors': {'images': ['1~10개의 이미지를 업로드해주세요.']}},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # Save images
        dir_map = {'main': 'races', 'course': 'races/courses', 'giveaway': 'races/giveaways'}
        save_dir = os.path.join(str(settings.MEDIA_ROOT), dir_map[image_type])
        os.makedirs(save_dir, exist_ok=True)

        stored_paths = []
        urls = []
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')

        for i, img in enumerate(images):
            ext = os.path.splitext(img.name)[1] or '.jpg'
            filename = f'{race.id}_{timestamp}_{i}{ext}'
            filepath = os.path.join(save_dir, filename)
            with open(filepath, 'wb') as f:
                for chunk in img.chunks():
                    f.write(chunk)

            rel_path = f'{dir_map[image_type]}/{filename}'
            stored_paths.append(rel_path)
            urls.append(f'{settings.STORAGE_URL}{rel_path}')

            # Convert to WebP + thumbnail
            from races.image_utils import process_image
            process_image(rel_path)

        # Create pending change for admin review
        import json
        if image_type == 'main' and stored_paths:
            RacePendingChange.objects.create(
                race=race,
                field_name='image_path',
                old_value=race.image_path,
                new_value=stored_paths[0],
                source='crawler',
                status='pending',
            )
        elif image_type == 'course':
            existing = race.course_image_uploads or []
            new_val = existing + stored_paths
            RacePendingChange.objects.create(
                race=race,
                field_name='course_image_uploads',
                old_value=json.dumps(existing),
                new_value=json.dumps(new_val),
                source='crawler',
                status='pending',
            )
        elif image_type == 'giveaway':
            existing = race.giveaway_image_uploads or []
            new_val = existing + stored_paths
            RacePendingChange.objects.create(
                race=race,
                field_name='giveaway_image_uploads',
                old_value=json.dumps(existing),
                new_value=json.dumps(new_val),
                source='crawler',
                status='pending',
            )

        return Response({
            'message': 'Images uploaded and pending review.',
            'race_id': race.id,
            'race_title': race.title,
            'type': image_type,
            'stored_paths': stored_paths,
            'urls': urls,
        }, status=status.HTTP_201_CREATED)
