import re

from django.core.management.base import BaseCommand

from races.models import Race


# 우선순위 순서대로 시도. 가장 구체적인 패턴 먼저.
EDITION_PATTERNS = [
    # 한국어: '제5회', '제 5 회', '제5차'
    (re.compile(r'제\s*(\d+)\s*회'), lambda m: f'제{m.group(1)}회'),
    (re.compile(r'제\s*(\d+)\s*차'), lambda m: f'제{m.group(1)}차'),
    # 영어: '5th', '23rd', '1st'
    (re.compile(r'\b(\d+)(st|nd|rd|th)\b', re.IGNORECASE),
     lambda m: f'{m.group(1)}{m.group(2).lower()}'),
]


def extract_edition(title: str) -> str | None:
    if not title:
        return None
    for pattern, formatter in EDITION_PATTERNS:
        m = pattern.search(title)
        if m:
            return formatter(m)
    return None


class Command(BaseCommand):
    help = "기존 대회 title에서 '제N회' 패턴을 추출해 edition 필드에 채웁니다"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='저장하지 않고 매칭 결과만 출력',
        )
        parser.add_argument(
            '--overwrite', action='store_true',
            help='이미 edition 값이 있어도 덮어씀 (기본: 비어있는 것만)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        overwrite = options['overwrite']

        qs = Race.objects.all()
        if not overwrite:
            from django.db.models import Q
            qs = qs.filter(Q(edition__isnull=True) | Q(edition=''))

        total = qs.count()
        self.stdout.write(f'대상: {total}개 대회 (overwrite={overwrite})')
        if dry_run:
            self.stdout.write(self.style.WARNING('--dry-run 모드'))

        matched = 0
        skipped = 0
        for race in qs.iterator(chunk_size=200):
            edition = extract_edition(race.title)
            if not edition:
                skipped += 1
                continue
            self.stdout.write(f'  [매칭] {edition:>10} ← {race.title}')
            matched += 1
            if not dry_run:
                race.edition = edition
                race.save(update_fields=['edition', 'updated_at'])

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'완료: 매칭 {matched} / 미매칭 {skipped} / 전체 {total}'
        ))
