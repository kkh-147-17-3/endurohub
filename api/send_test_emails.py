"""One-shot script: send all 5 redesigned email templates to a test address.

Builds mock race objects (no DB hits) and dispatches via the configured SMTP backend.
Run: venv\\Scripts\\python.exe send_test_emails.py kterry0002@gmail.com
"""
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / '.env')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.core.mail import EmailMultiAlternatives, send_mail  # noqa: E402
from django.template.loader import render_to_string  # noqa: E402

from races.constants import SPORT_CODES, SPORT_LABELS  # noqa: E402

TO = sys.argv[1] if len(sys.argv) > 1 else 'kterry0002@gmail.com'
APP_URL = getattr(settings, 'APP_URL', 'https://www.endurohub.kr')


def mk_race(*, title, sport, region, location, race_date_, slug,
            registration_end_=None, distances=None, image=None, race_end=None):
    days_left = None
    if registration_end_:
        days_left = (registration_end_ - date.today()).days
    return SimpleNamespace(
        title=title,
        sport=sport,
        sport_label=SPORT_LABELS.get(sport, sport),
        sport_code=SPORT_CODES.get(sport, sport[:3].upper()),
        region=region,
        location=location,
        race_date=race_date_,
        race_end_date=race_end,
        registration_end=registration_end_,
        days_until_registration_end=days_left,
        is_registration_open=days_left is not None and days_left >= 0,
        slug=slug,
        distances=distances or [],
        email_image_src=image,
        official_url=None,
    )


today = date.today()

SAMPLE_RACES = [
    mk_race(
        title='서울국제마라톤 겸 동아마라톤',
        sport='running', region='서울', location='광화문 → 잠실종합운동장',
        race_date_=today + timedelta(days=42),
        registration_end_=today + timedelta(days=14),
        distances=[{'name': '풀코스'}, {'name': '10km'}],
        slug='seoul-international-marathon',
    ),
    mk_race(
        title='제주 그란폰도 200',
        sport='cycling', region='제주', location='제주시 일주도로',
        race_date_=today + timedelta(days=21),
        registration_end_=today + timedelta(days=3),
        distances=[{'name': '200km'}, {'name': '100km'}, {'name': '50km'}],
        slug='jeju-granfondo-200',
    ),
    mk_race(
        title='강원 평창 트레일런 챌린지',
        sport='trail_running', region='강원', location='평창 알펜시아 일대',
        race_date_=today + timedelta(days=58),
        registration_end_=today + timedelta(days=30),
        distances=[{'name': '50km'}, {'name': '21km'}],
        slug='pyeongchang-trail-challenge',
    ),
    mk_race(
        title='부산 오픈워터 스위밍 페스티벌',
        sport='swimming', region='부산', location='해운대 해수욕장',
        race_date_=today + timedelta(days=70),
        registration_end_=today + timedelta(days=45),
        distances=[{'name': '3km'}, {'name': '1.5km'}],
        slug='busan-open-water-2026',
    ),
    mk_race(
        title='고성 통일 철인3종 대회',
        sport='triathlon', region='강원', location='고성 송지호',
        race_date_=today + timedelta(days=90),
        registration_end_=today + timedelta(days=60),
        distances=[{'name': '올림픽'}, {'name': '스프린트'}],
        slug='goseong-triathlon-2026',
    ),
]

CLOSING_SOON = [
    mk_race(
        title='춘천 마라톤',
        sport='running', region='강원', location='춘천 의암호반',
        race_date_=today + timedelta(days=10),
        registration_end_=today + timedelta(days=2),
        distances=[{'name': '풀코스'}, {'name': '하프'}],
        slug='chuncheon-marathon',
    ),
    mk_race(
        title='남산 야간 러닝',
        sport='running', region='서울', location='남산공원',
        race_date_=today + timedelta(days=7),
        registration_end_=today,
        distances=[{'name': '10km'}],
        slug='namsan-night-run',
    ),
    mk_race(
        title='가평 자라섬 사이클',
        sport='cycling', region='경기', location='가평 자라섬',
        race_date_=today + timedelta(days=14),
        registration_end_=today + timedelta(days=5),
        distances=[{'name': '80km'}],
        slug='gapyeong-cycling',
    ),
]


def send_html(subject, template, context, text_body):
    html = render_to_string(template, context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[TO],
    )
    msg.attach_alternative(html, 'text/html')
    msg.send(fail_silently=False)
    print(f'  ✓ sent {subject}')


def send_welcome():
    print('1) welcome')
    ctx = {
        'nickname': '테리',
        'preferred_sport_labels': ['마라톤', '트레일러닝'],
        'preferred_regions': ['서울', '강원'],
        'recommended_races': SAMPLE_RACES[:4],
        'closing_soon_races': CLOSING_SOON,
        'app_url': APP_URL,
    }
    send_html(
        '[EnduroHub TEST] 환영합니다 — Arena 스타일 샘플',
        'emails/welcome.html',
        ctx,
        '환영합니다 (HTML 미지원 클라이언트용 텍스트)',
    )


def send_weekly():
    print('2) weekly_digest')
    ctx = {
        'nickname': '테리',
        'week_label': f'{today.month}월 {today.day}일',
        'recommended_races': SAMPLE_RACES[:3],
        'closing_soon_races': CLOSING_SOON,
        'new_races': SAMPLE_RACES,
        'new_races_count': len(SAMPLE_RACES),
        'closing_soon_count': len(CLOSING_SOON),
        'has_preferences': True,
        'app_url': APP_URL,
    }
    send_html(
        '[EnduroHub TEST] 주간 다이제스트 — Arena 스타일 샘플',
        'emails/weekly_digest.html',
        ctx,
        '주간 다이제스트',
    )


def send_new_alert():
    print('3) new_races_alert')
    ctx = {
        'nickname': '테리',
        'new_races': SAMPLE_RACES,
        'race_count': len(SAMPLE_RACES),
        'app_url': APP_URL,
    }
    send_html(
        '[EnduroHub TEST] 새 대회 5건 등록 — Arena 스타일 샘플',
        'emails/new_races_alert.html',
        ctx,
        '새 대회가 등록되었습니다',
    )


def send_crawl():
    print('4) crawl_report')
    created = SAMPLE_RACES[:3]
    updated_items = [
        {
            'race': SAMPLE_RACES[3],
            'applied_changes': [
                {'field_name': 'race_date', 'field_label': '대회일', 'old_value': '2026.07.04', 'new_value': '2026.07.05'},
                {'field_name': 'location', 'field_label': '장소', 'old_value': '해운대', 'new_value': '해운대 해수욕장'},
            ],
            'pending_changes': [],
        },
        {
            'race': SAMPLE_RACES[4],
            'applied_changes': [],
            'pending_changes': [
                {'field_name': 'entry_fee', 'field_label': '참가비', 'old_value': '70000', 'new_value': '85000'},
            ],
        },
    ]
    ctx = {
        'result': {
            'total': 12,
            'created': len(created),
            'updated': len(updated_items),
            'skipped': 7,
            'createdRaces': created,
        },
        'crawl_type': 'detailed',
        'updated_items': updated_items,
    }
    send_html(
        '[EnduroHub TEST] 크롤링 리포트 — Arena 스타일 샘플',
        'emails/crawl_report.html',
        ctx,
        '크롤링 리포트',
    )


def send_verify():
    print('5) verification_code')
    html = render_to_string('emails/verification_code.html', {'code': '584092'})
    send_mail(
        subject='[EnduroHub TEST] 이메일 인증 코드 — Arena 스타일 샘플',
        message='인증 코드: 584092 (10분 유효)',
        html_message=html,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[TO],
        fail_silently=False,
    )
    print(f'  ✓ sent verification code')


if __name__ == '__main__':
    print(f'Sending 5 sample emails to: {TO}')
    print(f'From: {settings.DEFAULT_FROM_EMAIL}')
    print(f'SMTP: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}\n')
    send_welcome()
    send_weekly()
    send_new_alert()
    send_crawl()
    send_verify()
    print('\nDone.')
