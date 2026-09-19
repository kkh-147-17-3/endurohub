"""추천 로직.

request 객체를 받지 않는다 — queryset이나 평범한 값만 받아서 결과를 반환한다.
직렬화·캐싱·즐겨찾기 주입은 view 계층의 책임.
"""
from collections import defaultdict
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db.models import Count, Q, QuerySet
from django.utils import timezone

from core.models import AnalyticsEvent
from ..models import Race

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

_RECOMMENDATION_EVENT_TYPES = ['race_view', 'race_search', 'review_submit']


def build_event_filter(user: User | None = None, session_id: str = '', since: datetime | None = None) -> Q:
    """개인화에 쓸 AnalyticsEvent 필터. user가 있으면 user 기준, 없으면 session 기준."""
    if since is None:
        since = timezone.now() - timedelta(days=LOOKBACK_DAYS)
    event_filter = Q(
        event_type__in=_RECOMMENDATION_EVENT_TYPES,
        created_at__gte=since,
    )
    if user:
        event_filter &= Q(user=user)
    elif session_id:
        event_filter &= Q(session_id=session_id)
    return event_filter


def has_sufficient_events(events: QuerySet[AnalyticsEvent]) -> bool:
    """개인화할 만큼 이벤트가 쌓였는지 (조회 수 + 고유 대회 수 기준)."""
    stats = events.filter(event_type='race_view').aggregate(
        total=Count('id'),
        unique_races=Count('item_id', distinct=True),
    )
    return bool(stats['total'] >= MIN_EVENTS and stats['unique_races'] >= MIN_UNIQUE_RACES)


def build_recommendations(events: QuerySet[AnalyticsEvent]) -> dict:
    """이벤트 이력이 충분하면 개인화 추천, 아니면 인기 대체 추천.

    Returns {'type', 'races' (Race 인스턴스 목록), 'reason'}.
    """
    if has_sufficient_events(events):
        return _personalized(events)
    return popular_recommendations()


def popular_recommendations() -> dict:
    """조회수 상위 + 랜덤 보충. 이벤트가 없는 사용자의 대체 추천."""
    qs = Race.objects.upcoming().exclude(title__contains='(취소)')

    top_races = list(qs.order_by('-view_count')[:TOP_COUNT])
    top_ids = {r.id for r in top_races}

    remaining = list(
        qs.exclude(id__in=top_ids).order_by('?')[:RANDOM_COUNT]
    )

    return {
        'type': 'popular',
        'races': top_races + remaining,
        'reason': None,
    }


def _personalized(events: QuerySet[AnalyticsEvent]) -> dict:
    """이벤트 이력에서 선호 종목·지역을 추출해 맞는 예정 대회를 고른다."""
    sport_scores: defaultdict[str, float] = defaultdict(float)
    region_scores: defaultdict[str, float] = defaultdict(float)
    viewed_race_ids = set()

    for event in events.filter(
        event_type__in=['race_view', 'review_submit'],
        item_type='race',
    ).values('event_type', 'item_id', 'properties'):
        weight = EVENT_WEIGHTS.get(event['event_type'], 1)
        props = event['properties'] or {}
        if props.get('sport'):
            sport_scores[props['sport']] += weight
        if props.get('region'):
            region_scores[props['region']] += weight
        if event['item_id']:
            viewed_race_ids.add(event['item_id'])

    # 검색 이벤트도 점수에 반영
    for search_event in events.filter(event_type='race_search').values('properties'):
        props = search_event['properties'] or {}
        for sport in (props.get('sport') or []):
            sport_scores[sport] += EVENT_WEIGHTS['race_search']
        for region in (props.get('region') or []):
            region_scores[region] += EVENT_WEIGHTS['race_search']

    top_sports = [s for s, _ in sorted(sport_scores.items(), key=lambda x: -x[1])][:3]
    top_regions = [r for r, _ in sorted(region_scores.items(), key=lambda x: -x[1])][:3]

    qs = Race.objects.upcoming().exclude(title__contains='(취소)')

    # 이미 본 대회는 제외 (item_id는 race.id의 문자열)
    viewed_int_ids = set()
    for rid in viewed_race_ids:
        try:
            viewed_int_ids.add(int(rid))
        except (ValueError, TypeError):
            pass
    if viewed_int_ids:
        qs = qs.exclude(id__in=viewed_int_ids)

    # 선호 종목 또는 지역에 해당하는 대회만
    sport_region_q = Q()
    if top_sports:
        sport_region_q |= Q(sport__in=top_sports)
    if top_regions:
        sport_region_q |= Q(region__in=top_regions)

    if sport_region_q:
        matched_qs = qs.filter(sport_region_q)
    else:
        matched_qs = qs

    # 조회수 상위
    top_races = list(matched_qs.order_by('-view_count')[:TOP_COUNT])
    top_ids = {r.id for r in top_races}

    # 나머지 중 랜덤
    remaining = list(
        matched_qs.exclude(id__in=top_ids).order_by('?')[:RANDOM_COUNT]
    )

    # 부족하면 일반 예정 대회로 채움
    total = top_races + remaining
    if len(total) < TOP_COUNT + RANDOM_COUNT:
        fill_count = (TOP_COUNT + RANDOM_COUNT) - len(total)
        fill_ids = {r.id for r in total}
        fill = list(
            qs.exclude(id__in=fill_ids).order_by('-view_count')[:fill_count]
        )
        total += fill

    return {
        'type': 'personalized',
        'races': total,
        'reason': {
            'topSports': top_sports,
            'topRegions': top_regions,
        },
    }
