from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Generate default OG images for each sport and year'

    def add_arguments(self, parser):
        parser.add_argument(
            '--years', action='store_true',
            help='Generate yearly OG images',
        )

    def handle(self, *args, **options):
        # TODO: Implement OG image generation using Pillow
        self.stdout.write(self.style.ERROR(
            'Not yet implemented. Migrate OG image generation from Laravel (uses GD/Pillow).'
        ))
