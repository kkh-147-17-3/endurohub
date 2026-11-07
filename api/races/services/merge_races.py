"""Explicit, preview-first duplicate-race merges with user-content preservation."""

import logging
from datetime import date
from typing import Any

from django.core.cache import cache
from django.db import transaction
from django.db.models import F, Model, Q

from accounts.models import RaceRecord
from core.models import AnalyticsEvent
from posts.models import PostRace
from races.models import (
    Race, RaceAlias, RaceFavorite, RaceMergeLog, RaceParticipation,
    RacePendingChange, Review,
)


class MergeConflict(ValueError):
    """The requested pair cannot be combined without an unsafe assumption."""


logger = logging.getLogger(__name__)


def _invalidate_cache() -> None:
    try:
        cache.clear()
    except Exception:
        # The merge has committed by this point; don't report it as a failed
        # transaction or invite an unsafe retry of an already merged ID.
        logger.exception('Race merge committed; shared cache invalidation failed.')


RELATION_MODELS: tuple[type[Model], ...] = (
    Review, RaceRecord, RaceFavorite, RaceParticipation, RacePendingChange,
    PostRace, RaceAlias,
)


def _participation_values(source: RaceParticipation, target: RaceParticipation) -> dict[str, Any]:
    for row in (source, target):
        if row.status not in {RaceParticipation.STATUS_MAYBE, RaceParticipation.STATUS_GOING}:
            raise MergeConflict(f'Unsupported participation status on row {row.pk}.')
        if not isinstance(row.planned_codes, list) or any(
            not isinstance(code, str) for code in row.planned_codes
        ):
            raise MergeConflict(f'Invalid planned_codes on participation {row.pk}.')
    codes = list(dict.fromkeys([*target.planned_codes, *source.planned_codes]))
    notes = list(dict.fromkeys(note for note in (target.note, source.note) if note))
    note = '\n'.join(notes)
    if len(note) > 200:
        raise MergeConflict(
            f'Participation notes for user {source.user_id} exceed 200 characters together; '
            'review and shorten the notes before merging. Neither note was changed.'
        )
    return {
        'status': RaceParticipation.STATUS_GOING if any(
            row.status == RaceParticipation.STATUS_GOING for row in (source, target)
        ) else RaceParticipation.STATUS_MAYBE,
        'planned_codes': codes,
        'main_goal': source.main_goal or target.main_goal,
        'note': note,
        'created_at': min(source.created_at, target.created_at),
        'updated_at': max(source.updated_at, target.updated_at),
    }


def _rows(model: type[Model], race_ids: list[int]) -> list[dict[str, Any]]:
    return list(model._default_manager.filter(race_id__in=race_ids).order_by('pk').values())


def _assert_known_relations() -> None:
    """A future FK must fail closed rather than be cascaded away by a merge."""
    for relation in Race._meta.related_objects:
        if relation.many_to_many:
            if getattr(relation, 'through', None) is PostRace:
                continue
            raise MergeConflict('Unhandled many-to-many race relationship; extend the merge service.')
        if relation.related_model not in RELATION_MODELS:
            raise MergeConflict(
                f'Unhandled race relationship: {relation.related_model._meta.label}; '
                'extend the merge service before applying this merge.'
            )
    for field in Race._meta.many_to_many:
        if getattr(field.remote_field, 'through', None) is not PostRace:
            raise MergeConflict('Unhandled many-to-many race field; extend the merge service.')


def merge_races(source_id: int, target_id: int, *, apply: bool = False) -> dict[str, Any]:
    """Preview or atomically merge one explicit duplicate into a chosen target.

    Target metadata is authoritative. The race date, end date and sport must
    match; this service never guesses that two different events are duplicates.
    A full snapshot of both races and every affected direct relationship is
    stored before applying. User-generated rows keep IDs and timestamps.
    """
    if source_id == target_id:
        raise MergeConflict('Source and target must be different race IDs.')
    if source_id <= 0 or target_id <= 0:
        raise MergeConflict('Source and target must be positive race IDs.')

    with transaction.atomic():
        # Deterministic row-lock order also serializes simultaneous merges that
        # share a source or target. PostgreSQL FK inserts wait for these locks.
        locked = {
            race.pk: race for race in Race.objects.select_for_update()
            .filter(pk__in=[source_id, target_id]).order_by('pk')
        }
        if len(locked) != 2:
            raise MergeConflict('Both IDs must identify live races; an ID is missing or already merged.')
        source, target = locked[source_id], locked[target_id]
        _assert_known_relations()
        for field in ('sport', 'race_date', 'race_end_date'):
            if getattr(source, field) != getattr(target, field):
                raise MergeConflict(
                    f'{field} differs between source and target; confirm the events '
                    'and correct the metadata before merging.'
                )

        alias_names = sorted({source.slug, str(source.pk)})
        for name in alias_names:
            live = Race.objects.filter(pk=int(name)) if name.isdigit() else Race.objects.filter(slug=name)
            if live.exclude(pk=source.pk).exists():
                raise MergeConflict(f'Old URL {name!r} belongs to another live race.')
            existing = RaceAlias.objects.filter(alias=name).first()
            if existing is not None and existing.race_id not in {source.pk, target.pk}:
                raise MergeConflict(f'Old URL {name!r} already points to a different race.')

        # Lock dependent rows too, for existing favorites, notes and results that
        # can be edited independently of race metadata.
        for model in RELATION_MODELS:
            list(model._default_manager.select_for_update().filter(
                race_id__in=[source_id, target_id],
            ).order_by('pk').values_list('pk', flat=True))

        relation_rows = {
            model._meta.label_lower: _rows(model, [source_id, target_id])
            for model in RELATION_MODELS
        }
        source_parts = list(RaceParticipation.objects.filter(race=source))
        target_parts = {
            row.user_id: row for row in RaceParticipation.objects.filter(race=target)
        }
        participation_updates = {
            row.pk: _participation_values(row, target_parts[row.user_id])
            for row in source_parts if row.user_id in target_parts
        }
        counts = {
            model._meta.label_lower: {
                'source': sum(row['race_id'] == source_id for row in rows),
                'target': sum(row['race_id'] == target_id for row in rows),
            }
            for model in RELATION_MODELS
            for rows in [relation_rows[model._meta.label_lower]]
        }
        overlap_counts: dict[str, int] = {}
        for model, key in (
            (Review, 'user_id'), (RaceRecord, 'user_id'),
            (RaceFavorite, 'user_id'), (RaceParticipation, 'user_id'),
            (PostRace, 'post_id'),
        ):
            rows = relation_rows[model._meta.label_lower]
            source_keys = {row[key] for row in rows if row['race_id'] == source_id and row[key] is not None}
            target_keys = {row[key] for row in rows if row['race_id'] == target_id and row[key] is not None}
            overlap_counts[model._meta.label_lower] = len(source_keys & target_keys)

        differences = {
            field.name: {'source': getattr(source, field.attname), 'target': getattr(target, field.attname)}
            for field in Race._meta.concrete_fields
            if field.name not in {'id', 'view_count', 'created_at', 'updated_at'}
            and getattr(source, field.attname) != getattr(target, field.attname)
        }
        result: dict[str, Any] = {
            'applied': False,
            'source': {'id': source.pk, 'slug': source.slug, 'title': source.title},
            'target': {'id': target.pk, 'slug': target.slug, 'title': target.title},
            'aliases': alias_names,
            'relations': counts,
            'overlapping_users_or_posts': overlap_counts,
            'metadata_differences_target_wins': differences,
        }
        if not apply:
            return result

        analytics = AnalyticsEvent.objects.select_for_update().filter(
            item_type='race', item_id__in=[str(source_id), str(target_id)],
        )
        snapshot = {
            'version': 1,
            'source': Race.objects.filter(pk=source_id).values().get(),
            'target': Race.objects.filter(pk=target_id).values().get(),
            'relations': relation_rows,
            # Likes/reward entries reference review IDs, which never change.
            'analytics_events': list(analytics.order_by('pk').values()),
        }
        log = RaceMergeLog.objects.create(
            source_race_id=source_id, target_race_id=target_id, snapshot=snapshot,
        )

        # Preserve all reviews, including two existing member reviews of the
        # same event. Imported overlaps are excluded from normal-write UNIQUE.
        Review.objects.filter(race=source, merge_source_race_id__isnull=True).update(
            merge_source_race_id=source_id,
        )
        Review.objects.filter(race=source).update(race=target)

        current_target_users = RaceRecord.objects.filter(
            race=target, merge_source_race_id__isnull=True,
        ).values('user_id')
        RaceRecord.objects.filter(
            race=source, merge_source_race_id__isnull=True,
            user_id__in=current_target_users,
        ).update(merge_source_race_id=source_id)
        RaceRecord.objects.filter(race=source).update(race=target)

        for favorite in RaceFavorite.objects.filter(race=source):
            existing_favorite = RaceFavorite.objects.filter(race=target, user_id=favorite.user_id).first()
            if existing_favorite is None:
                RaceFavorite.objects.filter(pk=favorite.pk).update(race=target)
            else:
                RaceFavorite.objects.filter(pk=existing_favorite.pk).update(
                    created_at=min(favorite.created_at, existing_favorite.created_at),
                )
                favorite.delete()  # Same user's bookmark is one bookmark; snapshot retains both rows.

        for participation in source_parts:
            existing_part = target_parts.get(participation.user_id)
            if existing_part is None:
                RaceParticipation.objects.filter(pk=participation.pk).update(race=target)
            else:
                RaceParticipation.objects.filter(pk=existing_part.pk).update(
                    **participation_updates[participation.pk],
                )
                participation.delete()

        for link in PostRace.objects.filter(race=source):
            if PostRace.objects.filter(race=target, post_id=link.post_id).exists():
                link.delete()
            else:
                PostRace.objects.filter(pk=link.pk).update(race=target)
        RacePendingChange.objects.filter(race=source).update(race=target)

        RaceAlias.objects.filter(race=source).update(race=target)
        for name in alias_names:
            RaceAlias.objects.update_or_create(alias=name, defaults={
                'race': target, 'source_race_id': source_id, 'source_slug': source.slug,
                'source': source.source,
                'source_url': source.source_url or '', 'external_id': source.external_id or '',
            })
        AnalyticsEvent.objects.filter(item_type='race', item_id=str(source_id)).update(
            item_id=str(target_id),
        )
        Race.objects.filter(pk=target_id).update(view_count=F('view_count') + source.view_count)

        # A future unsupported relation must not vanish through CASCADE. There
        # should be no remaining direct FK when deleting the duplicate row.
        for model in RELATION_MODELS:
            if model._default_manager.filter(race_id=source_id).exists():
                raise MergeConflict(f'Unmoved relationship: {model._meta.label}.')
        source.delete()
        transaction.on_commit(_invalidate_cache)
        result.update(applied=True, merge_log_id=log.pk)
        return result


def merged_source_race(
    *, source_url: str | None = None, external_id: str | None = None, source: str | None = None,
    race_date: date | None = None,
) -> Race | None:
    """Find a previously merged crawler identity without recreating a duplicate."""
    query = Q()
    if source_url:
        query |= Q(source_url=source_url)
    if external_id and source:
        query |= Q(external_id=external_id, source=source)
    if not query:
        return None
    aliases = RaceAlias.objects.filter(query)
    if race_date is not None:
        aliases = aliases.filter(race__race_date=race_date)
    targets = list(aliases.values_list('race_id', flat=True).distinct()[:2])
    if len(targets) > 1:
        raise MergeConflict('Crawler source identity maps to multiple canonical races; review aliases.')
    return Race.objects.filter(pk=targets[0]).first() if targets else None
