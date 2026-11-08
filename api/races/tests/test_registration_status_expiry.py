from datetime import date, timedelta
from typing import Any
from unittest.mock import patch

from django.test import TestCase

from races.models import Race


class RegistrationStatusExpiryTests(TestCase):
    def setUp(self) -> None:
        self.today = date(2026, 11, 15)
        date_patch = patch('races.models.timezone.localdate', return_value=self.today)
        date_patch.start()
        self.addCleanup(date_patch.stop)

    def race(self, slug: str, **overrides: Any) -> Race:
        values: dict[str, Any] = {
            'title': f'가을 {slug}',
            'slug': slug,
            'sport': 'running',
            'race_date': self.today + timedelta(days=7),
            'location': '서울 테스트 장소',
            'region': '서울',
            'status': 'registration_closed',
        }
        values.update(overrides)
        return Race.objects.create(**values)

    def assert_status(self, race: Race, expected: str) -> None:
        self.assertEqual(race.computed_status, expected)
        for status in ('upcoming', 'registration_open', 'registration_closed', 'finished', 'cancelled'):
            with self.subTest(slug=race.slug, queried_status=status):
                self.assertEqual(
                    Race.objects.by_status(status).filter(pk=race.pk).exists(),
                    status == expected,
                )

    def test_past_registration_overrides_expire_without_mutating_raw_status(self) -> None:
        for status in ('registration_closed', 'registration_open', 'upcoming'):
            with self.subTest(raw_status=status):
                race = self.race(status, status=status, race_date=self.today - timedelta(days=1))

                self.assert_status(race, 'finished')
                race.refresh_from_db()
                self.assertEqual(race.status, status)

    def test_past_multiday_registration_overrides_expire_after_final_day(self) -> None:
        for status in ('registration_closed', 'registration_open', 'upcoming'):
            with self.subTest(raw_status=status):
                race = self.race(
                    status, status=status,
                    race_date=self.today - timedelta(days=3),
                    race_end_date=self.today - timedelta(days=1),
                )

                self.assert_status(race, 'finished')

    def test_race_day_registration_overrides_are_still_current(self) -> None:
        for status in ('registration_closed', 'registration_open', 'upcoming'):
            with self.subTest(raw_status=status):
                race = self.race(status, status=status, race_date=self.today)

                self.assert_status(race, status)

    def test_future_registration_closure_is_preserved(self) -> None:
        race = self.race(
            'future-closed',
            registration_start=self.today - timedelta(days=10),
            registration_end=self.today + timedelta(days=3),
        )

        self.assert_status(race, 'registration_closed')

    def test_multiday_registration_closure_remains_through_final_day(self) -> None:
        race = self.race(
            'ongoing-closed',
            race_date=self.today - timedelta(days=1),
            race_end_date=self.today,
        )

        self.assert_status(race, 'registration_closed')

    def test_explicit_finished_status_is_respected_even_before_race_date(self) -> None:
        race = self.race('manually-finished', status='finished')

        self.assert_status(race, 'finished')

    def test_other_manual_status_is_not_expired(self) -> None:
        race = self.race('postponed', status='postponed', race_date=self.today - timedelta(days=1))

        self.assert_status(race, 'postponed')
        self.assertTrue(Race.objects.by_status('postponed').filter(pk=race.pk).exists())

    def test_empty_manual_status_still_uses_event_dates(self) -> None:
        for slug, status in (('null', None), ('empty', '')):
            with self.subTest(raw_status=status):
                race = self.race(slug, status=status, race_date=self.today - timedelta(days=1))

                self.assert_status(race, 'finished')

    def test_cancellation_takes_precedence_over_expired_registration_status(self) -> None:
        for suffix, overrides in (
            ('explicit', {'status': 'cancelled'}),
            ('title', {'title': '[취소] 가을 대회'}),
            ('notice', {'description': '대회를 취소합니다.'}),
        ):
            with self.subTest(cancellation=suffix):
                race = self.race(
                    suffix, race_date=self.today - timedelta(days=1), **overrides,
                )

                self.assert_status(race, 'cancelled')

    def test_combined_status_filter_includes_expired_and_current_without_duplicates(self) -> None:
        expired = self.race('expired', race_date=self.today - timedelta(days=1))
        current = self.race('current')
        self.race('cancelled', status='cancelled', race_date=self.today - timedelta(days=1))

        ids = list(Race.objects.by_status(['finished', 'registration_closed']).values_list('id', flat=True))

        self.assertCountEqual(ids, [expired.pk, current.pk])
