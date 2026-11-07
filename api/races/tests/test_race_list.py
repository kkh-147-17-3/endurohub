from datetime import date, datetime, timedelta, timezone as datetime_timezone
from typing import Any
from unittest.mock import patch

from django.test import override_settings
from rest_framework.test import APITestCase

from races.models import Race


class RaceListTests(APITestCase):
    def setUp(self) -> None:
        self.today = date(2026, 11, 7)
        self.date_patch = patch('races.models.timezone.localdate', return_value=self.today)
        self.date_patch.start()
        self.addCleanup(self.date_patch.stop)
        track_patch = patch('races.views.track')
        track_patch.start()
        self.addCleanup(track_patch.stop)
        self.url = '/api/v1/races/'

    def race(self, slug: str, **overrides: Any) -> Race:
        values = {
            'title': f'가을 {slug}',
            'slug': slug,
            'sport': 'running',
            'race_date': self.today + timedelta(days=10),
            'location': '서울 테스트 장소',
            'region': '서울',
            'distances': [{'name': '10km'}],
            'registration_start': self.today - timedelta(days=10),
            'registration_end': self.today + timedelta(days=3),
        }
        values.update(overrides)
        return Race.objects.create(**values)

    def ids(self, response: Any) -> list[int]:
        self.assertEqual(response.status_code, 200)
        return [race['id'] for race in response.data['results']]

    def test_default_excludes_finished_races_but_includes_today_and_ongoing_races(self) -> None:
        self.race('past', race_date=self.today - timedelta(days=1))
        self.race('ended-multiday', race_date=date(2026, 10, 30), race_end_date=self.today - timedelta(days=1))
        ongoing = self.race('ongoing', race_date=date(2026, 10, 30), race_end_date=self.today)
        today = self.race('today', race_date=self.today)
        future = self.race('future')

        response = self.client.get(self.url)

        self.assertEqual(self.ids(response), [ongoing.id, today.id, future.id])
        self.assertEqual(response.data['count'], 3)
        self.assertIsNone(response.data['applied']['monthFrom'])

    def test_explicit_current_month_includes_earlier_finished_races(self) -> None:
        self.race('october', race_date=date(2026, 10, 31))
        earlier = self.race('earlier', race_date=date(2026, 11, 1))
        future = self.race('future')
        self.race('december', race_date=date(2026, 12, 1))

        response = self.client.get(self.url, {'month_from': '2026-11', 'month_to': '2026-11'})

        self.assertEqual(self.ids(response), [earlier.id, future.id])
        self.assertEqual(response.data['applied']['monthFrom'], '2026-11')

    def test_explicit_historical_year_or_end_month_remains_accessible(self) -> None:
        old = self.race('old', race_date=date(2025, 12, 31))
        january = self.race('january', race_date=date(2026, 1, 1))
        december = self.race('december', race_date=date(2026, 12, 31))
        self.race('next-year', race_date=date(2027, 1, 1))

        year = self.client.get(self.url, {'month_from': '2026-01', 'month_to': '2026-12'})
        end_only = self.client.get(self.url, {'month_to': '2026-01'})

        self.assertEqual(self.ids(year), [january.id, december.id])
        self.assertEqual(self.ids(end_only), [old.id, january.id])

    def test_explicit_finished_status_remains_a_history_request(self) -> None:
        past = self.race('past', race_date=date(2026, 1, 1))
        self.race('future')

        self.assertEqual(self.ids(self.client.get(self.url, {'status': 'finished'})), [past.id])
        self.assertEqual(self.ids(self.client.get(self.url, {'status': 'finished', 'upcoming': 'true'})), [])

    def test_upcoming_flag_composes_all_filters_and_stable_pagination(self) -> None:
        first = self.race('match-first')
        second = self.race('match-second')
        self.race('past-match', race_date=self.today - timedelta(days=1))
        self.race('match-other-sport', sport='swimming')
        self.race('match-other-region', region='부산')
        self.race('other-name', title='봄 대회')
        self.race('match-other-distance', distances=[{'name': '42.195km'}])
        self.race('match-closed', registration_end=self.today - timedelta(days=1))
        params: dict[str, Any] = {
            'upcoming': 'true', 'sport': 'running', 'region': '서울',
            'name': 'match', 'distance_category': 'short',
            'status': 'registration_open', 'per_page': 1,
        }

        page_one = self.client.get(self.url, params)
        page_two = self.client.get(self.url, {**params, 'page': 2})

        self.assertEqual(self.ids(page_one), [first.id])
        self.assertEqual(self.ids(page_two), [second.id])
        self.assertEqual(page_one.data['count'], 2)
        self.assertEqual(page_two.data['count'], 2)

    def test_closing_soon_flag_composes_filters_and_orders_by_deadline(self) -> None:
        later = self.race('match-later', registration_end=self.today + timedelta(days=2))
        today = self.race('match-today', registration_end=self.today)
        self.race('match-too-late', registration_end=self.today + timedelta(days=4))
        self.race('match-other-sport', sport='swimming')
        self.race('match-other-region', region='부산')
        self.race('other-name', title='봄 대회')
        self.race('match-other-distance', distances=[{'name': '42.195km'}])
        self.race('match-manually-closed', status='registration_closed')
        params: dict[str, Any] = {
            'closing_soon': 'true', 'days': 2, 'sport': 'running', 'region': '서울',
            'name': 'match', 'distance_category': 'short', 'status': 'registration_open',
        }

        response = self.client.get(self.url, params)

        self.assertEqual(self.ids(response), [today.id, later.id])
        self.assertEqual(response.data['count'], 2)

    def test_month_bounds_intersect_with_mobile_flags(self) -> None:
        self.race('past', race_date=date(2026, 11, 1))
        november = self.race('november')
        self.race('december', race_date=date(2026, 12, 1))
        for flag in ('upcoming', 'closing_soon'):
            with self.subTest(flag=flag):
                response = self.client.get(self.url, {
                    flag: 'true', 'month_from': '2026-11', 'month_to': '2026-11',
                })
                self.assertEqual(self.ids(response), [november.id])

    def test_mixed_closing_soon_status_is_an_or_within_other_filters(self) -> None:
        closing = self.race('closing')
        not_open = self.race('not-open', registration_start=self.today + timedelta(days=1))
        self.race('closed', registration_end=self.today - timedelta(days=1))
        self.race('other-region', region='부산')

        response = self.client.get(self.url, {
            'sport': 'running', 'region': '서울', 'status': ['closing_soon', 'upcoming'],
        })

        self.assertEqual(self.ids(response), [closing.id, not_open.id])

    @override_settings(TIME_ZONE='Asia/Seoul')
    def test_default_uses_korean_date_when_utc_is_still_previous_day(self) -> None:
        self.date_patch.stop()
        utc_now = datetime(2026, 11, 6, 15, 30, tzinfo=datetime_timezone.utc)
        yesterday = self.race('yesterday', race_date=date(2026, 11, 6))
        today = self.race('today', race_date=date(2026, 11, 7))

        with patch('django.utils.timezone.now', return_value=utc_now):
            response = self.client.get(self.url)

        self.assertEqual(self.ids(response), [today.id])
        self.assertNotIn(yesterday.id, self.ids(response))
