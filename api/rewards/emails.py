import logging
import mimetypes
import os

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_winner_email(winner):
    coupon = winner.coupon
    campaign = winner.campaign
    user = winner.user
    profile = getattr(user, 'profile', None) if user else None
    nickname = (
        getattr(profile, 'nickname', '')
        or winner.email.split('@')[0]
    )
    app_url = getattr(settings, 'APP_URL', 'https://www.endurohub.kr')
    context = {
        'app_url': app_url,
        'campaign': campaign,
        'coupon': coupon,
        'nickname': nickname,
    }
    subject = f'[EnduroHub] {campaign.name} 당첨을 축하드립니다'
    text_body = _build_winner_text(context)
    html_body = render_to_string('emails/reward_winner.html', context)
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[winner.email],
    )
    message.attach_alternative(html_body, 'text/html')

    if coupon.image:
        filename = os.path.basename(coupon.image.name)
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        with coupon.image.open('rb') as image_file:
            message.attach(filename, image_file.read(), mime_type)

    message.send(fail_silently=False)
    logger.info('Reward email sent for winner_id=%s', winner.pk)


def _build_winner_text(context):
    campaign = context['campaign']
    coupon = context['coupon']
    lines = [
        f'{context["nickname"]}님, 축하드립니다!',
        f'{campaign.name}에 당첨되어 {campaign.prize_name}을 보내드립니다.',
        '',
    ]
    if coupon.code:
        lines.append(f'쿠폰 코드: {coupon.code}')
    if coupon.redemption_url:
        lines.append(f'쿠폰 확인: {coupon.redemption_url}')
    if coupon.image:
        lines.append('기프티콘 이미지는 이 메일에 첨부되어 있습니다.')
    if coupon.expires_on:
        lines.append(f'사용 기한: {coupon.expires_on:%Y.%m.%d}')
    lines.extend([
        '',
        '이 메일은 리뷰 이벤트 당첨 및 경품 전달을 위해 발송되었습니다.',
        f'문의: {context["app_url"]}/help',
    ])
    return '\n'.join(lines)
