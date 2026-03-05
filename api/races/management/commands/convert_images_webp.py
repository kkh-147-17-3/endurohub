import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from races.image_utils import process_image
from races.models import Race


class Command(BaseCommand):
    help = 'Convert existing race images to WebP and generate thumbnails.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would be converted without actually doing it.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        media_root = Path(settings.MEDIA_ROOT)

        # Collect all image paths from races
        image_paths = set()

        for race in Race.objects.only(
            'id', 'image_path', 'course_image_uploads', 'giveaway_image_uploads'
        ).iterator():
            if race.image_path:
                image_paths.add(race.image_path)
            for uploads_field in [race.course_image_uploads, race.giveaway_image_uploads]:
                if uploads_field and isinstance(uploads_field, list):
                    image_paths.update(uploads_field)

        # Filter to existing non-webp files that don't already have a webp counterpart
        to_convert = []
        for rel_path in sorted(image_paths):
            abs_path = media_root / rel_path
            if not abs_path.exists():
                continue
            if abs_path.suffix.lower() == '.webp':
                continue
            webp_path = abs_path.with_suffix('.webp')
            thumb_path = abs_path.parent / 'thumbs' / f'{abs_path.stem}.webp'
            if webp_path.exists() and thumb_path.exists():
                continue
            to_convert.append(rel_path)

        self.stdout.write(f'Found {len(to_convert)} images to convert.')

        if dry_run:
            for p in to_convert:
                self.stdout.write(f'  Would convert: {p}')
            return

        converted = 0
        failed = 0
        for rel_path in to_convert:
            result = process_image(rel_path)
            if result:
                converted += 1
                self.stdout.write(f'  Converted: {rel_path}')
            else:
                failed += 1
                self.stderr.write(f'  Failed: {rel_path}')

        self.stdout.write(self.style.SUCCESS(
            f'Done. Converted: {converted}, Failed: {failed}, Skipped: {len(image_paths) - len(to_convert)}'
        ))
