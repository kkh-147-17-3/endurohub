from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '마라톤온라인(marathon.pe.kr)에서 마라톤 대회 정보를 크롤링합니다'

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

        self.stdout.write('마라톤 대회 정보 크롤링을 시작합니다...')
        month_str = f'{month}월' if month else '전체'
        self.stdout.write(f'대상: {year}년 {month_str}')

        if with_details:
            self.stdout.write('상세 정보 크롤링 모드 (시간이 더 소요됩니다)')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '--dry-run 모드: 데이터베이스에 저장하지 않습니다.'
            ))

        # TODO: Implement crawler service
        self.stdout.write(self.style.ERROR(
            'Not yet implemented. Migrate MarathonCrawlerService from Laravel.'
        ))
