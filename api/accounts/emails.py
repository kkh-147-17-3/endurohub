import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from races.constants import SPORT_CODES, SPORT_LABELS
from races.models import Race

logger = logging.getLogger(__name__)

APP_URL = getattr(settings, 'APP_URL', 'https://www.endurohub.kr')


def _make_absolute_url(url):
    """Convert relative URLs to absolute using APP_URL."""
    if not url:
        return None
    if url.startswith(('http://', 'https://')):
        return url
    return f'{APP_URL}{url}'


def _prepare_races_for_email(races):
    """Ensure all race image URLs are absolute and inject sport_code for email rendering."""
    for race in races:
        race.email_image_src = _make_absolute_url(race.image_src)
        race.sport_code = SPORT_CODES.get(race.sport, race.sport[:3].upper() if race.sport else '')
    return races


def _get_recommended_races(profile, limit=4):
    """Get recommended races based on user preferences, or popular upcoming races."""
    qs = Race.objects.upcoming()

    if profile.preferred_sports:
        sport_qs = qs.by_sport(profile.preferred_sports)
        if profile.preferred_regions:
            region_qs = sport_qs.by_region(profile.preferred_regions)
            if region_qs.exists():
                return list(region_qs[:limit])
        if sport_qs.count() >= limit:
            return list(sport_qs[:limit])
        # Pad with other upcoming races
        races = list(sport_qs[:limit])
        if len(races) < limit:
            exclude_ids = [r.id for r in races]
            extra = qs.exclude(id__in=exclude_ids)[:limit - len(races)]
            races.extend(extra)
        return races

    # Fallback: popular upcoming races
    return list(qs.order_by('-view_count')[:limit])


def _get_closing_soon_races(profile, limit=3):
    """Get races with registration closing soon, filtered by user preferences."""
    qs = Race.objects.closing_soon(days=7)

    if profile.preferred_sports:
        filtered = qs.by_sport(profile.preferred_sports)
        if filtered.exists():
            return list(filtered[:limit])

    return list(qs[:limit])


def send_welcome_email(profile):
    """Send personalized welcome email with race recommendations."""
    user = profile.user
    if not user.email:
        logger.warning('No email for user %s, skipping welcome email', user.id)
        return False

    if profile.welcome_email_sent:
        logger.info('Welcome email already sent for user %s', user.id)
        return False

    recommended_races = _prepare_races_for_email(_get_recommended_races(profile))
    closing_soon_races = _prepare_races_for_email(_get_closing_soon_races(profile))

    preferred_sport_labels = []
    if profile.preferred_sports:
        preferred_sport_labels = [
            SPORT_LABELS.get(s, s) for s in profile.preferred_sports
        ]

    context = {
        'nickname': profile.nickname or user.email.split('@')[0],
        'preferred_sports': profile.preferred_sports,
        'preferred_sport_labels': preferred_sport_labels,
        'preferred_regions': profile.preferred_regions or [],
        'recommended_races': recommended_races,
        'closing_soon_races': closing_soon_races,
        'app_url': APP_URL,
    }

    subject = f'[EnduroHub] {context["nickname"]}님, 환영합니다! 맞춤 대회 정보를 확인하세요'
    html_body = render_to_string('emails/welcome.html', context)
    text_body = _build_welcome_text(context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    message.attach_alternative(html_body, 'text/html')

    try:
        message.send(fail_silently=False)
    except Exception:
        logger.exception('Failed to send welcome email to %s', user.email)
        return False

    profile.welcome_email_sent = True
    profile.save(update_fields=['welcome_email_sent', 'updated_at'])
    logger.info('Welcome email sent to user %s (%s)', user.id, user.email)
    return True


def send_weekly_digest_email(profile):
    """Send weekly digest email with personalized race recommendations."""
    user = profile.user
    if not user.email:
        return False

    recommended_races = _prepare_races_for_email(_get_recommended_races(profile, limit=3))
    closing_soon_races = _prepare_races_for_email(_get_closing_soon_races(profile, limit=5))

    # New races added in the last 7 days
    week_ago = timezone.now() - timezone.timedelta(days=7)
    new_races_qs = Race.objects.upcoming().filter(created_at__gte=week_ago)
    if profile.preferred_sports:
        filtered_new = new_races_qs.by_sport(profile.preferred_sports)
        new_races = list(filtered_new[:5]) if filtered_new.exists() else list(new_races_qs[:5])
    else:
        new_races = list(new_races_qs[:5])
    new_races = _prepare_races_for_email(new_races)

    today = timezone.localdate()
    week_label = f'{today.month}.{today.day}'

    context = {
        'nickname': profile.nickname or user.email.split('@')[0],
        'week_label': week_label,
        'recommended_races': recommended_races,
        'closing_soon_races': closing_soon_races,
        'new_races': new_races,
        'new_races_count': len(new_races),
        'closing_soon_count': len(closing_soon_races),
        'has_preferences': bool(profile.preferred_sports),
        'app_url': APP_URL,
    }

    subject = f'[EnduroHub] {context["nickname"]}님의 주간 대회 소식'
    html_body = render_to_string('emails/weekly_digest.html', context)
    text_body = _build_digest_text(context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    message.attach_alternative(html_body, 'text/html')

    try:
        message.send(fail_silently=False)
    except Exception:
        logger.exception('Failed to send weekly digest to %s', user.email)
        return False

    return True


def send_new_races_alert(races):
    """Send new race alert to all opted-in users. Called hourly if new races exist."""
    from accounts.models import UserProfile

    races = _prepare_races_for_email(list(races))
    if not races:
        return 0

    profiles = UserProfile.objects.filter(
        email_verified=True,
        email_updates_opt_in=True,
    ).select_related('user')

    sent = 0
    for profile in profiles:
        user = profile.user
        if not user.email:
            continue

        # Filter races by user preferences if set
        if profile.preferred_sports:
            user_races = [r for r in races if r.sport in profile.preferred_sports]
            if not user_races:
                continue
        else:
            user_races = races

        nickname = profile.nickname or user.email.split('@')[0]

        match_parts = []
        if profile.preferred_sports:
            match_parts.append(
                '/'.join(SPORT_LABELS.get(s, s) for s in profile.preferred_sports)
            )
        if profile.preferred_regions:
            match_parts.append('/'.join(profile.preferred_regions))
        match_summary = ' · '.join(match_parts)

        context = {
            'nickname': nickname,
            'new_races': user_races,
            'race_count': len(user_races),
            'match_summary': match_summary,
            'app_url': APP_URL,
        }

        subject = f'[EnduroHub] 새 대회 {len(user_races)}건이 등록되었습니다'
        html_body = render_to_string('emails/new_races_alert.html', context)
        text_body = _build_new_races_text(context)

        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        message.attach_alternative(html_body, 'text/html')

        try:
            message.send(fail_silently=False)
            sent += 1
        except Exception:
            logger.exception('Failed to send new races alert to %s', user.email)

    return sent


def _build_new_races_text(ctx):
    lines = [
        f'{ctx["nickname"]}님, 새 대회 {ctx["race_count"]}건이 등록되었습니다.',
        '',
    ]
    for race in ctx['new_races']:
        lines.append(f'- {race.title}')
        lines.append(f'  {race.race_date} · {race.location}')
        lines.append(f'  {ctx["app_url"]}/races/{race.slug}')
        lines.append('')
    lines.extend([
        f'전체 대회 보기: {ctx["app_url"]}/races',
        '',
        '수신 거부: 마이페이지에서 이메일 수신 설정을 변경해주세요.',
    ])
    return '\n'.join(lines)


def _build_welcome_text(ctx):
    lines = [
        f'{ctx["nickname"]}님, EnduroHub에 오신 것을 환영합니다!',
        '',
    ]
    if ctx['recommended_races']:
        lines.append('추천 대회:')
        for race in ctx['recommended_races']:
            lines.append(
                f'- {race.title} ({race.race_date}, {race.location})'
            )
            lines.append(f'  {ctx["app_url"]}/races/{race.slug}')
    lines.extend([
        '',
        f'전체 대회 보기: {ctx["app_url"]}/races',
        '',
        '수신 거부: 마이페이지에서 이메일 수신 설정을 변경해주세요.',
    ])
    return '\n'.join(lines)


def _build_digest_text(ctx):
    lines = [
        f'{ctx["nickname"]}님의 주간 대회 소식 ({ctx["week_label"]})',
        '',
        f'신규 대회: {ctx["new_races_count"]}건 | 마감 임박: {ctx["closing_soon_count"]}건',
        '',
    ]
    if ctx['closing_soon_races']:
        lines.append('접수 마감 임박:')
        for race in ctx['closing_soon_races']:
            lines.append(f'- {race.title} (마감 {race.registration_end})')
    if ctx['recommended_races']:
        lines.extend(['', '추천 대회:'])
        for race in ctx['recommended_races']:
            lines.append(f'- {race.title} ({race.race_date})')
    lines.extend([
        '',
        f'전체 대회 보기: {ctx["app_url"]}/races',
        '',
        '수신 거부: 마이페이지에서 이메일 수신 설정을 변경해주세요.',
    ])
    return '\n'.join(lines)
