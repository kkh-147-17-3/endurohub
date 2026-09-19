from typing import Any

from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = '스크래핑된 이미지를 자동으로 검토하고 선별'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--all', action='store_true',
            help='모든 pending 대회 자동 검토',
        )
        parser.add_argument(
            '--id', type=int, default=None,
            help='특정 대회 ID만',
        )
        parser.add_argument(
            '--apply', action='store_true',
            help='검토 후 바로 DB 적용',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='실제 저장하지 않고 미리보기만',
        )

    def handle(self, *args: Any, **options: Any) -> str | None:
        # TODO: Implement auto review logic
        self.stdout.write(self.style.ERROR(
            'Not yet implemented. Migrate AutoReviewImages logic from Laravel.'
        ))
        return None
