from django.core.management.base import BaseCommand
from django.utils import timezone

from races.models import Race


class Command(BaseCommand):
    help = 'Generate blog post for currently open registration races'

    def add_arguments(self, parser):
        parser.add_argument('year', nargs='?', type=int)
        parser.add_argument('month', nargs='?', type=int)
        parser.add_argument('--sport', type=str, default=None)
        parser.add_argument('--region', type=str, default=None)
        parser.add_argument('--format', type=str, default='html', choices=['html', 'markdown'])
        parser.add_argument('--tweet', action='store_true')
        parser.add_argument('--image', action='store_true')
        parser.add_argument('--instagram', action='store_true')
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--output', type=str, default=None)

    def handle(self, *args, **options):
        now = timezone.now().date()
        year = options.get('year')
        month = options.get('month')

        qs = Race.objects.filter(
            registration_start__lte=now,
            registration_end__gte=now,
        )

        if year and month:
            qs = qs.filter(race_date__year=year, race_date__month=month)
        elif year or month:
            self.stderr.write('year and month must be provided together')
            return

        if options['sport']:
            qs = qs.filter(sport=options['sport'])
        if options['region']:
            qs = qs.filter(region=options['region'])

        qs = qs.order_by('race_date')
        races = list(qs)

        if not races:
            self.stdout.write('No open registration races found.')
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

        self.stdout.write(f'\nOpen registration races: {len(races)}')
        self.stdout.write('-' * 40)
        for sport in sport_order:
            if sport in grouped:
                label = sport_labels.get(sport, sport)
                self.stdout.write(f'  {label}: {len(grouped[sport])}개')

        if options['dry_run']:
            self.stdout.write('\n[Dry run] No files generated.')
            return

        # Image generation
        if options['image'] or options['instagram']:
            try:
                from races.services.gemini_image import GeminiImageService
                service = GeminiImageService()
                sports_in_data = [s for s in sport_order if s in grouped]
                y = year or now.year
                m = month or now.month

                if options['image']:
                    path = service.generate_blog_image(y, m, sports_in_data, 'open')
                    if path:
                        self.stdout.write(f'Featured image: {path}')

                if options['instagram']:
                    path = service.generate_instagram_image(y, m, sports_in_data, 'open')
                    if path:
                        self.stdout.write(f'Instagram image: {path}')
            except Exception as e:
                self.stderr.write(f'Image generation failed: {e}')

        self.stdout.write(self.style.SUCCESS('Done.'))
