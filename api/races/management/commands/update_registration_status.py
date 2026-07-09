from django.core.management.base import BaseCommand

from races.services.reg_status import update_registration_status


class Command(BaseCommand):
    help = '마감 전 대회의 공식 페이지를 확인해 접수마감 상태를 갱신'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='판정만 하고 DB에는 반영하지 않음',
        )
        parser.add_argument(
            '--limit', type=int, default=None,
            help='확인할 대회 수 상한 (테스트용)',
        )

    def handle(self, *args, **options):
        summary = update_registration_status(dry_run=options['dry_run'], limit=options['limit'])
        self.stdout.write(self.style.SUCCESS(
            f"완료 — 대상 {summary['total']}건 / 판정 {summary['checked']}건 / "
            f"마감 반영 {summary['closed']}건 / 근거기각 {summary['rejected_evidence']}건 / "
            f"잠금 건너뜀 {summary['skipped_locked']}건 / 오류 {summary['errors']}건"
        ))
