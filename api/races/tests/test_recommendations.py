"""추천 로직 단위 테스트 — races.services.

view/캐시/직렬화 없이 DB fixture만으로 서비스 함수를 검증한다.
"""
from datetime import timedelta
from typing import Any

import pytest
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.utils import timezone

from core.models import AnalyticsEvent
from races.models import Race
from races.services.recommendations import (
    LOOKBACK_DAYS,
    MIN_EVENTS,
    build_event_filter,
    build_recommendations,
    has_sufficient_events,
    popular_recommendations,
)


def make_race(title: str, sport: str = 'running', region: str = '서울', view_count: int = 0, days_until: int = 30) -> Race:
    return Race.objects.create(
        title=title,
        slug=Race.generate_unique_slug(title),
        sport=sport,
        race_date=timezone.now().date() + timedelta(days=days_until),
        location='테스트 장소',
        region=region,
        view_count=view_count,
    )


def make_view_event(race: Race, session_id: str = '', user: User | None = None, **props: Any) -> AnalyticsEvent:
    properties = {'sport': race.sport, 'region': race.region}
    properties.update(props)
    return AnalyticsEvent.objects.create(
        event_type='race_view',
        item_type='race',
        item_id=str(race.id),
        properties=properties,
        session_id=session_id,
        user=user,
    )


def make_sufficient_views(races: list[Race], session_id: str = 'sess') -> None:
    """MIN_EVENTS 건을 첫 3개 대회에 분산 (충분성 통과 + 첫 3개는 '본 대회')."""
    for i in range(MIN_EVENTS):
        make_view_event(races[i % 3], session_id=session_id)


def events_for(**filter_kwargs: Any) -> QuerySet[AnalyticsEvent]:
    return AnalyticsEvent.objects.filter(build_event_filter(**filter_kwargs))


# ── 인기 대체 추천 ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_popular_조회수_상위_4개를_먼저_선정() -> None:
    races = [make_race(f'대회{i}', view_count=i * 10) for i in range(6)]

    result = popular_recommendations()

    assert result['type'] == 'popular'
    assert result['reason'] is None
    assert [r.id for r in result['races'][:4]] == [races[i].id for i in (5, 4, 3, 2)]
    # 나머지 2개는 하위 2개 중 랜덤
    assert {r.id for r in result['races'][4:]} == {races[0].id, races[1].id}


@pytest.mark.django_db
def test_popular_취소된_대회는_제외() -> None:
    cancelled = make_race('취소된 대회 (취소)', view_count=999)
    others = [make_race(f'대회{i}', view_count=i) for i in range(3)]

    result = popular_recommendations()

    assert cancelled.id not in {r.id for r in result['races']}
    assert {r.id for r in result['races']} == {r.id for r in others}


@pytest.mark.django_db
def test_popular_지난_대회는_제외() -> None:
    make_race('지난 대회', view_count=999, days_until=-10)
    races = [make_race(f'대회{i}', view_count=i) for i in range(2)]

    result = popular_recommendations()

    assert {r.id for r in result['races']} == {r.id for r in races}


# ── 개인화 ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_personalized_본_대회는_제외() -> None:
    viewed = [make_race(f'본대회{i}', sport='trail_running', view_count=100 + i) for i in range(3)]
    candidates = [make_race(f'후보{i}', sport='trail_running', view_count=i) for i in range(6)]
    make_sufficient_views(viewed)

    result = build_recommendations(events_for(session_id='sess'))

    assert result['type'] == 'personalized'
    ids = {r.id for r in result['races']}
    assert all(r.id not in ids for r in viewed)


@pytest.mark.django_db
def test_personalized_선호_종목의_대회만_선정() -> None:
    seed = [make_race(f'시드{i}', sport='trail_running', region='강원') for i in range(3)]
    preferred = [make_race(f'트레일{i}', sport='trail_running', view_count=10 * i) for i in range(6)]
    other_sport = [make_race(f'마라톤{i}', view_count=999, region='부산') for i in range(4)]
    make_sufficient_views(seed)

    result = build_recommendations(events_for(session_id='sess'))

    assert [r.id for r in result['races'][:4]] == [preferred[i].id for i in (5, 4, 3, 2)]
    assert {r.id for r in result['races']} == {r.id for r in preferred}
    assert all(r.id not in {x.id for x in seed} for r in result['races'])


@pytest.mark.django_db
def test_personalized_검색_이벤트도_선호에_반영() -> None:
    seed = [make_race(f'시드{i}', sport='running', region='서울') for i in range(3)]
    races = [make_race(f'대회{i}', sport='trail_running', view_count=10 * i) for i in range(8)]
    # 조회 이벤트로 충분성만 채우고, 종목 선호는 검색 이벤트로 유도
    for i in range(MIN_EVENTS):
        make_view_event(seed[i % 3], session_id='sess', sport=None)
    AnalyticsEvent.objects.create(
        event_type='race_search',
        properties={'sport': ['trail_running'], 'region': []},
        session_id='sess',
    )

    result = build_recommendations(events_for(session_id='sess'))

    assert result['reason']['topSports'] == ['trail_running']
    assert [r.id for r in result['races'][:4]] == [races[i].id for i in (7, 6, 5, 4)]
    assert len(result['races']) == 6
    assert all(r.sport == 'trail_running' for r in result['races'])


@pytest.mark.django_db
def test_personalized_매칭_부족시_일반_예정_대회로_채움() -> None:
    seed = [make_race(f'시드{i}', sport='trail_running', region='강원') for i in range(3)]
    preferred = [make_race(f'트레일{i}', sport='trail_running', view_count=10 * i) for i in range(2)]
    others = [make_race(f'러닝{i}', sport='running', region='부산', view_count=100 * i) for i in range(4)]
    make_sufficient_views(seed)

    result = build_recommendations(events_for(session_id='sess'))

    ids = {r.id for r in result['races']}
    assert len(result['races']) == 6
    assert {r.id for r in preferred} <= ids  # 매칭된 것은 전부 포함
    assert {r.id for r in others} <= ids  # 부족분은 일반 대회로 채움
    assert all(r.id not in ids for r in seed)


# ── 충분성 판정 ────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_충분성_만족() -> None:
    races = [make_race(f'대회{i}') for i in range(3)]
    for i in range(MIN_EVENTS):
        make_view_event(races[i % 3], session_id='sess')

    assert has_sufficient_events(events_for(session_id='sess'))


@pytest.mark.django_db
def test_충분성_고유_대회_부족하면_불만족() -> None:
    race = make_race('대회')
    for _ in range(MIN_EVENTS):
        make_view_event(race, session_id='sess')

    assert not has_sufficient_events(events_for(session_id='sess'))


@pytest.mark.django_db
def test_이벤트_부족하면_인기_대체_추천으로_폴리백() -> None:
    races = [make_race(f'대회{i}', view_count=10 * i) for i in range(6)]
    make_view_event(races[0], session_id='sess')
    make_view_event(races[0], session_id='sess')

    result = build_recommendations(events_for(session_id='sess'))

    assert result['type'] == 'popular'
    assert [r.id for r in result['races'][:4]] == [races[i].id for i in (5, 4, 3, 2)]


# ── 이벤트 필터 ────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_필터는_세션_이벤트만_포함() -> None:
    race = make_race('대회')
    make_view_event(race, session_id='sess-a')
    make_view_event(race, session_id='sess-b')

    events = events_for(session_id='sess-a')

    assert events.count() == 1
    assert events[0].session_id == 'sess-a'


@pytest.mark.django_db
def test_필터는_사용자_이벤트만_포함() -> None:
    u1 = User.objects.create_user(username='u1')
    u2 = User.objects.create_user(username='u2')
    race = make_race('대회')
    make_view_event(race, user=u1)
    make_view_event(race, user=u2)

    events = AnalyticsEvent.objects.filter(build_event_filter(user=u1))

    assert events.count() == 1
    assert events[0].user_id == u1.id


@pytest.mark.django_db
def test_필터는_룩백_기간_이전_이벤트는_제외() -> None:
    race = make_race('대회')
    old = AnalyticsEvent.objects.create(
        event_type='race_view', item_type='race', item_id=str(race.id), session_id='sess',
    )
    AnalyticsEvent.objects.filter(pk=old.pk).update(
        created_at=timezone.now() - timedelta(days=LOOKBACK_DAYS + 10),
    )
    make_view_event(race, session_id='sess')

    events = events_for(session_id='sess')

    assert events.count() == 1
    assert events[0].pk != old.pk


@pytest.mark.django_db
def test_필터는_추천_대상_이벤트_타입만_포함() -> None:
    race = make_race('대회')
    make_view_event(race, session_id='sess')
    AnalyticsEvent.objects.create(event_type='page_view', session_id='sess')
    AnalyticsEvent.objects.create(event_type='tool_use', session_id='sess')

    assert events_for(session_id='sess').count() == 1
