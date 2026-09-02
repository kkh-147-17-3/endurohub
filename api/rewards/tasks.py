import logging

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import CampaignWinner, GiftCoupon, RewardCampaign

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, ignore_result=True)
def send_reward_email_task(self, winner_id):
    """Send one prize email, safely ignoring duplicate task delivery."""
    with transaction.atomic():
        winner = (
            CampaignWinner.objects.select_for_update()
            .select_related('campaign', 'user__profile')
            .get(pk=winner_id)
        )
        if winner.status == CampaignWinner.STATUS_SENT:
            return
        if (
            winner.status == CampaignWinner.STATUS_SENDING
            and winner.delivery_started_at
            and winner.delivery_started_at > timezone.now() - timezone.timedelta(minutes=15)
        ):
            return
        winner.status = CampaignWinner.STATUS_SENDING
        winner.delivery_started_at = timezone.now()
        winner.email_attempts += 1
        winner.last_error = ''
        winner.save(update_fields=[
            'status', 'delivery_started_at', 'email_attempts',
            'last_error', 'updated_at',
        ])

    try:
        from .emails import send_winner_email
        winner = (
            CampaignWinner.objects.select_related('campaign', 'user__profile', 'coupon')
            .get(pk=winner_id)
        )
        send_winner_email(winner)
    except Exception as exc:
        CampaignWinner.objects.filter(pk=winner_id).update(
            status=CampaignWinner.STATUS_FAILED,
            last_error=str(exc)[:2000],
        )
        logger.exception('Failed to send reward email for winner %s', winner_id)
        raise self.retry(exc=exc, countdown=min(60 * (2 ** self.request.retries), 900))

    now = timezone.now()
    CampaignWinner.objects.filter(pk=winner_id).update(
        status=CampaignWinner.STATUS_SENT,
        email_sent_at=now,
        last_error='',
    )
    GiftCoupon.objects.filter(winner_id=winner_id).update(
        status=GiftCoupon.STATUS_SENT,
    )

    campaign_id = winner.campaign_id
    if not CampaignWinner.objects.filter(campaign_id=campaign_id).exclude(
        status=CampaignWinner.STATUS_SENT,
    ).exists():
        RewardCampaign.objects.filter(
            pk=campaign_id,
            status=RewardCampaign.STATUS_DRAWN,
        ).update(status=RewardCampaign.STATUS_COMPLETED)
