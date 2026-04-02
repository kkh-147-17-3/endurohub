from django.core.management.base import BaseCommand

from races.services import MarathonCrawlerService


class Command(BaseCommand):
    help = 'Roadrun 마라톤 대회 정보를 크롤링합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year', type=int, default=None,
            help='크롤링할 연도 (기본: 현재 연도)',
        )
        parser.add_argument(
            '--month', type=int, default=None,
            help='크롤링할 월 (선택)',
        )
        parser.add_argument(
            '--with-details', action='store_true',
            help='각 대회의 상세 정보도 크롤링',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='데이터베이스에 저장하지 않고 결과만 출력',
        )

    def handle(self, *args, **options):
        from django.utils import timezone

        year = options['year'] or timezone.now().year
        month = options['month']
        with_details = options['with_details']
        dry_run = options['dry_run']
        service = MarathonCrawlerService()

        self.stdout.write('마라톤 대회 정보 크롤링을 시작합니다...')
        month_str = f'{month}월' if month else '전체'
        self.stdout.write(f'대상: {year}년 {month_str}')

        if with_details:
            self.stdout.write('상세 정보 크롤링 모드 (시간이 더 소요됩니다)')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '--dry-run 모드: 데이터베이스에 저장하지 않습니다.'
            ))

        crawl_func = service.crawl_with_details if with_details else service.crawl
        result = crawl_func(year=year, month=month, dry_run=dry_run)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('크롤링이 완료되었습니다.'))
        self.stdout.write(f"전체: {result.get('total', 0)}")
        self.stdout.write(f"신규: {result.get('created', 0)}")
        self.stdout.write(f"업데이트: {result.get('updated', 0)}")
        self.stdout.write(f"스킵: {result.get('skipped', 0)}")

        if dry_run:
            races = result.get('races', [])
            preview_count = min(len(races), 10)
            if preview_count:
                self.stdout.write('')
                self.stdout.write(f'미리보기 ({preview_count}건):')
                for race in races[:preview_count]:
                    self.stdout.write(
                        f"- {race.get('race_date')} | {race.get('region')} | {race.get('title')}"
                    )
