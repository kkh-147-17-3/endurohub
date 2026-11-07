from datetime import timedelta
from io import StringIO
from typing import Any
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import RaceRecord, UserProfile
from accounts.serializers import upsert_linked_race_record
from core.models import AnalyticsEvent
from posts.models import Post, PostRace
from races.models import (
    Race, RaceAlias, RaceFavorite, RaceMergeLog, RaceParticipation,
    RacePendingChange, Review, ReviewLike,
)
from races.resolution import resolve_race
from races.services.marathon_crawler import MarathonCrawlerService
from races.services.merge_races import MergeConflict, merge_races, merged_source_race


class RaceMergeTests(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.addCleanup(cache.clear)
        self.track_patcher = patch('races.views.track')
        self.track_patcher.start()
        self.addCleanup(self.track_patcher.stop)
        self.source = self.make_race('duplicate', view_count=7, source_url='https://example.org/old')
        self.target = self.make_race('canonical', view_count=11, source_url='https://example.org/new')
        self.user = User.objects.create_user(username='shared', email='shared@example.org')
        UserProfile.objects.create(user=self.user, nickname='회원', email_verified=True)

    def make_race(self, slug: str, **kwargs: Any) -> Race:
        return Race.objects.create(
            title=slug, slug=slug, sport='running',
            race_date=timezone.localdate() - timedelta(days=1),
            location='서울', region='서울', distances=[{'name': '10km', 'distance_meter': 10000}],
            source='crawl', **kwargs,
        )

    def review(self, race: Race, user: User | None = None, **kwargs: Any) -> Review:
        return Review.objects.create(
            race=race, user=user, rating=4, comment='원래 대회 후기입니다.', ip_hash='original-ip', **kwargs,
        )

    def record(self, race: Race, user: User, **kwargs: Any) -> RaceRecord:
        return RaceRecord.objects.create(
            race=race, user=user, sport='running', distance='10km', course_code='10K',
            duration_seconds=3600, **kwargs,
        )

    def test_preview_and_command_default_leave_everything_unchanged(self) -> None:
        review = self.review(self.source, self.user)
        output = StringIO()
        call_command('merge_races', source=self.source.pk, target=self.target.pk, stdout=output)
        self.assertIn('PREVIEW ONLY', output.getvalue())
        self.assertIn('metadata_differences_target_wins', output.getvalue())
        review.refresh_from_db()
        self.assertEqual(review.race_id, self.source.pk)
        self.assertIsNone(review.merge_source_race_id)
        self.assertEqual(Race.objects.count(), 2)
        self.assertFalse(RaceAlias.objects.exists())
        self.assertFalse(RaceMergeLog.objects.exists())

    def test_merge_preserves_overlapping_reviews_likes_and_results(self) -> None:
        old_review = self.review(self.source, self.user)
        current_review = self.review(self.target, self.user)
        anonymous = self.review(self.source)
        like = ReviewLike.objects.create(review=old_review, ip_hash='a-fan')
        old_record = self.record(self.source, self.user, is_public=False, is_personal_best=True)
        current_record = self.record(self.target, self.user, is_public=True)
        original_created_at = old_record.created_at
        result = merge_races(self.source.pk, self.target.pk, apply=True)
        self.assertTrue(result['applied'])
        self.assertFalse(Race.objects.filter(pk=self.source.pk).exists())
        self.assertEqual(Review.objects.filter(race=self.target).count(), 3)
        for review in (old_review, current_review, anonymous):
            review.refresh_from_db()
            self.assertEqual(review.race_id, self.target.pk)
            self.assertEqual(review.comment, '원래 대회 후기입니다.')
        self.assertEqual(old_review.user_id, self.user.pk)
        self.assertEqual(ReviewLike.objects.get(pk=like.pk).review_id, old_review.pk)
        self.assertEqual(RaceRecord.objects.filter(race=self.target).count(), 2)
        old_record.refresh_from_db()
        current_record.refresh_from_db()
        self.assertEqual(old_record.merge_source_race_id, self.source.pk)
        self.assertIsNone(current_record.merge_source_race_id)
        self.assertFalse(old_record.is_public)
        self.assertTrue(old_record.is_personal_best)
        self.assertEqual(old_record.created_at, original_created_at)
        self.target.refresh_from_db()
        self.assertEqual(self.target.view_count, 18)
        self.assertEqual(self.target.title, 'canonical')
        log = RaceMergeLog.objects.get(pk=result['merge_log_id'])
        self.assertEqual(log.snapshot['source']['slug'], 'duplicate')
        self.assertEqual(len(log.snapshot['relations']['races.review']), 3)

    def test_favorites_union_keeps_earliest_date_and_all_users(self) -> None:
        other = User.objects.create_user(username='other')
        old = RaceFavorite.objects.create(user=self.user, race=self.source)
        current = RaceFavorite.objects.create(user=self.user, race=self.target)
        unique = RaceFavorite.objects.create(user=other, race=self.source)
        earliest = timezone.now() - timedelta(days=30)
        RaceFavorite.objects.filter(pk=old.pk).update(created_at=earliest)
        merge_races(self.source.pk, self.target.pk, apply=True)
        self.assertEqual(RaceFavorite.objects.filter(race=self.target).count(), 2)
        current.refresh_from_db()
        unique.refresh_from_db()
        self.assertEqual(current.created_at, earliest)
        self.assertEqual(unique.race_id, self.target.pk)

    def test_participation_post_links_pending_changes_and_analytics_survive(self) -> None:
        RaceParticipation.objects.create(
            race=self.source, user=self.user, status='confirmed_going',
            planned_codes=['10K', 'HM'], note='교통편 확인', main_goal=True,
        )
        part = RaceParticipation.objects.create(
            race=self.target, user=self.user, planned_codes=['10K'], note='친구와 참가',
        )
        post = Post.objects.create(title='후기', content='글', ip_hash='post-ip')
        PostRace.objects.create(post=post, race=self.source)
        PostRace.objects.create(post=post, race=self.target)
        change = RacePendingChange.objects.create(
            race=self.source, field_name='location', old_value='서울', new_value='부산',
        )
        event = AnalyticsEvent.objects.create(
            event_type='race_view', item_type='race', item_id=str(self.source.pk),
            properties={'race_id': self.source.pk},
        )
        unrelated = AnalyticsEvent.objects.create(
            event_type='post_view', item_type='post', item_id=str(self.source.pk),
        )
        merge_races(self.source.pk, self.target.pk, apply=True)
        part.refresh_from_db()
        change.refresh_from_db()
        event.refresh_from_db()
        unrelated.refresh_from_db()
        self.assertEqual(part.status, 'confirmed_going')
        self.assertEqual(part.planned_codes, ['10K', 'HM'])
        self.assertTrue(part.main_goal)
        self.assertEqual(part.note, '친구와 참가\n교통편 확인')
        self.assertEqual(PostRace.objects.filter(post=post, race=self.target).count(), 1)
        self.assertEqual(change.race_id, self.target.pk)
        self.assertEqual(event.item_id, str(self.target.pk))
        self.assertEqual(event.properties, {'race_id': self.source.pk})
        self.assertEqual(unrelated.item_id, str(self.source.pk))

    def test_current_record_upsert_updates_only_current_preserving_history(self) -> None:
        historical = self.record(self.source, self.user, is_public=False)
        current = self.record(self.target, self.user, is_public=True)
        merge_races(self.source.pk, self.target.pk, apply=True)
        edited = upsert_linked_race_record(
            user=self.user, race=self.target,
            result_data={'course_code': '10K', 'duration_seconds': 4200},
        )
        historical.refresh_from_db()
        current.refresh_from_db()
        self.assertEqual(edited.pk, current.pk)
        self.assertEqual(current.duration_seconds, 4200)
        self.assertEqual(historical.duration_seconds, 3600)
        self.assertFalse(historical.is_public)
        self.assertEqual(RaceRecord.objects.filter(user=self.user, race=self.target).count(), 2)

    def test_nonoverlapping_result_stays_current(self) -> None:
        record = self.record(self.source, self.user)
        merge_races(self.source.pk, self.target.pk, apply=True)
        record.refresh_from_db()
        self.assertEqual(record.race_id, self.target.pk)
        self.assertIsNone(record.merge_source_race_id)

    def test_alias_chain_flattens_and_audit_ids_remain_historical(self) -> None:
        last = self.make_race('last')
        first_source_id = self.source.pk
        middle_id = self.target.pk
        merge_races(first_source_id, middle_id, apply=True)
        merge_races(middle_id, last.pk, apply=True)
        for identifier in ('duplicate', 'canonical', str(first_source_id), str(middle_id)):
            self.assertEqual(resolve_race(identifier).pk, last.pk)
        self.assertEqual(RaceAlias.objects.values('race_id').distinct().get()['race_id'], last.pk)
        self.assertEqual(RaceMergeLog.objects.get(source_race_id=first_source_id).target_race_id, middle_id)
        self.assertEqual(Race.generate_unique_slug('duplicate'), 'duplicate-2')

    def test_injected_failure_rolls_back_all_relations_and_audit(self) -> None:
        review = self.review(self.source, self.user)
        favorite = RaceFavorite.objects.create(race=self.source, user=self.user)
        with patch.object(Race, 'delete', side_effect=RuntimeError('injected failure')):
            with self.assertRaisesMessage(RuntimeError, 'injected failure'):
                merge_races(self.source.pk, self.target.pk, apply=True)
        review.refresh_from_db()
        favorite.refresh_from_db()
        self.assertEqual(review.race_id, self.source.pk)
        self.assertIsNone(review.merge_source_race_id)
        self.assertEqual(favorite.race_id, self.source.pk)
        self.assertFalse(RaceAlias.objects.exists())
        self.assertFalse(RaceMergeLog.objects.exists())
        self.assertEqual(Race.objects.count(), 2)

    def test_incompatible_event_or_overlong_notes_abort_before_writing(self) -> None:
        self.target.race_date += timedelta(days=1)
        self.target.save(update_fields=['race_date'])
        with self.assertRaisesMessage(MergeConflict, 'race_date differs'):
            merge_races(self.source.pk, self.target.pk, apply=True)
        self.target.race_date = self.source.race_date
        self.target.save(update_fields=['race_date'])
        RaceParticipation.objects.create(race=self.source, user=self.user, note='a' * 150)
        RaceParticipation.objects.create(race=self.target, user=self.user, note='b' * 150)
        with self.assertRaisesMessage(MergeConflict, 'exceed 200'):
            merge_races(self.source.pk, self.target.pk, apply=True)
        self.assertEqual(Race.objects.count(), 2)
        self.assertFalse(RaceMergeLog.objects.exists())

    def test_normal_writes_keep_unique_current_review_and_result_constraints(self) -> None:
        self.review(self.target, self.user)
        self.record(self.target, self.user)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.review(self.target, self.user)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.record(self.target, self.user)

    def test_old_slug_numeric_detail_like_and_favorite_endpoints_resolve(self) -> None:
        review = self.review(self.source, self.user)
        merge_races(self.source.pk, self.target.pk, apply=True)
        for identifier in (self.source.slug, str(self.source.pk)):
            response = self.client.get(reverse('race-detail', kwargs={'slug': identifier}))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['race']['slug'], self.target.slug)
            self.assertEqual(response.data['reviews'][0]['id'], review.pk)
        like_response = self.client.post(reverse('review-like-toggle', kwargs={
            'slug': self.source.slug, 'review_id': review.pk,
        }))
        self.assertEqual(like_response.status_code, 200)
        self.assertTrue(like_response.data['liked'])
        self.client.force_authenticate(user=self.user)
        favorite_response = self.client.post(reverse('race-favorite-toggle', kwargs={'slug': str(self.source.pk)}))
        self.assertEqual(favorite_response.status_code, 200)
        self.assertTrue(RaceFavorite.objects.filter(user=self.user, race=self.target).exists())

    def test_alias_result_api_and_season_use_current_record(self) -> None:
        historical = self.record(self.source, self.user, is_public=True)
        current = self.record(self.target, self.user)
        merge_races(self.source.pk, self.target.pk, apply=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/me/races/{self.source.slug}/result/', {
            'course_code': '10K', 'hours': 0, 'minutes': 45, 'seconds': 0,
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['record']['id'], current.pk)
        historical.refresh_from_db()
        self.assertEqual(historical.duration_seconds, 3600)
        result = self.client.delete(f'/api/v1/me/races/{self.source.pk}/result/')
        self.assertEqual(result.status_code, 200)
        self.assertTrue(RaceRecord.objects.filter(pk=historical.pk).exists())
        self.assertFalse(RaceRecord.objects.filter(pk=current.pk).exists())

    def test_owner_sees_current_and_private_history_without_exposing_source_ids(self) -> None:
        historical = self.record(self.source, self.user, is_public=False)
        current = self.record(self.target, self.user, is_public=True)
        merge_races(self.source.pk, self.target.pk, apply=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/me/records/')
        self.assertEqual(response.status_code, 200)
        records = {row['id']: row for row in response.data['records']}
        self.assertTrue(records[historical.pk]['is_merge_history'])
        self.assertFalse(records[historical.pk]['is_public'])
        self.assertFalse(records[current.pk]['is_merge_history'])
        self.assertTrue(records[current.pk]['is_public'])
        self.assertNotIn('merge_source_race_id', records[historical.pk])
        detail = self.client.get(reverse('race-detail', kwargs={'slug': self.target.slug}))
        own_records = {row['id']: row for row in detail.data['seasonRecords']}
        self.assertTrue(own_records[historical.pk]['isMergeHistory'])
        self.assertFalse(own_records[current.pk]['isMergeHistory'])
        self.client.force_authenticate(user=None)
        public = self.client.get(reverse('race-detail', kwargs={'slug': self.target.slug}))
        public_ids = {row['id'] for row in public.data['seasonRecords']}
        self.assertIn(current.pk, public_ids)
        self.assertNotIn(historical.pk, public_ids)

    def test_crawler_skips_merged_source_and_namespaces_external_ids(self) -> None:
        self.source.external_id = 'old-123'
        self.source.save(update_fields=['external_id'])
        merge_races(self.source.pk, self.target.pk, apply=True)
        service = MarathonCrawlerService()
        result = service.save_detailed_race({
            'external_id': 'old-123', 'title': 'duplicate', 'source_url': 'https://example.org/old',
        })
        self.assertEqual(result['reason'], 'merged_duplicate_source')
        self.assertEqual(result['race'].pk, self.target.pk)
        self.assertEqual(Race.objects.count(), 1)
        canonical = merged_source_race(external_id='old-123', source='crawl')
        self.assertIsNotNone(canonical)
        assert canonical is not None
        self.assertEqual(canonical.pk, self.target.pk)
        self.assertIsNone(merged_source_race(external_id='old-123', source='another-feed'))
        self.assertIsNone(merged_source_race(external_id='old-123'))
        self.assertIsNone(merged_source_race(
            external_id='old-123', source='crawl', race_date=self.target.race_date + timedelta(days=365),
        ))

    def test_command_apply_requires_explicit_flag_and_records_log(self) -> None:
        output = StringIO()
        call_command('merge_races', source=self.source.pk, target=self.target.pk, apply=True, stdout=output)
        self.assertIn('"applied": true', output.getvalue())
        self.assertEqual(RaceMergeLog.objects.count(), 1)
        with self.assertRaises(MergeConflict):
            merge_races(self.source.pk, self.target.pk, apply=True)

    def test_reserved_old_url_and_id_cannot_be_reused_by_new_race(self) -> None:
        merge_races(self.source.pk, self.target.pk, apply=True)
        with self.assertRaises(ValidationError):
            self.make_race(self.source.slug)
        with self.assertRaises(ValidationError):
            self.make_race('new-slug', id=self.source.pk)

    def test_unknown_new_many_to_many_relation_fails_closed(self) -> None:
        relations = (*Race._meta.related_objects, SimpleNamespace(many_to_many=True, through=object()))
        with patch.object(Race._meta, 'related_objects', relations):
            with self.assertRaisesMessage(MergeConflict, 'Unhandled many-to-many'):
                merge_races(self.source.pk, self.target.pk, apply=True)
        self.assertEqual(Race.objects.count(), 2)
        self.assertFalse(RaceMergeLog.objects.exists())

    @override_settings(ADMIN_SECRET='merge-test-admin')
    def test_admin_slug_edit_rejects_reserved_alias_with_validation_response(self) -> None:
        third = self.make_race('third')
        merge_races(self.source.pk, self.target.pk, apply=True)
        response = self.client.patch(
            reverse('admin-race-detail', kwargs={'slug': third.slug}),
            {'slug': self.source.slug}, format='json',
            HTTP_AUTHORIZATION='Bearer merge-test-admin',
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn('slug', response.data['errors'])
        third.refresh_from_db()
        self.assertEqual(third.slug, 'third')
        third.slug = self.source.slug
        with self.assertRaises(ValidationError):
            third.full_clean()
