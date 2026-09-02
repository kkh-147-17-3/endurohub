from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import UserProfile
from races.models import Race, Review

User = get_user_model()


class MemberReviewTests(APITestCase):
    def setUp(self):
        self.race = Race.objects.create(
            title='테스트 마라톤',
            slug='test-marathon',
            sport='running',
            race_date=timezone.localdate() - timedelta(days=1),
            location='서울',
            region='서울',
        )
        self.url = reverse('review-create', kwargs={'slug': self.race.slug})
        self.payload = {
            'nickname': '조작된 닉네임',
            'rating': 5,
            'comment': '정말 즐거운 대회였습니다.',
        }

    def make_user(self, email='runner@example.com', verified=True):
        user = User.objects.create_user(username=email, email=email)
        UserProfile.objects.create(
            user=user,
            nickname=f'러너{user.pk}',
            email_verified=verified,
        )
        return user

    def test_anonymous_member_cannot_create_review(self):
        response = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Review.objects.exists())

    def test_email_verification_is_required(self):
        user = self.make_user(verified=False)
        self.client.force_authenticate(user=user)

        response = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Review.objects.exists())

    def test_review_is_owned_by_member_and_uses_profile_nickname(self):
        user = self.make_user()
        self.client.force_authenticate(user=user)

        response = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(response.status_code, 201)
        review = Review.objects.get()
        self.assertEqual(review.user, user)
        self.assertEqual(review.nickname, user.profile.nickname)
        self.assertNotEqual(review.nickname, self.payload['nickname'])

    def test_member_can_review_same_race_only_once(self):
        user = self.make_user()
        self.client.force_authenticate(user=user)

        first = self.client.post(self.url, self.payload, format='json')
        second = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 400)
        self.assertEqual(Review.objects.filter(user=user, race=self.race).count(), 1)

    def test_future_race_cannot_be_reviewed_through_api(self):
        self.race.race_date = timezone.localdate() + timedelta(days=1)
        self.race.save(update_fields=['race_date'])
        user = self.make_user()
        self.client.force_authenticate(user=user)

        response = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Review.objects.exists())
