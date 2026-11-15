from datetime import date
from typing import Any

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import RaceRecord
from races.models import Race, RaceAlias, RaceFavorite, Review
from races.resolution import resolve_race
from races.services.marathon_crawler import MarathonCrawlerService
from races.services.merge_races import merge_races, merged_source_race


class RaceSlugAliasTests(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.addCleanup(cache.clear)
        self.race = self.make_race(
            'original', source='crawl', source_url='https://example.org/original',
            external_id='feed-original', description='Original description',
        )

    def make_race(self, slug: str, **kwargs: Any) -> Race:
        return Race.objects.create(
            title=slug, slug=slug, sport='running', race_date=date(2026, 5, 10),
            location='서울', region='서울', distances=[{'name': '10km'}], **kwargs,
        )

    def reserve_alias(self, alias: str, owner: Race) -> RaceAlias:
        return RaceAlias.objects.create(
            alias=alias, race=owner, source_race_id=owner.pk, source_slug=alias,
        )

    def test_repeated_renames_preserve_every_url_on_the_same_race(self) -> None:
        race_id = self.race.pk
        self.race.slug = 'second'
        self.race.save()
        self.race.slug = 'third'
        self.race.save(update_fields=['slug', 'updated_at'])

        for identifier in ('original', 'second', 'third', str(race_id)):
            with self.subTest(identifier=identifier):
                self.assertEqual(resolve_race(identifier).pk, race_id)
        self.assertEqual(
            set(RaceAlias.objects.values_list('alias', 'race_id')),
            {('original', race_id), ('second', race_id)},
        )
        self.race.refresh_from_db()
        self.assertEqual(self.race.slug, 'third')

    def test_renamed_urls_follow_a_later_merge_without_losing_user_content(self) -> None:
        user = User.objects.create_user(username='slug-owner')
        review = Review.objects.create(
            race=self.race, user=user, rating=4, comment='Keep this review', ip_hash='slug-owner-ip',
        )
        favorite = RaceFavorite.objects.create(race=self.race, user=user)
        record = RaceRecord.objects.create(
            race=self.race, user=user, sport='running', distance='10km',
            course_code='10K', duration_seconds=3600, is_public=False,
        )
        source_id = self.race.pk
        review_created = review.created_at
        record_created = record.created_at
        self.race.slug = 'second'
        self.race.save()
        self.race.slug = 'third'
        self.race.save(update_fields=['slug'])
        target = self.make_race('final-target')

        merge_races(source_id, target.pk, apply=True)

        for identifier in ('original', 'second', 'third', str(source_id), target.slug):
            with self.subTest(identifier=identifier):
                self.assertEqual(resolve_race(identifier).pk, target.pk)
        self.assertFalse(Race.objects.filter(pk=source_id).exists())
        self.assertEqual(set(RaceAlias.objects.values_list('race_id', flat=True)), {target.pk})
        review.refresh_from_db()
        favorite.refresh_from_db()
        record.refresh_from_db()
        self.assertEqual(review.race_id, target.pk)
        self.assertEqual(review.comment, 'Keep this review')
        self.assertEqual(review.created_at, review_created)
        self.assertEqual(favorite.race_id, target.pk)
        self.assertEqual(record.race_id, target.pk)
        self.assertEqual(record.duration_seconds, 3600)
        self.assertFalse(record.is_public)
        self.assertEqual(record.created_at, record_created)
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(RaceFavorite.objects.count(), 1)
        self.assertEqual(RaceRecord.objects.count(), 1)

    def test_alias_owned_by_another_race_rejects_the_entire_edit(self) -> None:
        other = self.make_race('other')
        self.reserve_alias('reserved', other)
        self.race.slug = 'reserved'
        self.race.title = 'This title must not be saved'

        with self.assertRaises(ValidationError):
            self.race.save()

        self.race.refresh_from_db()
        self.assertEqual(self.race.slug, 'original')
        self.assertEqual(self.race.title, 'original')
        self.assertEqual(RaceAlias.objects.get(alias='reserved').race_id, other.pk)
        self.assertFalse(RaceAlias.objects.filter(alias='original').exists())
        with self.assertRaises(ValidationError):
            self.make_race('reserved')

    def test_conflicting_old_url_reservation_rolls_back_the_entire_rename(self) -> None:
        other = self.make_race('other')
        # Simulate inconsistent legacy data rather than bypass the guard under test.
        self.reserve_alias('original', other)
        self.race.slug = 'new-url'
        self.race.title = 'This title must not be saved'

        with self.assertRaises(ValidationError):
            self.race.save(update_fields=['slug', 'title'])

        self.race.refresh_from_db()
        self.assertEqual(self.race.slug, 'original')
        self.assertEqual(self.race.title, 'original')
        self.assertEqual(RaceAlias.objects.get(alias='original').race_id, other.pk)
        self.assertFalse(RaceAlias.objects.filter(alias='new-url').exists())

    def test_update_fields_without_slug_ignores_an_unsaved_slug_and_adds_no_aliases(self) -> None:
        other = self.make_race('other')
        self.reserve_alias('reserved', other)
        for dirty_slug in ('unsaved-url', 'reserved', '123'):
            with self.subTest(dirty_slug=dirty_slug):
                self.race.slug = dirty_slug
                self.race.title = f'Updated title for {dirty_slug}'
                self.race.save(update_fields=['title'])
                self.race.refresh_from_db()
                self.assertEqual(self.race.slug, 'original')
                self.assertEqual(self.race.title, f'Updated title for {dirty_slug}')
                self.assertEqual(list(RaceAlias.objects.values_list('alias', flat=True)), ['reserved'])

    def test_empty_update_fields_does_not_reserve_a_dirty_slug(self) -> None:
        self.race.slug = 'unsaved-url'
        self.race.save(update_fields=[])

        self.race.refresh_from_db()
        self.assertEqual(self.race.slug, 'original')
        self.assertFalse(RaceAlias.objects.exists())

    def test_direct_save_rejects_ascii_numeric_slugs_on_create_and_edit(self) -> None:
        other = self.make_race('other')
        for numeric_slug in (str(other.pk), '987654321', '00123'):
            with self.subTest(numeric_slug=numeric_slug):
                with self.assertRaises(ValidationError):
                    self.make_race(numeric_slug)
                self.race.slug = numeric_slug
                with self.assertRaises(ValidationError):
                    self.race.save(update_fields=['slug'])
                self.race.refresh_from_db()
                self.assertEqual(self.race.slug, 'original')
        self.assertFalse(RaceAlias.objects.exists())

    @override_settings(ADMIN_SECRET='slug-alias-admin')
    def test_admin_numeric_slug_edit_returns_validation_error_without_changing_the_race(self) -> None:
        other = self.make_race('other')
        for numeric_slug in (str(other.pk), '987654321', '00123'):
            with self.subTest(numeric_slug=numeric_slug):
                response = self.client.patch(
                    reverse('admin-race-detail', kwargs={'slug': self.race.slug}),
                    {'slug': numeric_slug, 'title': 'Must not change'}, format='json',
                    HTTP_AUTHORIZATION='Bearer slug-alias-admin',
                )
                self.assertEqual(response.status_code, 422)
                self.assertIn('slug', response.data['errors'])
                self.race.refresh_from_db()
                self.assertEqual(self.race.slug, 'original')
                self.assertEqual(self.race.title, 'original')
        self.assertFalse(RaceAlias.objects.exists())

    def test_numeric_title_generator_avoids_numeric_urls_and_reserved_aliases(self) -> None:
        self.assertEqual(Race.generate_unique_slug('123'), 'race-123')
        numeric_title = self.make_race('race-123')
        self.assertEqual(Race.generate_unique_slug('123'), 'race-123-2')
        self.reserve_alias('race-123-2', numeric_title)
        self.assertEqual(Race.generate_unique_slug('123'), 'race-123-3')

    @override_settings(ADMIN_SECRET='slug-alias-admin')
    def test_unsafe_slugs_reject_model_and_admin_edits_without_partial_changes(self) -> None:
        for unsafe_slug in ('', 'a/b', 'a?b', 'a#b', 'a%b', 'a\\b', '.', '..'):
            with self.subTest(unsafe_slug=unsafe_slug):
                with self.assertRaises(ValidationError):
                    self.make_race(unsafe_slug)
                self.race.slug = unsafe_slug
                self.race.title = 'Must not change'
                with self.assertRaises(ValidationError):
                    self.race.save(update_fields=['slug', 'title'])
                self.race.refresh_from_db()
                self.assertEqual(self.race.slug, 'original')
                self.assertEqual(self.race.title, 'original')
                response = self.client.patch(
                    reverse('admin-race-detail', kwargs={'slug': self.race.slug}),
                    {'slug': unsafe_slug, 'title': 'Must not change'}, format='json',
                    HTTP_AUTHORIZATION='Bearer slug-alias-admin',
                )
                self.assertEqual(response.status_code, 422)
                self.assertIn('slug', response.data['errors'])
                self.race.refresh_from_db()
                self.assertEqual(self.race.slug, 'original')
                self.assertEqual(self.race.title, 'original')
                self.assertEqual(Race.objects.count(), 1)
                self.assertFalse(RaceAlias.objects.exists())

    def test_empty_or_punctuation_only_titles_get_a_unique_fallback_slug(self) -> None:
        for title in ('', '!!!'):
            with self.subTest(title=title):
                self.assertEqual(Race.generate_unique_slug(title), 'race')
        fallback = self.make_race('race')
        self.assertEqual(Race.generate_unique_slug('!!!'), 'race-2')
        self.reserve_alias('race-2', fallback)
        self.assertEqual(Race.generate_unique_slug('!!!'), 'race-3')

    @override_settings(ADMIN_SECRET='slug-alias-admin')
    def test_non_ascii_numeric_slugs_resolve_their_own_race_including_admin(self) -> None:
        self.make_race('numeric-id-owner', id=123)
        for unicode_slug in ('１２３', '١٢٣'):
            with self.subTest(unicode_slug=unicode_slug):
                self.race.slug = unicode_slug
                self.race.save(update_fields=['slug'])
                self.assertEqual(resolve_race(unicode_slug).pk, self.race.pk)
                response = self.client.get(
                    reverse('admin-race-detail', kwargs={'slug': unicode_slug}),
                    HTTP_AUTHORIZATION='Bearer slug-alias-admin',
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data['id'], self.race.pk)
                self.assertEqual(response.data['slug'], unicode_slug)

    def test_unicode_numeric_slugs_merge_and_keep_aliases_without_taking_a_live_numeric_id(self) -> None:
        numeric_id_owner = self.make_race('numeric-id-owner', id=123)
        target = self.make_race('final-target')
        old_identifiers: list[str] = []
        for unicode_slug in ('１２３', '²'):
            with self.subTest(unicode_slug=unicode_slug):
                source = self.make_race(unicode_slug)
                old_identifiers.extend((unicode_slug, str(source.pk)))
                merge_races(source.pk, target.pk, apply=True)
                self.assertFalse(Race.objects.filter(pk=source.pk).exists())

        for identifier in old_identifiers:
            with self.subTest(identifier=identifier):
                self.assertEqual(resolve_race(identifier).pk, target.pk)
        self.assertEqual(resolve_race('123').pk, numeric_id_owner.pk)
        self.assertEqual(resolve_race(numeric_id_owner.slug).pk, numeric_id_owner.pk)

    def test_korean_slug_remains_available_and_resolvable(self) -> None:
        korean_slug = Race.generate_unique_slug('서울 마라톤')
        self.assertEqual(korean_slug, '서울-마라톤')
        self.race.slug = korean_slug
        self.race.save(update_fields=['slug'])

        self.assertEqual(resolve_race(korean_slug).pk, self.race.pk)
        self.assertEqual(resolve_race('original').pk, self.race.pk)

    def test_renaming_an_active_crawler_race_does_not_mark_its_source_as_merged(self) -> None:
        self.race.slug = 'renamed-crawler-race'
        self.race.save()

        self.assertIsNone(merged_source_race(source_url=self.race.source_url))
        self.assertIsNone(merged_source_race(external_id=self.race.external_id, source='crawl'))
        self.assertIsNone(merged_source_race(
            source_url=self.race.source_url, external_id=self.race.external_id,
            source='crawl', race_date=self.race.race_date,
        ))
        result = MarathonCrawlerService().save_detailed_race({
            'title': self.race.title, 'race_date': self.race.race_date,
            'location': self.race.location, 'region': self.race.region,
            'distances': self.race.distances, 'external_id': self.race.external_id,
            'source_url': self.race.source_url, 'description': 'Fresh crawler description',
        })

        self.assertEqual(result['race'].pk, self.race.pk)
        self.assertEqual(result['status'], 'updated')
        self.race.refresh_from_db()
        self.assertEqual(self.race.description, 'Fresh crawler description')
        self.assertEqual(self.race.slug, 'renamed-crawler-race')
        self.assertEqual(Race.objects.count(), 1)
