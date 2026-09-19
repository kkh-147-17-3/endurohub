from typing import Any

from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = 'Generate default OG images for each sport and year'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--years', action='store_true',
            help='Generate yearly OG images',
        )

    def handle(self, *args: Any, **options: Any) -> str | None:
        # TODO: Implement OG image generation using Pillow
        self.stdout.write(self.style.ERROR(
            'Not yet implemented. Migrate OG image generation from Laravel (uses GD/Pillow).'
        ))
        return None
