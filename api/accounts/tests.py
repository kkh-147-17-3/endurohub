from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from races.models import Race

from .models import RaceRecord


User = get_user_model()


class RaceRecordDefaultsTests(APITestCase):
    def make_user(self):
        return User.objects.create_user(
            username='runner@example.com',
            email='runner@example.com',
        )

    def make_race(self):
        return Race.objects.create(
            title='공개 설정 테스트 대회',
            slug='record-visibility-test',
            sport='running',
            race_date=timezone.localdate() - timedelta(days=1),
            distances=[{'name': '10km', 'distance_meter': 10000}],
        )

    def test_free_form_record_is_private_by_default(self):
        user = self.make_user()
        self.client.force_authenticate(user=user)

        response = self.client.post('/api/v1/me/records/', {
            'sport': 'running',
            'distance': '10K',
            'hours': 1,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        record = RaceRecord.objects.get(user=user)
        self.assertFalse(record.is_public)
        self.assertFalse(response.data['records'][0]['is_public'])

    def test_linked_record_visibility_requires_an_explicit_public_choice(self):
        user = self.make_user()
        race = self.make_race()
        self.client.force_authenticate(user=user)
        url = f'/api/v1/me/races/{race.slug}/result/'
        payload = {
            'course_code': '10K',
            'hours': 1,
        }

        private_response = self.client.post(url, payload, format='json')
        self.assertEqual(private_response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(RaceRecord.objects.get(user=user, race=race).is_public)

        public_response = self.client.post(
            url,
            {**payload, 'is_public': True},
            format='json',
        )
        self.assertEqual(public_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(RaceRecord.objects.get(user=user, race=race).is_public)

        season_response = self.client.get(
            f'/api/v1/me/season/?year={race.race_date.year}',
        )
        self.assertEqual(season_response.status_code, status.HTTP_200_OK)
        self.assertTrue(season_response.data['races'][0]['result']['public'])

        revoke_response = self.client.post(
            url,
            {**payload, 'is_public': False},
            format='json',
        )
        self.assertEqual(revoke_response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(RaceRecord.objects.get(user=user, race=race).is_public)
