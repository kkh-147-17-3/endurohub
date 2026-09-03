from django.test import TestCase
from django.utils import timezone

from .models import Notice


class NoticeSlugDetailTests(TestCase):
    def setUp(self):
        self.notice, _ = Notice.objects.update_or_create(
            slug='coffee-coupon-event',
            defaults={
                'category': 'event',
                'title': '스타벅스 카페 아메리카노 T 이벤트',
                'published_at': timezone.now(),
                'view_count': 0,
            },
        )

    def test_slug_detail_increments_view_count(self):
        response = self.client.get('/api/v1/notices/by-slug/coffee-coupon-event/')

        self.assertEqual(response.status_code, 200)
        self.notice.refresh_from_db()
        self.assertEqual(self.notice.view_count, 1)
        self.assertEqual(response.json()['notice']['views'], 1)

    def test_list_exposes_custom_href_and_current_views(self):
        self.notice.view_count = 7
        self.notice.save(update_fields=['view_count'])

        response = self.client.get('/api/v1/notices/?tab=event')

        self.assertEqual(response.status_code, 200)
        item = response.json()['data'][0]
        self.assertEqual(item['href'], '/notice/coffee-coupon-event')
        self.assertEqual(item['views'], 7)
        self.assertEqual(response.json()['counts']['event'], 1)
