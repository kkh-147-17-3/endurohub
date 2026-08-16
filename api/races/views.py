import copy
import os
import random
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg, Count, F, Q
from core.utils import post_count_subqueries
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import JWTAuthentication
from core.analytics import track
from core.models import AnalyticsEvent
from core.pagination import LaravelStylePagination
from core.utils import check_rate_limit, hash_ip
from posts.models import Post
from posts.serializers import PostListSerializer
from rest_framework.permissions import IsAuthenticated

from .constants import DISTANCE_CATEGORIES, REGIONS, SPORTS
from .models import DeviceToken, Race, RaceFavorite, RacePendingChange, Review


def _favorite_race_ids(request, race_ids=None):
    """Return set of race IDs favorited by the authenticated user (empty if anonymous)."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return set()
    qs = RaceFavorite.objects.filter(user=user)
    if race_ids is not None:
        qs = qs.filter(race_id__in=race_ids)
    return set(qs.values_list('race_id', flat=True))


def _inject_is_favorited(request, race_dicts):
    """Overwrite isFavorited on a list of already-serialized race dicts for the current user.

    Used after cache retrieval since cached payloads are user-agnostic.
    """
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated or not race_dicts:
        return
    ids = [r['id'] for r in race_dicts if isinstance(r, dict) and 'id' in r]
    if not ids:
        return
    fav = set(RaceFavorite.objects.filter(
        user=user, race_id__in=ids,
    ).values_list('race_id', flat=True))
    for r in race_dicts:
        if isinstance(r, dict) and 'id' in r:
            r['isFavorited'] = r['id'] in fav
from .serializers import (
    DeviceTokenCreateSerializer,
    DeviceTokenSerializer,
    DeviceTokenUpdateSerializer,
    RaceListSerializer,
    RaceSerializer,
    ReviewCreateSerializer,
    ReviewSerializer,
    UpcomingRaceSerializer,
)


class HomeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]
    CACHE_KEY = 'home_page_data'
    CACHE_TTL = 300  # 5 minutes

    def get(self, request):
        cached = cache.get(self.CACHE_KEY)
        if cached:
            import copy
            data = copy.deepcopy(cached)
            for key in ('closingSoon', 'upcomingRaces', 'recentlyAdded'):
                _inject_is_favorited(request, data.get(key) or [])
            return Response(data)

        today = timezone.localdate()

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

        import copy
        response_data = copy.deepcopy(data)
        for key in ('closingSoon', 'upcomingRaces', 'recentlyAdded'):
            _inject_is_favorited(request, response_data.get(key) or [])
        return Response(response_data)


class RecommendationsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]
    CACHE_TTL = 300  # 5 minutes
    EVENT_WEIGHTS = {
        'review_submit': 3,
        'race_view': 2,
        'race_search': 1,
    }
    MIN_EVENTS = 5
    MIN_UNIQUE_RACES = 3
    LOOKBACK_DAYS = 30
    TOP_COUNT = 4
    RANDOM_COUNT = 2

    def get(self, request):
        user = request.user if request.user and request.user.is_authenticated else None
        session_id = request.META.get('HTTP_X_SESSION_ID', '') or request.COOKIES.get('ehub_sid', '')

        # Cache key: per-user or per-session
        if user:
            cache_key = f'recommendations_user_{user.pk}'
        elif session_id:
            cache_key = f'recommendations_session_{session_id}'
        else:
            cache_key = 'recommendations_anonymous'

        cached = cache.get(cache_key)
        if cached:
            import copy
            data = copy.deepcopy(cached)
            _inject_is_favorited(request, data.get('races') or [])
            return Response(data)

        cutoff = timezone.now() - timedelta(days=self.LOOKBACK_DAYS)

        # Build event filter
        event_filter = Q(
            event_type__in=['race_view', 'race_search', 'review_submit'],
            created_at__gte=cutoff,
        )
        if user:
            event_filter &= Q(user=user)
        elif session_id:
            event_filter &= Q(session_id=session_id)
        else:
            data = self._popular_fallback()
            cache.set(cache_key, data, self.CACHE_TTL)
            import copy
            response_data = copy.deepcopy(data)
            _inject_is_favorited(request, response_data.get('races') or [])
            return Response(response_data)

        events = AnalyticsEvent.objects.filter(event_filter)

        # Check data sufficiency
        stats = events.filter(event_type='race_view').aggregate(
            total=Count('id'),
            unique_races=Count('item_id', distinct=True),
        )

        if stats['total'] >= self.MIN_EVENTS and stats['unique_races'] >= self.MIN_UNIQUE_RACES:
            data = self._personalized(events)
        else:
            data = self._popular_fallback()

        cache.set(cache_key, data, self.CACHE_TTL)

        import copy
        response_data = copy.deepcopy(data)
        _inject_is_favorited(request, response_data.get('races') or [])
        return Response(response_data)

    def _personalized(self, events):
        """Generate personalized recommendations based on user event history."""
        sport_scores = defaultdict(float)
        region_scores = defaultdict(float)
        viewed_race_ids = set()

        for event in events.filter(
            event_type__in=['race_view', 'review_submit'],
            item_type='race',
        ).values('event_type', 'item_id', 'properties'):
            weight = self.EVENT_WEIGHTS.get(event['event_type'], 1)
            props = event['properties'] or {}
            if props.get('sport'):
                sport_scores[props['sport']] += weight
            if props.get('region'):
                region_scores[props['region']] += weight
            if event['item_id']:
                viewed_race_ids.add(event['item_id'])

        # Also aggregate race_search events
        for event in events.filter(event_type='race_search').values('properties'):
            props = event['properties'] or {}
            for sport in (props.get('sport') or []):
                sport_scores[sport] += self.EVENT_WEIGHTS['race_search']
            for region in (props.get('region') or []):
                region_scores[region] += self.EVENT_WEIGHTS['race_search']

        # Sort by score descending
        top_sports = [s for s, _ in sorted(sport_scores.items(), key=lambda x: -x[1])][:3]
        top_regions = [r for r, _ in sorted(region_scores.items(), key=lambda x: -x[1])][:3]

        # Build query: upcoming races matching preferred sports/regions, exclude already viewed
        qs = Race.objects.upcoming().exclude(
            title__contains='(취소)'
        )

        # Exclude viewed race IDs (item_id is stored as string of race.id)
        viewed_int_ids = set()
        for rid in viewed_race_ids:
            try:
                viewed_int_ids.add(int(rid))
            except (ValueError, TypeError):
                pass
        if viewed_int_ids:
            qs = qs.exclude(id__in=viewed_int_ids)

        # Filter by preferred sports or regions
        sport_region_q = Q()
        if top_sports:
            sport_region_q |= Q(sport__in=top_sports)
        if top_regions:
            sport_region_q |= Q(region__in=top_regions)

        if sport_region_q:
            matched_qs = qs.filter(sport_region_q)
        else:
            matched_qs = qs

        # Top 4 by view_count
        top_races = list(matched_qs.order_by('-view_count')[:self.TOP_COUNT])
        top_ids = {r.id for r in top_races}

        # Random 2 from remaining matched races
        remaining = list(
            matched_qs.exclude(id__in=top_ids).order_by('?')[:self.RANDOM_COUNT]
        )

        # If not enough, fill from general upcoming
        total = top_races + remaining
        if len(total) < self.TOP_COUNT + self.RANDOM_COUNT:
            fill_count = (self.TOP_COUNT + self.RANDOM_COUNT) - len(total)
            fill_ids = {r.id for r in total}
            fill = list(
                qs.exclude(id__in=fill_ids).order_by('-view_count')[:fill_count]
            )
            total += fill

        return {
            'type': 'personalized',
            'races': RaceSerializer(total, many=True).data,
            'reason': {
                'topSports': top_sports,
                'topRegions': top_regions,
            },
        }

    def _popular_fallback(self):
        """Return popular races based on view_count."""
        qs = Race.objects.upcoming().exclude(title__contains='(취소)')

        top_races = list(qs.order_by('-view_count')[:self.TOP_COUNT])
        top_ids = {r.id for r in top_races}

        remaining = list(
            qs.exclude(id__in=top_ids).order_by('?')[:self.RANDOM_COUNT]
        )

        return {
            'type': 'popular',
            'races': RaceSerializer(top_races + remaining, many=True).data,
            'reason': None,
        }


class RaceListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

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
                closing_ids = Race.objects.closing_soon(7).values_list('pk', flat=True)
                status_ids = Race.objects.by_status(regular_statuses).values_list('pk', flat=True)
                qs = Race.objects.filter(pk__in=set(closing_ids) | set(status_ids))
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
        page_ids = [r.id for r in page]
        favorite_ids = _favorite_race_ids(request, page_ids)
        serializer = RaceSerializer(page, many=True, context={'favorite_race_ids': favorite_ids})

        response_data = paginator.get_paginated_response(serializer.data).data
        response_data['filters'] = {
            'regions': REGIONS,
            'sports': SPORTS,
            'distanceCategories': DISTANCE_CATEGORIES,
        }
        applied = {
            'sport': sport,
            'region': region,
            'status': status_filter,
            'name': name,
            'distanceCategory': distance_category,
            'monthFrom': month_from,
            'monthTo': month_to,
        }
        response_data['applied'] = applied

        if sport or region or name or distance_category or status_filter:
            track('race_search', request, {
                k: v for k, v in applied.items() if v
            })

        return Response(response_data)


class RaceNlSearchView(APIView):
    """자연어 대회 검색. q(자연어)를 LLM으로 구조화 필터로 파싱 후 목록 반환.

    LLM 미설정/실패 시 q를 제목 키워드로 쓰는 폴백으로 동작한다.
    응답은 RaceListView 와 동일한 data/meta/links 형태에 interpretation(요약·칩)을 더한다.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        from .nl_search import VALID_DISTANCE_CATEGORIES, interpret_query

        raw_query = (request.query_params.get('q') or '').strip()

        today = timezone.localdate()
        parsed = interpret_query(raw_query, today) if raw_query else None

        if parsed is None:
            # 폴백: 키워드(제목) 검색만
            parsed = {
                'sports': [], 'regions': [], 'statuses': [],
                'distance_categories': [], 'month_from': '', 'month_to': '',
                'fee_max': None, 'q': raw_query, 'summary': '', 'chips': [],
            }

        sports = parsed['sports']
        regions = parsed['regions']
        statuses = parsed['statuses']
        distance_categories = parsed['distance_categories']
        fee_max = parsed['fee_max']
        keyword = parsed['q']

        # 월 범위: LLM 미지정 시 현재 월부터 (RaceListView 기본 동작과 동일)
        month_from = parsed['month_from'] or today.strftime('%Y-%m')
        month_to = parsed['month_to'] or None

        qs = Race.objects.all()
        if statuses:
            qs = qs.by_status(statuses)
        if sports:
            qs = qs.by_sport(sports)
        if regions:
            qs = qs.by_region(regions)
        # 거리 카테고리는 단일 종목일 때만 적용 (DISTANCE_CATEGORIES 가 종목별 키)
        applied_distance = []
        if distance_categories and len(sports) == 1:
            valid = VALID_DISTANCE_CATEGORIES.get(sports[0], set())
            applied_distance = [c for c in distance_categories if c in valid]
            if applied_distance:
                qs = qs.by_distance_category(sports[0], applied_distance)
        if fee_max:
            qs = qs.by_fee_max(fee_max)
        qs = qs.by_month_range(month_from, month_to)
        if keyword:
            qs = qs.by_name(keyword)

        paginator = LaravelStylePagination()
        per_page = request.query_params.get('per_page')
        if per_page:
            paginator.page_size = min(int(per_page), 100)

        page = paginator.paginate_queryset(qs, request)
        page_ids = [r.id for r in page]
        favorite_ids = _favorite_race_ids(request, page_ids)
        serializer = RaceSerializer(page, many=True, context={'favorite_race_ids': favorite_ids})

        response_data = paginator.get_paginated_response(serializer.data).data
        response_data['interpretation'] = {
            'summary': parsed['summary'],
            'chips': parsed['chips'],
        }
        applied = {
            'query': raw_query,
            'sport': sports,
            'region': regions,
            'status': statuses,
            'distanceCategory': applied_distance,
            'feeMax': fee_max,
            'monthFrom': month_from,
            'monthTo': month_to,
            'name': keyword,
        }
        response_data['applied'] = applied

        if raw_query:
            track('race_search_nl', request, {
                k: v for k, v in applied.items() if v
            })

        return Response(response_data)


class RaceDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            if slug.isdigit():
                race = Race.objects.get(id=int(slug))
            else:
                race = Race.objects.get(slug=slug)
        except Race.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        Race.objects.filter(pk=race.pk).update(view_count=F('view_count') + 1)

        track('race_view', request, {
            'slug': race.slug,
            'sport': race.sport,
            'region': race.region,
        }, item_id=race.id, item_type='race')

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

        # Season records (공개 완주 기록 + 내 기록)
        season_records = self._season_records(race, request)

        related_race_ids = [race.id]
        for slot in related_race_slots:
            related_race_ids.extend(r.id for r in slot['races'])
        favorite_ids = _favorite_race_ids(request, related_race_ids)
        ctx = {'favorite_race_ids': favorite_ids}

        return Response({
            'race': RaceSerializer(race, context=ctx).data,
            'relatedRaces': [
                {
                    'label': slot['label'],
                    'races': RaceSerializer(slot['races'], many=True, context=ctx).data,
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
            'seasonRecords': season_records,
        })

    def _season_records(self, race, request):
        """이 대회의 공개 완주 기록 목록. 로그인 사용자의 기록은 비공개여도 me로 포함."""
        from accounts.models import RaceRecord

        user = request.user if request.user.is_authenticated else None
        records = RaceRecord.objects.filter(race=race).select_related('user__profile')
        out = []
        for rec in records:
            is_me = user is not None and rec.user_id == user.id
            if not rec.is_public and not is_me:
                continue
            total = rec.duration_seconds or 0
            hours, rem = divmod(total, 3600)
            minutes, seconds = divmod(rem, 60)
            time = f'{hours}:{minutes:02d}:{seconds:02d}' if hours else f'{minutes}:{seconds:02d}'
            pace = ''
            km = self._course_km(race, rec.course_code)
            if km and total:
                per_km = int(round(total / km))
                pm, ps = divmod(per_km, 60)
                pace = f'{pm}\'{ps:02d}"'
            try:
                nickname = rec.user.profile.nickname or ''
            except ObjectDoesNotExist:
                nickname = ''
            out.append({
                'nickname': nickname or '러너',
                'courseCode': rec.course_code,
                'courseLabel': rec.distance,
                'time': time,
                'pace': pace,
                'date': rec.record_date or None,
                'durationSeconds': total,
                'me': is_me,
            })
        out.sort(key=lambda r: r['durationSeconds'])
        return out

    def _course_km(self, race, code):
        from accounts.serializers import course_code_for
        if not code:
            return None
        for d in race.distances or []:
            if isinstance(d, dict) and course_code_for(d) == code:
                meters = d.get('distance_meter')
                if meters and meters > 0:
                    return meters / 1000
        return None

    def _get_related_races(self, race, request=None):
        from datetime import timedelta

        slots = []
        exclude_ids = {race.id}
        now = timezone.localdate()

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
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]
    CACHE_TTL = 300  # 5 minutes

    @staticmethod
    def _cache_key(year):
        return f'races_yearly_{year}'

    def get(self, request, year):
        year = int(year)
        cache_key = self._cache_key(year)

        cached = cache.get(cache_key)
        if cached:
            data = copy.deepcopy(cached)
            for races_in_month in (data.get('races') or {}).values():
                _inject_is_favorited(request, races_in_month)
            return Response(data)

        races = list(Race.objects.filter(
            race_date__gte=date(year, 1, 1),
            race_date__lte=date(year, 12, 31),
        ).order_by('race_date'))

        serialized = RaceListSerializer(races, many=True).data

        grouped = defaultdict(list)
        for race, race_data in zip(races, serialized):
            month = str(race.race_date.month)
            grouped[month].append(race_data)

        data = {
            'races': dict(grouped),
            'year': year,
            'totalCount': len(races),
        }
        cache.set(cache_key, data, self.CACHE_TTL)

        response_data = copy.deepcopy(data)
        for races_in_month in response_data['races'].values():
            _inject_is_favorited(request, races_in_month)
        return Response(response_data)


class RaceCalendarView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]
    CACHE_TTL = 300  # 5 minutes
    REGIONS_CACHE_KEY = 'races_calendar_regions'
    REGIONS_CACHE_TTL = 3600  # 지역 목록은 거의 안 바뀐다 — 달력 캐시보다 길게 잡는다

    @staticmethod
    def _cache_key(year, month, sport, region):
        # 필터 조합마다 별도 키. 쿼리 파라미터 순서가 달라도 같은 키가 되도록 정렬.
        return 'races_calendar_{}_{}_{}_{}'.format(
            year, month, ','.join(sorted(sport)), ','.join(sorted(region)),
        )

    @classmethod
    def _regions(cls):
        """전체 지역 목록 — 매 요청 DISTINCT 전체 스캔하던 것을 캐시한다."""
        regions = cache.get(cls.REGIONS_CACHE_KEY)
        if regions is None:
            regions = list(
                Race.objects.exclude(region__isnull=True)
                .exclude(region__exact='')
                .values_list('region', flat=True)
                .distinct()
                .order_by('region')
            )
            cache.set(cls.REGIONS_CACHE_KEY, regions, cls.REGIONS_CACHE_TTL)
        return regions

    def get(self, request):
        now = timezone.now()
        year = int(request.query_params.get('year', now.year))
        month = int(request.query_params.get('month', now.month))
        sport = request.query_params.getlist('sport')
        region = request.query_params.getlist('region')

        # 캐시 페이로드는 사용자 무관하게 만들고 즐겨찾기만 요청마다 덮어쓴다
        # (RaceYearlyView 와 같은 방식).
        cache_key = self._cache_key(year, month, sport, region)
        cached = cache.get(cache_key)
        if cached:
            data = copy.deepcopy(cached)
            for races_on_day in (data.get('racesGrouped') or {}).values():
                _inject_is_favorited(request, races_on_day)
            return Response(data)

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
        if region:
            qs = qs.by_region(region)

        races = list(qs)
        # 대회마다 시리얼라이저를 새로 만들지 않고 한 번에 직렬화한다 (즐겨찾기는
        # 캐시 이후 _inject_is_favorited 가 채우므로 context 를 넘기지 않는다).
        serialized = RaceSerializer(races, many=True).data

        grouped = defaultdict(list)
        for race, race_data in zip(races, serialized):
            date_key = race.race_date.strftime('%Y-%m-%d')
            grouped[date_key].append(race_data)

        regions = self._regions()

        # Previous / next month
        if month == 1:
            prev_month = {'year': year - 1, 'month': 12}
        else:
            prev_month = {'year': year, 'month': month - 1}

        if month == 12:
            next_month = {'year': year + 1, 'month': 1}
        else:
            next_month = {'year': year, 'month': month + 1}

        data = {
            'year': year,
            'month': month,
            'startOfMonth': start_date,
            'racesGrouped': dict(grouped),
            'previousMonth': prev_month,
            'nextMonth': next_month,
            'sport': sport,
            'region': region,
            'sports': SPORTS,
            'regions': regions,
        }
        cache.set(cache_key, data, self.CACHE_TTL)

        response_data = copy.deepcopy(data)
        for races_on_day in response_data['racesGrouped'].values():
            _inject_is_favorited(request, races_on_day)
        return Response(response_data)


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

        track('review_submit', request, {
            'sport': race.sport,
            'rating': review.rating,
        }, item_id=race.id, item_type='race')

        return Response({
            'success': True,
            'message': '리뷰가 등록되었습니다.',
            'review': ReviewSerializer(review).data,
        }, status=status.HTTP_201_CREATED)


class RaceFavoriteToggleView(APIView):
    """POST /api/v1/races/<slug>/favorite/ — toggle favorite for authenticated user."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        try:
            if slug.isdigit():
                race = Race.objects.get(id=int(slug))
            else:
                race = Race.objects.get(slug=slug)
        except Race.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        existing = RaceFavorite.objects.filter(user=request.user, race=race).first()
        if existing:
            existing.delete()
            return Response({'success': True, 'favorited': False})

        RaceFavorite.objects.create(user=request.user, race=race)
        return Response({'success': True, 'favorited': True})


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
