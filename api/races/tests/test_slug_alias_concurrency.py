"""Exercise URL ownership on the production database engine, not SQLite locks."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier, Event
from unittest import skipUnless

from django.core.exceptions import ValidationError
from django.db import IntegrityError, close_old_connections, connection, connections, transaction
from django.test import TransactionTestCase

from races.models import Race, RaceAlias
from races.resolution import resolve_race


@skipUnless(connection.vendor == 'postgresql', 'Requires PostgreSQL transactional locks.')
class RaceSlugConcurrencyTests(TransactionTestCase):
    def make_race(self, slug: str) -> Race:
        return Race.objects.create(
            title=slug, slug=slug, sport='running', race_date=date(2026, 11, 21),
            location='서울', region='서울',
        )

    def test_old_url_cannot_be_claimed_while_its_owner_renames_it(self) -> None:
        original = self.make_race('concurrent-original')
        reserved, release, contender_started = Event(), Event(), Event()

        def rename() -> None:
            close_old_connections()
            try:
                with transaction.atomic():
                    race = Race.objects.get(pk=original.pk)
                    race.slug = 'concurrent-new'
                    race.save(update_fields=['slug'])
                    reserved.set()
                    if not release.wait(10):
                        raise TimeoutError('Timed out releasing the rename transaction.')
            finally:
                connections['default'].close()

        def claim() -> str:
            close_old_connections()
            try:
                contender_started.set()
                self.make_race('concurrent-original')
                return 'claimed'
            except (ValidationError, IntegrityError):
                return 'rejected'
            finally:
                connections['default'].close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            renamed = pool.submit(rename)
            try:
                self.assertTrue(reserved.wait(10))
                claimed = pool.submit(claim)
                self.assertTrue(contender_started.wait(10))
            finally:
                release.set()
            renamed.result(timeout=15)
            self.assertEqual(claimed.result(timeout=15), 'rejected')

        self.assertEqual(resolve_race('concurrent-original').pk, original.pk)
        self.assertEqual(resolve_race('concurrent-new').pk, original.pk)
        self.assertEqual(Race.objects.count(), 1)

    def test_two_races_cannot_take_the_same_new_url_and_keep_both_old_urls(self) -> None:
        first = self.make_race('concurrent-a')
        second = self.make_race('concurrent-b')
        start = Barrier(2)

        def rename(race_id: int) -> str:
            close_old_connections()
            try:
                race = Race.objects.get(pk=race_id)
                race.slug = 'concurrent-shared'
                start.wait(timeout=10)
                race.save(update_fields=['slug'])
                return 'renamed'
            except (ValidationError, IntegrityError):
                return 'rejected'
            finally:
                connections['default'].close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [pool.submit(rename, race.pk) for race in (first, second)]
            self.assertCountEqual([future.result(timeout=15) for future in results], ['renamed', 'rejected'])

        self.assertEqual(resolve_race('concurrent-a').pk, first.pk)
        self.assertEqual(resolve_race('concurrent-b').pk, second.pk)
        self.assertIn(resolve_race('concurrent-shared').pk, (first.pk, second.pk))
        self.assertEqual(Race.objects.count(), 2)
        self.assertEqual(RaceAlias.objects.count(), 1)
