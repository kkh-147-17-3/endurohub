from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import UserProfile
from races.models import Race, Review
from rewards.models import CampaignEntry, CampaignWinner, GiftCoupon, RewardCampaign
from rewards.services import draw_campaign
from rewards.tasks import send_reward_email_task

User = get_user_model()


class RewardCampaignTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.race = self.make_race('reward-race-1')
        self.other_race = self.make_race('reward-race-2')

    def make_race(self, slug):
        return Race.objects.create(
            title=slug,
            slug=slug,
            sport='running',
            race_date=timezone.localdate() - timedelta(days=10),
            location='서울',
            region='서울',
        )

    def make_user(self, email, verified=True):
        user = User.objects.create_user(username=email, email=email)
        UserProfile.objects.create(
            user=user,
            nickname=email.split('@')[0],
            email_verified=verified,
        )
        return user

    def make_review(self, user, race, created_at=None):
        review = Review.objects.create(
            race=race,
            user=user,
            nickname=user.profile.nickname,
            rating=5,
            comment='이벤트 응모용 리뷰입니다.',
            ip_hash=f'ip-{user.pk}-{race.pk}'.ljust(64, '0'),
        )
        Review.objects.filter(pk=review.pk).update(
            created_at=created_at or self.now - timedelta(days=1),
        )
        review.refresh_from_db()
        return review

    def make_campaign(self, winners_count=1):
        return RewardCampaign.objects.create(
            name='9월 리뷰 이벤트',
            starts_at=self.now - timedelta(days=2),
            ends_at=self.now - timedelta(hours=1),
            winners_count=winners_count,
            status=RewardCampaign.STATUS_OPEN,
        )

    @patch('rewards.services.queue_winner_emails')
    def test_draw_uses_one_entry_per_verified_member(self, queue_emails):
        first = self.make_user('first@example.com')
        second = self.make_user('second@example.com')
        unverified = self.make_user('unverified@example.com', verified=False)
        self.make_review(first, self.race)
        self.make_review(first, self.other_race)
        self.make_review(second, self.race)
        self.make_review(unverified, self.race)
        campaign = self.make_campaign(winners_count=2)
        GiftCoupon.objects.create(campaign=campaign, code='COUPON-A')
        GiftCoupon.objects.create(campaign=campaign, code='COUPON-B')

        with self.captureOnCommitCallbacks(execute=True):
            winner_ids = draw_campaign(campaign.pk)

        campaign.refresh_from_db()
        self.assertEqual(len(winner_ids), 2)
        self.assertEqual(CampaignEntry.objects.filter(campaign=campaign).count(), 2)
        self.assertEqual(CampaignWinner.objects.filter(campaign=campaign).count(), 2)
        self.assertEqual(campaign.status, RewardCampaign.STATUS_DRAWN)
        self.assertEqual(campaign.candidate_count, 2)
        self.assertEqual(len(campaign.candidate_hash), 64)
        self.assertEqual(len(campaign.draw_seed), 64)
        self.assertEqual(
            GiftCoupon.objects.filter(campaign=campaign, status=GiftCoupon.STATUS_ASSIGNED).count(),
            2,
        )
        queue_emails.assert_called_once_with(winner_ids)

    @patch('rewards.services.queue_winner_emails')
    def test_campaign_cannot_be_drawn_twice(self, queue_emails):
        user = self.make_user('runner@example.com')
        self.make_review(user, self.race)
        campaign = self.make_campaign()
        GiftCoupon.objects.create(campaign=campaign, code='ONLY-ONCE')

        with self.captureOnCommitCallbacks(execute=True):
            draw_campaign(campaign.pk)

        with self.assertRaises(ValidationError):
            draw_campaign(campaign.pk)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='contact@endurohub.kr',
    )
    @patch('rewards.services.queue_winner_emails')
    def test_winner_task_sends_coupon_and_marks_campaign_complete(self, queue_emails):
        user = self.make_user('winner@example.com')
        self.make_review(user, self.race)
        campaign = self.make_campaign()
        GiftCoupon.objects.create(
            campaign=campaign,
            code='STARBUCKS-1234',
            redemption_url='https://example.com/coupon',
        )
        with self.captureOnCommitCallbacks(execute=True):
            winner_id = draw_campaign(campaign.pk)[0]

        send_reward_email_task.run(winner_id)

        winner = CampaignWinner.objects.get(pk=winner_id)
        campaign.refresh_from_db()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['winner@example.com'])
        self.assertIn('STARBUCKS-1234', mail.outbox[0].body)
        self.assertEqual(winner.status, CampaignWinner.STATUS_SENT)
        self.assertIsNotNone(winner.email_sent_at)
        self.assertEqual(winner.coupon.status, GiftCoupon.STATUS_SENT)
        self.assertEqual(campaign.status, RewardCampaign.STATUS_COMPLETED)
