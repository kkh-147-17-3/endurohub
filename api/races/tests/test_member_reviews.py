from copy import deepcopy
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APITransactionTestCase

from accounts.models import RaceRecord, UserProfile
from races.models import Race, Review

User = get_user_model()


TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'member-review-tests',
    },
}


class MemberReviewTestDataMixin:
    def set_up_review_data(self):
        cache.clear()
        self.track_patcher = patch('races.views.track')
        self.track_patcher.start()
        self.addCleanup(self.track_patcher.stop)
        self.addCleanup(cache.clear)

        self.race = Race.objects.create(
            title='테스트 마라톤',
            slug='test-marathon',
            sport='running',
            race_date=timezone.localdate() - timedelta(days=1),
            location='서울',
            region='서울',
            distances=[
                {'name': '10km', 'distance_meter': 10000},
                {'name': '하프코스', 'distance_meter': 21097.5},
            ],
        )
        self.url = reverse('review-create', kwargs={'slug': self.race.slug})
        self.payload = {
            'nickname': '조작된 닉네임',
            'rating': 5,
            'comment': '정말 즐거운 대회였습니다.',
            'race_record': {
                'course_code': '10K',
                'hours': 1,
                'minutes': 2,
                'seconds': 3,
            },
        }

    def make_user(self, email='runner@example.com', verified=True):
        user = User.objects.create_user(username=email, email=email)
        UserProfile.objects.create(
            user=user,
            nickname=f'러너{user.pk}',
            email_verified=verified,
        )
        return user


@override_settings(CACHES=TEST_CACHES)
class MemberReviewTests(MemberReviewTestDataMixin, APITestCase):
    """Review + curated RaceRecord API contract and validation regressions."""

    def setUp(self):
        self.set_up_review_data()

    def test_anonymous_member_cannot_create_review(self):
        response = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Review.objects.exists())
        self.assertFalse(RaceRecord.objects.exists())

    def test_email_verification_is_required(self):
        user = self.make_user(verified=False)
        self.client.force_authenticate(user=user)

        response = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Review.objects.exists())
        self.assertFalse(RaceRecord.objects.exists())

    def test_review_is_owned_by_member_and_uses_profile_nickname(self):
        user = self.make_user()
        self.client.force_authenticate(user=user)

        response = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(response.status_code, 201)
        review = Review.objects.get()
        self.assertEqual(review.user, user)
        self.assertEqual(review.nickname, user.profile.nickname)
        self.assertNotEqual(review.nickname, self.payload['nickname'])
        self.assertEqual(review.completion_time, '1:02:03')

        record = RaceRecord.objects.get(user=user, race=self.race)
        self.assertEqual(record.course_code, '10K')
        self.assertEqual(record.distance, '10km')
        self.assertEqual(record.duration_seconds, 1 * 3600 + 2 * 60 + 3)
        self.assertEqual(response.data['race_record']['id'], record.pk)

    def test_race_record_payload_is_required(self):
        user = self.make_user()
        self.client.force_authenticate(user=user)
        payload = deepcopy(self.payload)
        payload.pop('race_record')

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, 422)
        self.assertFalse(Review.objects.exists())
        self.assertFalse(RaceRecord.objects.exists())

    def test_invalid_review_does_not_create_race_record(self):
        user = self.make_user()
        self.client.force_authenticate(user=user)
        payload = deepcopy(self.payload)
        payload['comment'] = '짧음'

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, 422)
        self.assertFalse(Review.objects.exists())
        self.assertFalse(RaceRecord.objects.exists())

    def test_unknown_course_does_not_create_review_or_record(self):
        user = self.make_user()
        self.client.force_authenticate(user=user)
        payload = deepcopy(self.payload)
        payload['race_record']['course_code'] = 'FULL'

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, 422)
        self.assertFalse(Review.objects.exists())
        self.assertFalse(RaceRecord.objects.exists())

    def test_distance_less_cycling_race_normalizes_legacy_fallback_code(self):
        self.race.sport = 'cycling'
        self.race.distances = []
        self.race.save(update_fields=['sport', 'distances'])
        user = self.make_user()
        self.client.force_authenticate(user=user)
        payload = deepcopy(self.payload)
        payload['race_record']['course_code'] = 'CYCLE'

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, 201)
        record = RaceRecord.objects.get(user=user, race=self.race)
        self.assertEqual(record.course_code, 'CYC')
        self.assertEqual(record.distance, '자전거')

    def test_zero_duration_does_not_create_review_or_record(self):
        user = self.make_user()
        self.client.force_authenticate(user=user)
        payload = deepcopy(self.payload)
        payload['race_record'].update(hours=0, minutes=0, seconds=0)

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, 422)
        self.assertFalse(Review.objects.exists())
        self.assertFalse(RaceRecord.objects.exists())

    def test_record_time_component_ranges_are_validated_without_partial_write(self):
        user = self.make_user()
        self.client.force_authenticate(user=user)

        for field, value in (('hours', 100), ('minutes', 60), ('seconds', 60)):
            with self.subTest(field=field, value=value):
                cache.clear()
                payload = deepcopy(self.payload)
                payload['race_record'][field] = value

                response = self.client.post(self.url, payload, format='json')

                self.assertEqual(response.status_code, 422)
                self.assertFalse(Review.objects.exists())
                self.assertFalse(RaceRecord.objects.exists())

    def test_completion_time_is_derived_from_record_instead_of_legacy_input(self):
        user = self.make_user()
        self.client.force_authenticate(user=user)
        payload = deepcopy(self.payload)
        payload['completion_time'] = 'legacy free-form value'
        payload['race_record'].update(hours=0, minutes=42, seconds=5)

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Review.objects.get().completion_time, '0:42:05')
        self.assertEqual(RaceRecord.objects.get().duration_seconds, 42 * 60 + 5)

    def test_existing_record_is_upserted_in_place_and_preserves_user_flags(self):
        user = self.make_user()
        existing = RaceRecord.objects.create(
            user=user,
            race=self.race,
            sport='running',
            distance='10km',
            course_code='10K',
            name=self.race.title,
            record_date=self.race.race_date.isoformat(),
            duration_seconds=55 * 60,
            is_personal_best=True,
            is_public=True,
        )
        original_pk = existing.pk
        previous_updated_at = timezone.now() - timedelta(days=30)
        RaceRecord.objects.filter(pk=existing.pk).update(updated_at=previous_updated_at)
        self.client.force_authenticate(user=user)

        response = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(RaceRecord.objects.filter(user=user, race=self.race).count(), 1)
        existing.refresh_from_db()
        self.assertEqual(existing.pk, original_pk)
        self.assertEqual(existing.duration_seconds, 1 * 3600 + 2 * 60 + 3)
        self.assertTrue(existing.is_personal_best)
        self.assertTrue(existing.is_public)
        self.assertGreater(existing.updated_at, previous_updated_at)
        self.assertEqual(Review.objects.filter(user=user, race=self.race).count(), 1)

    def test_member_can_review_same_race_only_once(self):
        user = self.make_user()
        self.client.force_authenticate(user=user)

        first = self.client.post(self.url, self.payload, format='json')
        second = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 400)
        self.assertEqual(Review.objects.filter(user=user, race=self.race).count(), 1)
        self.assertEqual(RaceRecord.objects.filter(user=user, race=self.race).count(), 1)

    def test_duplicate_review_does_not_mutate_race_record(self):
        user = self.make_user()
        self.client.force_authenticate(user=user)
        first = self.client.post(self.url, self.payload, format='json')
        record = RaceRecord.objects.get(user=user, race=self.race)
        original_pk = record.pk
        original_duration = record.duration_seconds
        changed_payload = deepcopy(self.payload)
        changed_payload['race_record'].update(hours=2, minutes=30, seconds=0)

        second = self.client.post(self.url, changed_payload, format='json')

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 400)
        record.refresh_from_db()
        self.assertEqual(record.pk, original_pk)
        self.assertEqual(record.duration_seconds, original_duration)

    def test_future_race_cannot_be_reviewed_through_api(self):
        self.race.race_date = timezone.localdate() + timedelta(days=1)
        self.race.save(update_fields=['race_date'])
        user = self.make_user()
        self.client.force_authenticate(user=user)

        response = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Review.objects.exists())
        self.assertFalse(RaceRecord.objects.exists())


@override_settings(CACHES=TEST_CACHES)
class MemberReviewTransactionTests(MemberReviewTestDataMixin, APITransactionTestCase):
    """Use real commits so the test runner cannot hide a missing view-level atomic block."""

    reset_sequences = True

    def setUp(self):
        self.set_up_review_data()
        self.user = self.make_user()
        self.client.force_authenticate(user=self.user)

    def post_while_upsert_raises_after_write(self):
        real_update_or_create = RaceRecord.objects.update_or_create

        def update_then_raise(*args, **kwargs):
            real_update_or_create(*args, **kwargs)
            raise RuntimeError('injected RaceRecord upsert failure')

        with patch.object(
            RaceRecord.objects,
            'update_or_create',
            side_effect=update_then_raise,
        ):
            with self.assertRaisesMessage(RuntimeError, 'injected RaceRecord upsert failure'):
                self.client.post(self.url, self.payload, format='json')

    def test_record_create_exception_rolls_back_review_and_record(self):
        self.post_while_upsert_raises_after_write()

        self.assertFalse(Review.objects.exists())
        self.assertFalse(RaceRecord.objects.exists())

    def test_record_update_exception_rolls_back_review_and_existing_record_changes(self):
        existing = RaceRecord.objects.create(
            user=self.user,
            race=self.race,
            sport='running',
            distance='10km',
            course_code='10K',
            name=self.race.title,
            record_date=self.race.race_date.isoformat(),
            duration_seconds=48 * 60,
            is_personal_best=True,
            is_public=True,
        )
        original_pk = existing.pk

        self.post_while_upsert_raises_after_write()

        self.assertFalse(Review.objects.exists())
        self.assertEqual(RaceRecord.objects.filter(user=self.user, race=self.race).count(), 1)
        existing.refresh_from_db()
        self.assertEqual(existing.pk, original_pk)
        self.assertEqual(existing.duration_seconds, 48 * 60)
        self.assertTrue(existing.is_personal_best)
        self.assertTrue(existing.is_public)
