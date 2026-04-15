import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def send_welcome_email_task(user_id):
    """Send welcome email to a newly registered user."""
    from accounts.emails import send_welcome_email
    from accounts.models import UserProfile

    try:
        profile = UserProfile.objects.select_related('user').get(user_id=user_id)
    except UserProfile.DoesNotExist:
        logger.warning('UserProfile not found for user_id=%s', user_id)
        return

    send_welcome_email(profile)


@shared_task(ignore_result=True)
def send_weekly_digest_task():
    """Send weekly digest email to all opted-in users."""
    from accounts.emails import send_weekly_digest_email
    from accounts.models import UserProfile

    profiles = UserProfile.objects.filter(
        email_verified=True,
        email_updates_opt_in=True,
    ).select_related('user')

    sent = 0
    failed = 0
    for profile in profiles:
        if not profile.user.email:
            continue
        success = send_weekly_digest_email(profile)
        if success:
            sent += 1
        else:
            failed += 1

    logger.info(
        'Weekly digest completed: sent=%d, failed=%d, total=%d',
        sent, failed, sent + failed,
    )


@shared_task(ignore_result=True)
def send_new_races_alert_task():
    """Check for races added in the last hour and notify opted-in users."""
    from django.utils import timezone

    from accounts.emails import send_new_races_alert
    from races.models import Race

    one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
    new_races = Race.objects.upcoming().filter(created_at__gte=one_hour_ago)

    count = new_races.count()
    if count == 0:
        logger.info('No new races in the last hour, skipping alert')
        return

    sent = send_new_races_alert(new_races)
    logger.info(
        'New races alert completed: new_races=%d, emails_sent=%d',
        count, sent,
    )
