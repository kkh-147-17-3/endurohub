import json
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.core.serializers.json import DjangoJSONEncoder

from races.services.merge_races import MergeConflict, merge_races


class Command(BaseCommand):
    help = 'Preview an explicit duplicate-race merge; only --apply writes changes.'
    requires_migrations_checks = True

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--source', type=int, required=True, help='Duplicate race ID to merge away.')
        parser.add_argument('--target', type=int, required=True, help='Canonical race ID to retain.')
        parser.add_argument('--apply', action='store_true', help='Apply the reviewed merge atomically.')

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            result = merge_races(options['source'], options['target'], apply=options['apply'])
        except MergeConflict as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(result, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2))
        if not options['apply']:
            self.stdout.write('PREVIEW ONLY: no rows changed. Review the target and rerun with --apply.')
