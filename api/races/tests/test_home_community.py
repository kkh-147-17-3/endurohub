from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import RaceRecord, UserProfile
from races.models import Race, Review


User = get_user_model()

TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'home-community-tests',
    },
}


@override_settings(CACHES=TEST_CACHES)
class HomeCommunityTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.url = reverse('home-community')
        self.race = Race.objects.create(
            title='홈 피드 테스트 마라톤',
            slug='home-feed-marathon',
            sport='running',
            race_date=timezone.localdate() - timedelta(days=1),
            location='서울',
            region='서울',
            distances=[{'name': '10km', 'distance_meter': 10000}],
        )

    def make_user(self, index):
        user = User.objects.create_user(
            username=f'runner{index}@example.com',
            email=f'runner{index}@example.com',
        )
        UserProfile.objects.create(user=user, nickname=f'러너{index}', email_verified=True)
        return user

    def test_empty_feed(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'recentReviews': [], 'recentRecords': []})

    def test_returns_only_five_latest_reviews_with_race_context(self):
        base = timezone.now() - timedelta(hours=1)
        reviews = []
        for index in range(6):
            review = Review.objects.create(
                race=self.race,
                nickname=f'익명러너{index}',
                rating=5,
                comment=f'최신 리뷰 순서 확인 {index}',
                completion_time=f'0:{40 + index}:00',
                ip_hash=f'ip-{index}',
            )
            Review.objects.filter(pk=review.pk).update(created_at=base + timedelta(minutes=index))
            reviews.append(review)

        with self.assertNumQueries(3):
            response = self.client.get(self.url)
        payload = response.json()
        items = payload['recentReviews']

        self.assertEqual([item['id'] for item in items], [review.id for review in reviews[:0:-1]])
        self.assertEqual(items[0]['race']['slug'], self.race.slug)
        self.assertEqual(items[0]['race']['title'], self.race.title)
        self.assertEqual(items[0]['race']['sport'], 'running')
        self.assertEqual(items[0]['race']['raceDate'], self.race.race_date.isoformat())
        self.assertNotIn('ipHash', items[0])

    def test_records_are_latest_public_catalogue_finishes_only(self):
        base = timezone.now() - timedelta(hours=1)
        public_records = []
        for index in range(6):
            record = RaceRecord.objects.create(
                user=self.make_user(index),
                race=self.race,
                sport='running',
                distance='10km',
                course_code='10K',
                name=self.race.title,
                record_date=self.race.race_date.isoformat(),
                duration_seconds=(40 + index) * 60,
                is_public=True,
            )
            RaceRecord.objects.filter(pk=record.pk).update(created_at=base + timedelta(minutes=index))
            public_records.append(record)

        private_record = RaceRecord.objects.create(
            user=self.make_user(10),
            race=self.race,
            sport='running',
            distance='10km',
            course_code='10K',
            duration_seconds=39 * 60,
            is_public=False,
        )
        freeform_record = RaceRecord.objects.create(
            user=self.make_user(11),
            race=None,
            sport='running',
            distance='10km',
            course_code='',
            name='직접 입력 대회',
            duration_seconds=38 * 60,
            is_public=True,
        )
        newest = base + timedelta(hours=2)
        RaceRecord.objects.filter(pk__in=[private_record.pk, freeform_record.pk]).update(created_at=newest)

        with self.assertNumQueries(2):
            response = self.client.get(self.url)
        items = response.json()['recentRecords']

        self.assertEqual([item['id'] for item in items], [record.id for record in public_records[:0:-1]])
        self.assertEqual(items[0]['nickname'], '러너5')
        self.assertEqual(items[0]['courseLabel'], '10km')
        self.assertEqual(items[0]['time'], '0:45:00')
        self.assertEqual(items[0]['metricLabel'], '평균 페이스')
        self.assertEqual(items[0]['metricValue'], '4′30″/km')
        self.assertEqual(items[0]['race']['slug'], self.race.slug)
        self.assertFalse(items[0]['me'])

        self.client.force_authenticate(user=public_records[-1].user)
        signed_in_items = self.client.get(self.url).json()['recentRecords']
        self.assertTrue(signed_in_items[0]['me'])

    def test_record_metric_matches_the_race_sport(self):
        cases = [
            ('running', 21097.5, '21.1K', '21.0975km', 1 * 3600 + 50 * 60, '평균 페이스', '5′13″/km'),
            ('trail_running', 40000, '40K', '40km', 5 * 3600 + 24 * 60 + 16, '평균 페이스', '8′06″/km'),
            ('cycling', 78000, '78K', '78km', 2 * 3600 + 46 * 60 + 19, '평균 속도', '28.1 km/h'),
            ('swimming', 1500, '1.5K', '1,500m', 31 * 60 + 48, '평균 페이스', '2′07″/100m'),
        ]
        for index, (sport, meters, code, label, duration, _, _) in enumerate(cases, start=20):
            race = Race.objects.create(
                title=f'종목별 지표 테스트 {sport}',
                slug=f'home-metric-{sport}',
                sport=sport,
                race_date=self.race.race_date,
                location='서울',
                region='서울',
                distances=[{'name': label, 'distance_meter': meters}],
            )
            RaceRecord.objects.create(
                user=self.make_user(index),
                race=race,
                sport=sport,
                distance=label,
                course_code=code,
                duration_seconds=duration,
                is_public=True,
            )

        items_by_sport = {
            item['sport']: item
            for item in self.client.get(self.url).json()['recentRecords']
        }

        for sport, _, _, _, _, metric_label, metric_value in cases:
            self.assertEqual(items_by_sport[sport]['metricLabel'], metric_label)
            self.assertEqual(items_by_sport[sport]['metricValue'], metric_value)

    def test_review_like_state_is_scoped_to_the_request_ip(self):
        review = Review.objects.create(
            race=self.race,
            nickname='공감 러너',
            rating=4,
            comment='공감 상태를 확인하는 리뷰입니다.',
            ip_hash='author-ip',
        )
        like_url = reverse(
            'review-like-toggle',
            kwargs={'slug': self.race.slug, 'review_id': review.pk},
        )

        self.client.post(like_url, REMOTE_ADDR='198.51.100.7')
        liked = self.client.get(self.url, REMOTE_ADDR='198.51.100.7').json()['recentReviews'][0]
        other = self.client.get(self.url, REMOTE_ADDR='198.51.100.8').json()['recentReviews'][0]

        self.assertEqual(liked['likeCount'], 1)
        self.assertTrue(liked['hasLiked'])
        self.assertEqual(other['likeCount'], 1)
        self.assertFalse(other['hasLiked'])
