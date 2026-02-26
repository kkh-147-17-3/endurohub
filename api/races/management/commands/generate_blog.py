from django.core.management.base import BaseCommand

from races.models import Race


class Command(BaseCommand):
    help = '월별 대회 정보를 네이버 블로그 포스트 HTML로 생성합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            'year', type=int,
            help='대상 연도 (예: 2026)',
        )
        parser.add_argument(
            'month', type=int,
            help='대상 월 (예: 2)',
        )
        parser.add_argument(
            '--sport', type=str, default=None,
            help='특정 종목만 (running, triathlon 등)',
        )
        parser.add_argument(
            '--region', type=str, default=None,
            help='특정 지역만',
        )
        parser.add_argument(
            '--format', type=str, default='html', choices=['html', 'markdown'],
            help='출력 형식 (html 또는 markdown)',
        )
        parser.add_argument(
            '--tweet', action='store_true',
            help='트윗용 요약 텍스트 생성',
        )
        parser.add_argument(
            '--image', action='store_true',
            help='블로그 대표 이미지 생성 (16:9)',
        )
        parser.add_argument(
            '--instagram', action='store_true',
            help='인스타그램 이미지 생성 (1:1)',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='미리보기 (파일 저장 안함)',
        )
        parser.add_argument(
            '--output', type=str, default=None,
            help='출력 파일 경로',
        )

    def handle(self, *args, **options):
        year = options['year']
        month = options['month']

        self.stdout.write('블로그 포스트 생성을 시작합니다...')
        self.stdout.write(f'대상: {year}년 {month}월')

        qs = Race.objects.filter(
            race_date__year=year,
            race_date__month=month,
        )

        if options['sport']:
            qs = qs.filter(sport=options['sport'])
            self.stdout.write(f'종목 필터: {options["sport"]}')

        if options['region']:
            qs = qs.filter(region=options['region'])
            self.stdout.write(f'지역 필터: {options["region"]}')

        qs = qs.order_by('race_date')
        races = list(qs)

        if not races:
            self.stdout.write('해당 조건의 대회가 없습니다.')
            return

        # Group by sport
        sport_order = ['running', 'trail_running', 'triathlon', 'cycling', 'swimming']
        sport_labels = {
            'running': '마라톤', 'trail_running': '트레일러닝',
            'triathlon': '철인3종', 'cycling': '자전거', 'swimming': '수영',
        }
        grouped = {}
        for race in races:
            grouped.setdefault(race.sport, []).append(race)

        self.stdout.write(f'\n{year}년 {month}월 대회: {len(races)}개')
        self.stdout.write('-' * 40)
        for sport in sport_order:
            if sport in grouped:
                label = sport_labels.get(sport, sport)
                self.stdout.write(f'  {label}: {len(grouped[sport])}개')

        if options['dry_run']:
            self.stdout.write(self.style.WARNING(
                '\n--dry-run 모드: 파일을 저장하지 않습니다.'
            ))
            return

        # Image generation
        if options['image'] or options['instagram']:
            try:
                from races.services.gemini_image import GeminiImageService
                service = GeminiImageService()
                sports_in_data = [s for s in sport_order if s in grouped]

                if options['image']:
                    path = service.generate_blog_image(year, month, sports_in_data, 'monthly')
                    if path:
                        self.stdout.write(f'대표 이미지: {path}')

                if options['instagram']:
                    path = service.generate_instagram_image(year, month, sports_in_data, 'monthly')
                    if path:
                        self.stdout.write(f'인스타그램 이미지: {path}')
            except Exception as e:
                self.stderr.write(f'이미지 생성 실패: {e}')

        # TODO: Implement blog post HTML/Markdown generation service
        self.stdout.write(self.style.WARNING(
            'Blog post content generation not yet implemented. '
            'Migrate BlogPostGeneratorService from Laravel.'
        ))

        self.stdout.write(self.style.SUCCESS('완료.'))
