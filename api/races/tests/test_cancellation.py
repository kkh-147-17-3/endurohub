from datetime import date, timedelta
from typing import Any
from unittest.mock import patch

from django.core.cache import cache
from rest_framework.test import APITestCase

from races.models import Race
from races.services.recommendations import popular_recommendations


class RaceCancellationTests(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.addCleanup(cache.clear)
        self.today = date(2026, 11, 7)
        today_patch = patch('races.models.timezone.localdate', return_value=self.today)
        today_patch.start()
        self.addCleanup(today_patch.stop)
        track_patch = patch('races.views.track')
        track_patch.start()
        self.addCleanup(track_patch.stop)

    def race(self, slug: str, **overrides: Any) -> Race:
        fields = {
            'title': '2026 가을 마라톤',
            'slug': slug,
            'sport': 'running',
            'race_date': self.today + timedelta(days=10),
            'location': '테스트 장소',
            'region': '서울',
            'registration_start': self.today - timedelta(days=10),
            'registration_end': self.today + timedelta(days=2),
        }
        fields.update(overrides)
        return Race.objects.create(**fields)

    def test_manual_cancellation_remains_cancelled_after_race_date(self) -> None:
        race = self.race(
            'manual', status='cancelled', race_date=self.today - timedelta(days=1),
        )

        self.assertEqual(race.computed_status, 'cancelled')
        self.assertEqual(race.status_label, '대회 취소')
        self.assertFalse(race.is_registration_open)
        self.assertIsNone(race.days_until_registration_end)
        self.assertFalse(Race.objects.by_status('finished').filter(pk=race.pk).exists())

    def test_title_notices_override_open_status_and_match_sql_filter(self) -> None:
        titles = (
            '2026 하남 미사 대회 취소',
            '대회취소',
            '[취소] 2026 가을 마라톤',
            '2026 가을 마라톤 (취소)',
            '2026 가을 마라톤 취소 안내',
        )
        for index, title in enumerate(titles):
            with self.subTest(title=title):
                race = self.race(f'title-{index}', title=title, status='registration_open')
                self.assertEqual(race.computed_status, 'cancelled')
                self.assertFalse(race.is_registration_open)
                self.assertIsNone(race.days_until_registration_end)
                self.assertTrue(Race.objects.by_status('cancelled').filter(pk=race.pk).exists())
                self.assertFalse(Race.objects.registration_open().filter(pk=race.pk).exists())
                self.assertFalse(Race.objects.closing_soon().filter(pk=race.pk).exists())

    def test_description_declarations_override_date_status_and_match_sql_filter(self) -> None:
        notices = (
            '참가자가 150여명으로 대회운영이 어려워 대회 취소합니다 참가신청자 여러분의 넓은 이해 부탁 드립니다',
            '부득이하게 대회를 취소합니다.',
            '본 대회가 전면 취소되었습니다.',
            '행사는 취소되었습니다. 환불은 별도로 안내하겠습니다.',
        )
        for index, notice in enumerate(notices):
            with self.subTest(notice=notice):
                race = self.race(f'notice-{index}', description=notice)
                self.assertEqual(race.computed_status, 'cancelled')
                self.assertTrue(Race.objects.by_status('cancelled').filter(pk=race.pk).exists())
                self.assertFalse(Race.objects.by_status('registration_open').filter(pk=race.pk).exists())

    def test_refund_rules_and_conditional_cancellation_do_not_cancel_event(self) -> None:
        policies = (
            '참가 취소 및 환불 규정: 접수 취소는 홈페이지에서 가능합니다.',
            '천재지변으로 대회가 취소될 경우 참가비를 환불합니다.',
            '대회 취소 시 참가비는 반환되지 않습니다.',
            '대회를 취소하지 않습니다. 정상 개최합니다.',
            '천재지변이 발생하면 대회가 취소됩니다.',
            '우천 시 행사는 취소됩니다.',
            '우천 시 대회를 취소합니다.',
            '우천시 대회를 취소합니다.',
            '참가자가 부족하면 대회를 취소합니다.',
            '참가 인원이 미달인 경우 대회를 취소합니다.',
            '태풍이 올 때 행사를 취소합니다.',
            '운영 규정\n만약 강풍이 예상된다면 대회를 취소합니다.',
            '우천 시\n대회를 취소합니다.',
        )
        for index, policy in enumerate(policies):
            with self.subTest(policy=policy):
                race = self.race(f'policy-{index}', description=policy)
                self.assertEqual(race.computed_status, 'registration_open')
                self.assertTrue(Race.objects.registration_open().filter(pk=race.pk).exists())
                self.assertFalse(Race.objects.by_status('cancelled').filter(pk=race.pk).exists())

    def test_confirmed_announcement_can_follow_conditional_policy_in_another_sentence(self) -> None:
        descriptions = (
            '우천 시 대회를 취소합니다. 이번 대회는 취소되었습니다.',
            '참가자가 부족하면 대회를 취소합니다. 올해는 참가 인원 미달로 대회를 취소합니다.',
            '태풍이 올 때 행사를 취소합니다.\n이번 행사는 취소되었습니다.',
        )
        for index, description in enumerate(descriptions):
            with self.subTest(description=description):
                race = self.race(f'confirmed-{index}', description=description, status='registration_open')
                self.assertEqual(race.computed_status, 'cancelled')
                self.assertTrue(Race.objects.by_status('cancelled').filter(pk=race.pk).exists())
                self.assertFalse(Race.objects.registration_open().filter(pk=race.pk).exists())

    def test_cancelled_status_filter_does_not_include_other_automatic_statuses(self) -> None:
        cancelled = self.race('cancelled', status='cancelled')
        self.race('open')
        upcoming = self.race('future-registration', registration_start=self.today + timedelta(days=1))

        self.assertEqual(list(Race.objects.by_status('cancelled')), [cancelled])
        self.assertEqual(
            set(Race.objects.by_status(['cancelled', 'upcoming'])),
            {cancelled, upcoming},
        )

    def test_detail_and_calendar_never_expose_cancellation_as_open(self) -> None:
        race = self.race('notice-detail', title='2026 하남 미사 대회 취소')
        detail = self.client.get(f'/api/v1/races/{race.slug}/')
        self.assertEqual(detail.status_code, 200)
        payload = detail.json()['race']
        self.assertEqual(payload['status'], 'cancelled')
        self.assertEqual(payload['statusLabel'], '대회 취소')
        self.assertFalse(payload['isRegistrationOpen'])
        self.assertIsNone(payload['daysUntilRegistrationEnd'])

        calendar = self.client.get('/api/v1/races/calendar/', {'year': '2026', 'month': '11'})
        self.assertEqual(calendar.status_code, 200)
        calendar_race = calendar.json()['racesGrouped'][race.race_date.isoformat()][0]
        self.assertEqual(calendar_race['status'], 'cancelled')
        self.assertIsNone(calendar_race['daysUntilRegistrationEnd'])

    def test_api_open_and_closing_filters_exclude_cancelled_and_preserve_other_filters(self) -> None:
        active = self.race('active')
        self.race('manual-cancelled', status='cancelled')
        self.race('notice-cancelled', title='2026 가을 마라톤 취소', status='registration_open')
        self.race('description-cancelled', description='대회를 취소합니다.')
        self.race('other-region', region='부산')

        for params in (
            {'status': 'registration_open'},
            {'status': 'closing_soon'},
            {'closing_soon': 'true'},
            {'status': ['registration_open', 'closing_soon']},
        ):
            with self.subTest(params=params):
                response = self.client.get('/api/v1/races/', {**params, 'region': '서울'})
                self.assertEqual(response.status_code, 200)
                self.assertEqual([row['id'] for row in response.json()['results']], [active.pk])

    def test_related_open_slot_and_recommendations_exclude_all_cancellation_forms(self) -> None:
        viewed = self.race('viewed')
        active = self.race('active-related')
        manual = self.race('manual-related', status='cancelled', view_count=1000)
        notice = self.race('notice-related', description='대회를 취소합니다.', view_count=900)

        response = self.client.get(f'/api/v1/races/{viewed.slug}/')
        self.assertEqual(response.status_code, 200)
        open_slot = next(
            slot for slot in response.json()['relatedRaces'] if slot['label'] == '지금 접수 가능한 대회'
        )
        self.assertEqual([row['id'] for row in open_slot['races']], [active.pk])
        recommended_ids = {row.pk for row in popular_recommendations()['races']}
        self.assertNotIn(manual.pk, recommended_ids)
        self.assertNotIn(notice.pk, recommended_ids)
