from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import UserProfile

from .models import Notice, NoticeComment


User = get_user_model()

TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'notice-tests',
    },
}


@override_settings(CACHES=TEST_CACHES)
class NoticeSlugDetailTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
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

    def test_sitemap_payload_exposes_notice_canonical_identifier(self):
        response = self.client.get('/api/v1/sitemap/')

        self.assertEqual(response.status_code, 200)
        item = next(n for n in response.json()['notices'] if n['id'] == self.notice.id)
        self.assertEqual(item['slug'], 'coffee-coupon-event')
        self.assertIn('updatedAt', item)

    def test_authenticated_user_can_comment_and_reply(self):
        user = User.objects.create_user(username='runner@example.com', email='runner@example.com')
        UserProfile.objects.create(user=user, nickname='러너')
        self.client.force_authenticate(user=user)

        created = self.client.post(
            f'/api/v1/notices/{self.notice.id}/comments/',
            {'content': '이벤트 참여 방법이 명확해서 좋네요.'},
            format='json',
        )

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        comment_id = created.data['comment']['id']
        self.assertTrue(created.data['comment']['is_owner'])

        reply = self.client.post(
            f'/api/v1/notices/{self.notice.id}/comments/',
            {'content': '저도 참여합니다!', 'parent_id': comment_id},
            format='json',
        )
        self.assertEqual(reply.status_code, status.HTTP_201_CREATED)

        detail = self.client.get(f'/api/v1/notices/{self.notice.id}/')
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data['notice']['comment_count'], 2)
        self.assertEqual(detail.data['notice']['comments'][0]['nickname'], '러너')
        self.assertEqual(detail.data['notice']['comments'][0]['replies'][0]['content'], '저도 참여합니다!')

    def test_comment_owner_can_update_and_delete(self):
        user = User.objects.create_user(username='runner@example.com', email='runner@example.com')
        self.client.force_authenticate(user=user)
        comment = NoticeComment.objects.create(
            notice=self.notice,
            user=user,
            content='수정 전 댓글',
            ip_hash='test',
        )
        comment_url = f'/api/v1/notices/{self.notice.id}/comments/{comment.id}/'

        updated = self.client.put(comment_url, {'content': '수정한 댓글'}, format='json')
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertEqual(comment.content, '수정한 댓글')

        deleted = self.client.delete(comment_url)
        self.assertEqual(deleted.status_code, status.HTTP_200_OK)
        self.assertFalse(NoticeComment.objects.filter(pk=comment.pk).exists())

    def test_anonymous_comment_requires_password(self):
        response = self.client.post(
            f'/api/v1/notices/{self.notice.id}/comments/',
            {'nickname': '익명', 'content': '댓글'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn('password', response.data['errors'])
