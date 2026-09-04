from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import RaceRecord, UserProfile
from races.models import Race, Review


User = get_user_model()


class CoffeeCouponEventStatusTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='runner', email='runner@example.com')
        self.race = Race.objects.create(
            title='이벤트 테스트 대회',
            slug='coffee-event-test-race',
            sport='running',
            race_date=datetime(2026, 9, 10).date(),
            location='서울',
            region='서울',
        )
        self.client.force_authenticate(user=self.user)

    def event_time(self, day):
        return timezone.make_aware(
            datetime(2026, 9, day, 12),
            timezone.get_current_timezone(),
        )

    def set_record_times(self, record, value):
        RaceRecord.objects.filter(pk=record.pk).update(
            created_at=value,
            updated_at=value,
        )

    def test_reports_review_and_linked_record_created_during_event(self):
        review = Review.objects.create(
            race=self.race,
            user=self.user,
            nickname='runner',
            rating=5,
            comment='좋은 대회였습니다.',
            ip_hash='a' * 64,
        )
        Review.objects.filter(pk=review.pk).update(created_at=self.event_time(3))

        record = RaceRecord.objects.create(
            user=self.user,
            race=self.race,
            sport='running',
            distance='10km',
            duration_seconds=3600,
        )
        self.set_record_times(record, self.event_time(30))

        response = self.client.get('/api/v1/rewards/coffee-coupon-event/status/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['review']['completed'])
        self.assertTrue(response.data['record']['completed'])
        self.assertTrue(response.data['completed'])

    def test_marketing_opt_out_does_not_block_event_completion(self):
        UserProfile.objects.create(user=self.user, email_updates_opt_in=False)
        review = Review.objects.create(
            race=self.race, user=self.user, nickname='runner', rating=5,
            comment='마케팅 수신과 무관한 이벤트 참여', ip_hash='b' * 64,
        )
        Review.objects.filter(pk=review.pk).update(created_at=self.event_time(3))
        record = RaceRecord.objects.create(
            user=self.user, race=self.race, sport='running', distance='10km',
            duration_seconds=3600,
        )
        self.set_record_times(record, self.event_time(3))

        response = self.client.get('/api/v1/rewards/coffee-coupon-event/status/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['completed'])

    def test_excludes_free_form_and_out_of_period_records(self):
        review = Review.objects.create(
            race=self.race, user=self.user, nickname='runner', rating=5,
            comment='기간 밖 기록과 함께 남긴 리뷰', ip_hash='e' * 64,
        )
        Review.objects.filter(pk=review.pk).update(created_at=self.event_time(10))

        free_form = RaceRecord.objects.create(
            user=self.user,
            sport='running',
            distance='10km',
            duration_seconds=3600,
        )
        self.set_record_times(free_form, self.event_time(10))

        linked = RaceRecord.objects.create(
            user=self.user,
            race=self.race,
            sport='running',
            distance='10km',
            duration_seconds=3600,
        )
        self.set_record_times(
            linked,
            timezone.make_aware(datetime(2026, 10, 1), timezone.get_current_timezone()),
        )

        response = self.client.get('/api/v1/rewards/coffee-coupon-event/status/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['review']['completed'])
        self.assertFalse(response.data['record']['completed'])
        self.assertFalse(response.data['completed'])

    def test_counts_existing_record_updated_with_event_review(self):
        review = Review.objects.create(
            race=self.race, user=self.user, nickname='runner', rating=5,
            comment='기존 기록과 함께 남기는 리뷰', ip_hash='c' * 64,
        )
        Review.objects.filter(pk=review.pk).update(created_at=self.event_time(10))

        record = RaceRecord.objects.create(
            user=self.user, race=self.race, sport='running', distance='10km',
            duration_seconds=3600,
        )
        self.set_record_times(
            record,
            timezone.make_aware(datetime(2026, 8, 20), timezone.get_current_timezone()),
        )
        RaceRecord.objects.filter(pk=record.pk).update(updated_at=self.event_time(10))

        response = self.client.get('/api/v1/rewards/coffee-coupon-event/status/')

        self.assertTrue(response.data['record']['completed'])
        self.assertTrue(response.data['completed'])

    def test_record_for_another_race_does_not_complete_same_race_condition(self):
        other_race = Race.objects.create(
            title='다른 이벤트 테스트 대회',
            slug='another-coffee-event-test-race',
            sport='running',
            race_date=datetime(2026, 9, 11).date(),
            location='서울',
            region='서울',
        )
        review = Review.objects.create(
            race=self.race, user=self.user, nickname='runner', rating=5,
            comment='리뷰와 기록의 대회가 다릅니다.', ip_hash='d' * 64,
        )
        Review.objects.filter(pk=review.pk).update(created_at=self.event_time(10))
        record = RaceRecord.objects.create(
            user=self.user, race=other_race, sport='running', distance='10km',
            duration_seconds=3600,
        )
        self.set_record_times(record, self.event_time(10))

        response = self.client.get('/api/v1/rewards/coffee-coupon-event/status/')

        self.assertTrue(response.data['review']['completed'])
        self.assertFalse(response.data['record']['completed'])
        self.assertFalse(response.data['completed'])
