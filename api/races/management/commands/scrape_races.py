from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '대회 공식 사이트에서 이미지/정보 스크래핑'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all', action='store_true',
            help='모든 대회 스크래핑',
        )
        parser.add_argument(
            '--id', type=int, default=None,
            help='특정 대회 ID',
        )
        parser.add_argument(
            '--pending', action='store_true',
            help='아직 스크래핑 안된 대회만',
        )
        parser.add_argument(
            '--screenshot', action='store_true',
            help='스크린샷 저장',
        )

    def handle(self, *args, **options):
        from races.models import Race

        if options['id']:
            races = Race.objects.filter(id=options['id'])
        elif options['pending']:
            races = Race.objects.filter(
                official_url__isnull=False,
            ).exclude(
                official_url='',
            ).filter(
                image_url__isnull=True,
            ).order_by('race_date')
        elif options['all']:
            races = Race.objects.filter(
                official_url__isnull=False,
            ).exclude(
                official_url='',
            ).order_by('race_date')
        else:
            races = Race.objects.filter(
                official_url__isnull=False,
            ).exclude(
                official_url='',
            ).order_by('race_date')[:10]

        if not races.exists():
            self.stdout.write(self.style.WARNING('스크래핑할 대회가 없습니다.'))
            return

        self.stdout.write(f'총 {races.count()}개 대회를 스크래핑합니다.')

        # TODO: Implement scraping logic (Node.js script call)
        self.stdout.write(self.style.ERROR(
            'Not yet implemented. Migrate scrape-race.mjs from Laravel.'
        ))
