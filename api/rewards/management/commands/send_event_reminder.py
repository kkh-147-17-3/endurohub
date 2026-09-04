import time
from datetime import date

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string

from accounts.models import UserProfile


SUBJECT = '[ENDURO/HUB] 9월 30일 마감 — 완주 기록 남기고 커피 받으세요'
CONFIRMATION = 'SEND-COFFEE-EVENT-2026'
EVENT_END = date(2026, 9, 30)


def mask_email(email):
    local, separator, domain = email.rpartition('@')
    if not separator:
        return '***'
    return f'{local[:2]}***@{domain}'


def build_message(*, to, test=False, connection=None):
    subject = f'[TEST] {SUBJECT}' if test else SUBJECT
    context = {'app_url': 'https://www.endurohub.kr'}
    text_body = render_to_string('emails/coffee_coupon_event.txt', context).strip()
    html_body = render_to_string('emails/coffee_coupon_event.html', context)
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
        connection=connection,
    )
    message.attach_alternative(html_body, 'text/html')
    return message


class Command(BaseCommand):
    help = '2026 커피 쿠폰 이벤트 독려 메일을 테스트 주소 또는 수신 동의 회원에게 발송합니다.'

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument('--to', help='테스트 메일을 받을 단일 이메일 주소')
        mode.add_argument('--send-all', action='store_true', help='수신 동의 회원 전체에게 발송')
        parser.add_argument(
            '--confirm',
            help=f'전체 발송 안전 확인 문자열: {CONFIRMATION}',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.15,
            help='전체 발송 시 메일 사이의 대기 시간(초, 기본 0.15)',
        )

    def handle(self, *args, **options):
        if options['delay'] < 0:
            raise CommandError('--delay는 0 이상이어야 합니다.')

        if options['to']:
            message = build_message(to=options['to'], test=True)
            sent = message.send(fail_silently=False)
            if sent != 1:
                raise CommandError('SMTP 백엔드가 테스트 메일을 발송하지 못했습니다.')
            self.stdout.write(
                self.style.SUCCESS(
                    f'테스트 메일 발송 완료: {mask_email(options["to"])}'
                )
            )
            return

        if options['confirm'] != CONFIRMATION:
            raise CommandError(
                f'전체 발송에는 --confirm {CONFIRMATION} 옵션이 필요합니다.'
            )
        if date.today() > EVENT_END:
            raise CommandError('이벤트 마감일이 지나 전체 발송을 중단했습니다.')

        recipients = list(
            UserProfile.objects.filter(
                email_verified=True,
                email_updates_opt_in=True,
                user__email__gt='',
                user__is_active=True,
            )
            .values_list('user__email', flat=True)
            .distinct()
            .order_by('user__email')
        )
        if not recipients:
            raise CommandError('발송 가능한 수신 동의 회원이 없습니다.')

        sent = 0
        failures = []
        with get_connection(fail_silently=False) as connection:
            for email in recipients:
                try:
                    sent += build_message(to=email, connection=connection).send(
                        fail_silently=False
                    )
                except Exception as exc:
                    failures.append((email, str(exc)))
                    self.stderr.write(f'발송 실패: {email} ({exc})')
                if options['delay']:
                    time.sleep(options['delay'])

        self.stdout.write(f'전체 대상 {len(recipients)}명 / 성공 {sent}명 / 실패 {len(failures)}명')
        if failures:
            raise CommandError('일부 메일 발송에 실패했습니다. 위 실패 목록을 확인하세요.')
        self.stdout.write(self.style.SUCCESS('이벤트 독려 메일 전체 발송 완료'))
