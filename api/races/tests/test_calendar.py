from datetime import date, timedelta

from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from races.models import Race


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'race-calendar-tests',
    },
})
class RaceCalendarTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse('race-calendar')

    def tearDown(self):
        cache.clear()

    def create_race(self, race_date, slug):
        return Race.objects.create(
            title=f'{race_date:%Y-%m} 테스트 대회',
            slug=slug,
            sport='running',
            race_date=race_date,
            location='서울',
            region='서울',
        )

    def test_rejects_noncanonical_or_invalid_year_and_month(self):
        invalid_queries = (
            {'year': '2026foo', 'month': '1'},
            {'year': '02026', 'month': '1'},
            {'year': '+2026', 'month': '1'},
            {'year': '2026', 'month': '09'},
            {'year': '2026', 'month': '0'},
            {'year': '2026', 'month': '13'},
            {'year': '2026', 'month': 'abc'},
        )

        for query in invalid_queries:
            with self.subTest(query=query):
                response = self.client.get(self.url, query)
                self.assertEqual(response.status_code, 404)

    def test_empty_database_only_serves_current_month_without_navigation(self):
        today = timezone.localdate()
        response = self.client.get(self.url, {
            'year': str(today.year),
            'month': str(today.month),
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['racesGrouped'], {})
        self.assertIsNone(response.data['previousMonth'])
        self.assertIsNone(response.data['nextMonth'])

        other_month = date(today.year, today.month, 1) - timedelta(days=1)
        response = self.client.get(self.url, {
            'year': str(other_month.year),
            'month': str(other_month.month),
        })
        self.assertEqual(response.status_code, 404)

    def test_bounds_limit_navigation_and_allow_empty_months_between_them(self):
        today = timezone.localdate()
        middle_month = date(today.year, today.month, 1)
        first_month = (middle_month - timedelta(days=1)).replace(day=1)
        last_month = (middle_month + timedelta(days=32)).replace(day=1)
        self.create_race(first_month.replace(day=10), 'first-bound-race')
        self.create_race(last_month.replace(day=10), 'last-bound-race')

        first = self.client.get(self.url, {
            'year': str(first_month.year), 'month': str(first_month.month),
        })
        middle = self.client.get(self.url, {
            'year': str(middle_month.year), 'month': str(middle_month.month),
        })
        last = self.client.get(self.url, {
            'year': str(last_month.year), 'month': str(last_month.month),
        })

        self.assertEqual(first.status_code, 200)
        self.assertIsNone(first.data['previousMonth'])
        self.assertEqual(first.data['nextMonth'], {
            'year': middle_month.year, 'month': middle_month.month,
        })

        self.assertEqual(middle.status_code, 200)
        self.assertEqual(middle.data['racesGrouped'], {})
        self.assertEqual(middle.data['previousMonth'], {
            'year': first_month.year, 'month': first_month.month,
        })
        self.assertEqual(middle.data['nextMonth'], {
            'year': last_month.year, 'month': last_month.month,
        })

        self.assertEqual(last.status_code, 200)
        self.assertEqual(last.data['previousMonth'], {
            'year': middle_month.year, 'month': middle_month.month,
        })
        self.assertIsNone(last.data['nextMonth'])

        before_month = (first_month - timedelta(days=1)).replace(day=1)
        after_month = (last_month + timedelta(days=32)).replace(day=1)
        before = self.client.get(self.url, {
            'year': str(before_month.year), 'month': str(before_month.month),
        })
        after = self.client.get(self.url, {
            'year': str(after_month.year), 'month': str(after_month.month),
        })
        self.assertEqual(before.status_code, 404)
        self.assertEqual(after.status_code, 404)

    def test_current_month_remains_available_when_all_races_are_in_the_past(self):
        today = timezone.localdate()
        current_month = date(today.year, today.month, 1)
        previous_month = current_month - timedelta(days=1)
        self.create_race(previous_month.replace(day=10), 'past-only-race')

        response = self.client.get(self.url, {
            'year': str(current_month.year),
            'month': str(current_month.month),
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['racesGrouped'], {})
        self.assertEqual(response.data['previousMonth'], {
            'year': previous_month.year,
            'month': previous_month.month,
        })
        self.assertIsNone(response.data['nextMonth'])

    def test_current_month_remains_available_when_all_races_are_in_the_future(self):
        today = timezone.localdate()
        current_month = date(today.year, today.month, 1)
        next_month = (current_month + timedelta(days=32)).replace(day=1)
        self.create_race(next_month.replace(day=10), 'future-only-race')

        response = self.client.get(self.url, {
            'year': str(current_month.year),
            'month': str(current_month.month),
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['racesGrouped'], {})
        self.assertIsNone(response.data['previousMonth'])
        self.assertEqual(response.data['nextMonth'], {
            'year': next_month.year,
            'month': next_month.month,
        })
