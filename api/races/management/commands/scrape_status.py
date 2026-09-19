from typing import Any

from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = '스크래핑 상태 확인'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--pending', action='store_true',
            help='검토 대기 중인 것만',
        )
        parser.add_argument(
            '--applied', action='store_true',
            help='적용 완료된 것만',
        )

    def handle(self, *args: Any, **options: Any) -> str | None:
        # TODO: Implement scrape status check
        self.stdout.write(self.style.ERROR(
            'Not yet implemented. Migrate ScrapeStatus logic from Laravel.'
        ))
        return None
