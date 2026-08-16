"""대회 요약(ai_summary) 일괄 생성.

    python manage.py generate_ai_summary --limit 3 --dry-run   # 표본 확인
    python manage.py generate_ai_summary --limit 50            # 50건 채우기
    python manage.py generate_ai_summary --slug 2026-경포마라톤 --force

기본값은 요약이 비어 있는 대회만 대상으로 한다. 이미 있는 것을 다시 만들려면 --force.
"""

import time

from django.core.management.base import BaseCommand
from django.db.models import Q

from races.models import Race
from races.services.ai_summary import generate_summary


class Command(BaseCommand):
    help = '대회 요약(ai_summary)을 LLM 으로 생성한다'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0, help='처리할 최대 건수 (0=전체)')
        parser.add_argument('--dry-run', action='store_true', help='저장하지 않고 결과만 출력')
        parser.add_argument('--force', action='store_true', help='이미 요약이 있어도 다시 생성')
        parser.add_argument('--slug', type=str, default='', help='특정 대회만 처리')
        parser.add_argument(
            '--sleep', type=float, default=0.5,
            help='호출 간 대기(초). 레이트리밋 회피용',
        )

    def handle(self, *args, **options):
        qs = Race.objects.all().order_by('-race_date')
        if options['slug']:
            qs = qs.filter(slug=options['slug'])
        elif not options['force']:
            qs = qs.filter(Q(ai_summary__isnull=True) | Q(ai_summary=''))

        total = qs.count()
        if options['limit']:
            qs = qs[: options['limit']]

        targets = list(qs)
        self.stdout.write(
            f'대상 {len(targets)}건 (조건에 맞는 전체 {total}건)'
            + (' — dry-run, 저장하지 않음' if options['dry_run'] else '')
        )

        done = skipped = 0
        for i, race in enumerate(targets, 1):
            summary = generate_summary(race)
            if not summary:
                # 정보가 너무 적어 건너뛴 경우와 호출 실패가 둘 다 None 이라 하나로 센다.
                # 실패는 서비스 쪽에서 warning 로그로 남는다.
                skipped += 1
                self.stdout.write(f'  [{i}/{len(targets)}] SKIP  {race.slug}')
            else:
                if not options['dry_run']:
                    race.ai_summary = summary
                    race.save(update_fields=['ai_summary', 'updated_at'])
                done += 1
                self.stdout.write(f'  [{i}/{len(targets)}] OK    {race.slug}')
                self.stdout.write(f'        {summary}'.replace('\n', '\n        '))

            if options['sleep'] and i < len(targets):
                time.sleep(options['sleep'])

        self.stdout.write(
            self.style.SUCCESS(f'완료 — 생성 {done}건 / 건너뜀·실패 {skipped}건')
        )
