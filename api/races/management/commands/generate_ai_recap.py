"""끝난 대회의 후기 요약 생성 (웹 검색 기반).

    python manage.py generate_ai_recap --slug 2025-경포마라톤 --dry-run   # 표본 확인
    python manage.py generate_ai_recap --limit 5 --dry-run                # 대상 5건 미리보기
    python manage.py generate_ai_recap --limit 20                         # 20건 채우기

ai_summary 가 비어 있는 대회만 대상으로 한다. 기존 요약을 덮어쓰는 옵션은 없다 —
관리자가 손댄 요약이 조용히 사라지는 게 이 잡의 가장 나쁜 실패라서다.
"""

from django.core.management.base import BaseCommand

from races.services.ai_recap import FINISHED_DAYS, generate_race_recaps


class Command(BaseCommand):
    help = '끝난 대회의 참가 후기를 웹에서 찾아 ai_summary 를 채운다'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=None, help='처리할 최대 건수')
        parser.add_argument('--dry-run', action='store_true', help='저장하지 않고 결과만 출력')
        parser.add_argument('--slug', type=str, default='', help='특정 대회만 처리')
        parser.add_argument(
            '--days', type=int, default=FINISHED_DAYS,
            help=f'대회 종료 후 며칠 지난 것부터 대상으로 삼을지 (기본 {FINISHED_DAYS})',
        )
        parser.add_argument(
            '--sleep', type=float, default=1.0,
            help='호출 간 대기(초). 레이트리밋 회피용',
        )

    def handle(self, *args, **options):
        if options['dry_run']:
            self.stdout.write('dry-run — 저장하지 않음')

        def report(race, text, reason):
            if text:
                self.stdout.write(f'  OK    {race.slug}')
                self.stdout.write('        ' + text.replace('\n', '\n        '))
            else:
                self.stdout.write(f'  SKIP  {race.slug}  ({reason})')

        summary = generate_race_recaps(
            dry_run=options['dry_run'],
            limit=options['limit'],
            days=options['days'],
            slug=options['slug'] or None,
            sleep=options['sleep'],
            on_result=report,
        )
        self.stdout.write(self.style.SUCCESS(
            f"완료 — 대상 {summary['total']}건 / 생성 {summary['generated']}건 / "
            f"후기없음 {summary['no_material']}건 / 근거기각 {summary['rejected']}건 / "
            f"오류 {summary['errors']}건 / 최근시도 제외 {summary['skipped_tried']}건 / "
            f"기존요약 보존 {summary['skipped_existing']}건"
        ))
