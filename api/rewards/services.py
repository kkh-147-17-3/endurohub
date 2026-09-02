import hashlib
import logging
import random
import secrets

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from races.models import Review

from .models import CampaignEntry, CampaignWinner, GiftCoupon, RewardCampaign

logger = logging.getLogger(__name__)


def enroll_review_in_active_campaigns(review):
    """Add a verified member review to every campaign currently accepting entries."""
    if not review.user_id:
        return 0
    user = review.user
    profile = getattr(user, 'profile', None)
    if not profile or not profile.email_verified or not user.email:
        return 0

    campaigns = RewardCampaign.objects.filter(
        status=RewardCampaign.STATUS_OPEN,
        starts_at__lte=review.created_at,
        ends_at__gte=review.created_at,
    )
    created = 0
    for campaign in campaigns:
        _, was_created = CampaignEntry.objects.get_or_create(
            campaign=campaign,
            user=user,
            defaults={'review': review},
        )
        created += int(was_created)
    return created


def _eligible_reviews(campaign):
    """Return the first eligible review per member in a stable order."""
    reviews = Review.objects.filter(
        user__isnull=False,
        user__email__gt='',
        user__profile__email_verified=True,
        created_at__gte=campaign.starts_at,
        created_at__lte=campaign.ends_at,
    ).select_related('user').order_by('user_id', 'created_at', 'id')

    first_by_user = {}
    for review in reviews:
        first_by_user.setdefault(review.user_id, review)
    return list(first_by_user.values())


def rebuild_campaign_entries(campaign):
    """Freeze current eligible reviews into one entry per member."""
    reviews = _eligible_reviews(campaign)
    CampaignEntry.objects.filter(campaign=campaign).delete()
    CampaignEntry.objects.bulk_create([
        CampaignEntry(campaign=campaign, review=review, user=review.user)
        for review in reviews
    ])
    return list(
        CampaignEntry.objects.filter(campaign=campaign)
        .select_related('user', 'review')
        .order_by('user_id', 'review_id')
    )


@transaction.atomic
def draw_campaign(campaign_id):
    """Draw winners once, assign coupons, and persist an auditable snapshot."""
    campaign = RewardCampaign.objects.select_for_update().get(pk=campaign_id)
    if campaign.status != RewardCampaign.STATUS_OPEN:
        raise ValidationError('응모 중 상태인 캠페인만 추첨할 수 있습니다.')
    if timezone.now() < campaign.ends_at:
        raise ValidationError('캠페인 종료 시각 이후에 추첨할 수 있습니다.')
    if campaign.drawn_at or campaign.winners.exists():
        raise ValidationError('이미 추첨된 캠페인입니다.')

    entries = rebuild_campaign_entries(campaign)
    if len(entries) < campaign.winners_count:
        raise ValidationError(
            f'응모자가 부족합니다. 필요 {campaign.winners_count}명, 현재 {len(entries)}명입니다.'
        )

    coupons = list(
        GiftCoupon.objects.select_for_update()
        .filter(campaign=campaign, status=GiftCoupon.STATUS_AVAILABLE, winner__isnull=True)
        .order_by('id')[:campaign.winners_count]
    )
    if len(coupons) < campaign.winners_count:
        raise ValidationError(
            f'사용 가능한 쿠폰이 부족합니다. 필요 {campaign.winners_count}개, 현재 {len(coupons)}개입니다.'
        )

    candidate_payload = ','.join(
        f'{entry.user_id}:{entry.review_id}' for entry in entries
    )
    candidate_hash = hashlib.sha256(candidate_payload.encode()).hexdigest()
    draw_seed = secrets.token_hex(32)
    rng = random.Random(int(draw_seed, 16))
    selected_entries = rng.sample(entries, campaign.winners_count)

    winner_ids = []
    for entry, coupon in zip(selected_entries, coupons):
        winner = CampaignWinner.objects.create(
            campaign=campaign,
            entry=entry,
            user=entry.user,
            email=entry.user.email,
        )
        coupon.winner = winner
        coupon.status = GiftCoupon.STATUS_ASSIGNED
        coupon.save(update_fields=['winner', 'status', 'updated_at'])
        winner_ids.append(winner.id)

    campaign.status = RewardCampaign.STATUS_DRAWN
    campaign.candidate_count = len(entries)
    campaign.candidate_hash = candidate_hash
    campaign.draw_seed = draw_seed
    campaign.drawn_at = timezone.now()
    campaign.save(update_fields=[
        'status', 'candidate_count', 'candidate_hash', 'draw_seed',
        'drawn_at', 'updated_at',
    ])

    transaction.on_commit(lambda: queue_winner_emails(winner_ids))
    return winner_ids


def queue_winner_emails(winner_ids):
    from .tasks import send_reward_email_task

    for winner_id in winner_ids:
        try:
            send_reward_email_task.delay(winner_id)
        except Exception:
            # The draw is already safely persisted. Staff can retry pending
            # winners from Django Admin after the broker recovers.
            logger.exception('Failed to queue reward email for winner %s', winner_id)
