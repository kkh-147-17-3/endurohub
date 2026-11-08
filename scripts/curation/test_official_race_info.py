"""Database safety checks for the reviewed official race information batch."""

import copy
from datetime import date
import importlib.util
import json
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model

from accounts.models import RaceRecord
from races.models import Race, RaceFavorite, RaceParticipation, Review


_SCRIPT = Path(__file__).with_name('apply_official_race_info.py')
_SPEC = importlib.util.spec_from_file_location('official_race_curation', _SCRIPT)
curation = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(curation)

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def batch():
    races = []
    for race_id, slug, source in [
        (341, '2026-pohang-championship', 'https://pohangmarathon.com/'),
        (546, '26th-suncheon-marathon', 'http://sc-marathon.kr/'),
    ]:
        race = Race.objects.create(
            id=race_id, title=f'Official race {race_id}', slug=slug,
            sport='running', race_date=date(2026, 11, 14),
            location='Official venue', region='경북', official_url=source,
            description='Existing description', ai_summary='Existing summary',
            registration_end=date(2026, 11, 1),
            locked_fields=['title', 'organizer'],
            distances=[{
                'id': f'course-{race_id}-10k', 'code': '10K', 'name': '10km',
                'distance_meter': 10000, 'fee': 20000,
                'start_time': None, 'cutoff': None,
            }],
        )
        races.append(race)

    user = get_user_model().objects.create_user(username='curation-preservation')
    review = Review.objects.create(
        race=races[0], user=user, rating=5, comment='Keep this review',
        ip_hash='a' * 64,
    )
    favorite = RaceFavorite.objects.create(race=races[0], user=user)
    participation = RaceParticipation.objects.create(
        race=races[0], user=user, status='confirmed_going',
        planned_codes=['10K'], main_goal=True, note='Keep this plan',
    )
    record = RaceRecord.objects.create(
        race=races[0], user=user, sport='running', distance='10km',
        course_code='10K', duration_seconds=3000, is_public=True,
    )
    entries = []
    for race in races:
        distances = copy.deepcopy(race.distances)
        distances[0].update(fee=50000, start_time='09:00', cutoff='2시간')
        changes = {
            'description': (
                '<p>공식 확인: 2026년 11월 8일</p>'
                f'<p><a href="{race.official_url}">공식 출처</a></p>'
            ),
            'ai_summary': 'Officially verified participant information.',
            'distances': distances,
            'start_time': '09:00',
            'race_end_date': '2026-11-14',
            'registration_end': '2026-11-03',
            'status': 'registration_closed',
        }
        entries.append({
            'id': race.pk, 'slug': race.slug, 'race_date': '2026-11-14',
            'sources': [{'url': race.official_url}],
            'expected': {
                key: curation.json_value(getattr(race, key)) for key in changes
            },
            'changes': changes,
        })
    return {
        'races': races,
        'manifest': {'schema_version': 1, 'checked_on': '2026-11-08', 'races': entries},
        'related_ids': [review.pk, favorite.pk, participation.pk, record.pk],
    }


def database_snapshot():
    return {
        model._meta.label: list(model.objects.order_by('pk').values())
        for model in [Race, Review, RaceFavorite, RaceParticipation, RaceRecord]
    }


def test_preview_preserves_all_database_values_and_creates_no_backup(batch, tmp_path):
    before = database_snapshot()
    backup = tmp_path / 'preview-must-not-write.json'

    receipt = curation.apply_manifest(
        batch['manifest'], backup_path=backup, manifest_sha256='reviewed-manifest',
    )

    assert receipt['mode'] == 'preview'
    assert receipt['manifest_sha256'] == 'reviewed-manifest'
    assert len(receipt['races']) == 2
    assert all(row['changed_fields'] for row in receipt['races'])
    assert all(row['context']['raw_status'] is None for row in receipt['races'])
    assert database_snapshot() == before
    assert not backup.exists()


def test_apply_preserves_race_course_and_member_content_identity_and_adds_locks(batch, tmp_path):
    before = database_snapshot()
    backup = tmp_path / 'before.json'

    receipt = curation.apply_manifest(batch['manifest'], apply=True, backup_path=backup)

    assert receipt['mode'] == 'apply'
    stored = json.loads(backup.read_text(encoding='utf-8'))
    assert stored == receipt
    assert stored['races'][0]['before']['description'] == 'Existing description'
    assert stored['races'][0]['locked_fields_before'] == ['title', 'organizer']
    for race, entry in zip(batch['races'], batch['manifest']['races']):
        old = next(row for row in before['races.Race'] if row['id'] == race.pk)
        race.refresh_from_db()
        assert race.slug == old['slug']
        assert race.title == old['title']
        assert race.race_date == old['race_date']
        assert race.official_url == old['official_url']
        assert race.distances == entry['changes']['distances']
        assert race.distances[0]['id'] == old['distances'][0]['id']
        assert race.distances[0]['code'] == old['distances'][0]['code']
        assert race.distances[0]['distance_meter'] == old['distances'][0]['distance_meter']
        assert {'title', 'organizer'} <= set(race.locked_fields)
        assert set(entry['changes']) & set(Race.CRAWLER_TRACKED_FIELDS) <= set(race.locked_fields)
        assert len(race.locked_fields) == len(set(race.locked_fields))
    after = database_snapshot()
    for label in ['races.Review', 'races.RaceFavorite', 'races.RaceParticipation', 'accounts.RaceRecord']:
        assert after[label] == before[label]


def test_reapplying_same_reviewed_batch_is_a_database_noop(batch, tmp_path):
    curation.apply_manifest(batch['manifest'], apply=True, backup_path=tmp_path / 'first.json')
    before = database_snapshot()

    second = curation.apply_manifest(
        batch['manifest'], apply=True, backup_path=tmp_path / 'second.json',
    )

    assert all(row['changed_fields'] == [] for row in second['races'])
    assert database_snapshot() == before


def test_concurrent_edit_on_last_entry_aborts_entire_batch_before_backup(batch, tmp_path):
    Race.objects.filter(pk=546).update(ai_summary='Concurrent operator edit')
    before = database_snapshot()
    backup = tmp_path / 'must-not-exist.json'

    with pytest.raises(curation.CurationConflict, match='Concurrent edit'):
        curation.apply_manifest(batch['manifest'], apply=True, backup_path=backup)

    assert database_snapshot() == before
    assert not backup.exists()


@pytest.mark.parametrize('identity_field,new_value', [
    ('slug', 'another-edition'), ('race_date', date(2027, 11, 14)),
])
def test_changed_identity_aborts_all_rows(batch, tmp_path, identity_field, new_value):
    Race.objects.filter(pk=546).update(**{identity_field: new_value})
    before = database_snapshot()
    with pytest.raises(curation.CurationConflict, match='identity'):
        curation.apply_manifest(batch['manifest'], apply=True, backup_path=tmp_path / 'backup.json')
    assert database_snapshot() == before


def test_missing_backup_or_existing_backup_fails_before_any_write(batch, tmp_path):
    before = database_snapshot()
    with pytest.raises(curation.CurationConflict, match='backup'):
        curation.apply_manifest(batch['manifest'], apply=True)
    backup = tmp_path / 'existing-private-backup.json'
    backup.write_text('preserve previous backup', encoding='utf-8')
    with pytest.raises(FileExistsError):
        curation.apply_manifest(batch['manifest'], apply=True, backup_path=backup)
    assert database_snapshot() == before
    assert backup.read_text(encoding='utf-8') == 'preserve previous backup'


def test_save_failure_on_second_race_rolls_back_first_race(batch, tmp_path, monkeypatch):
    before = database_snapshot()
    original_save = Race.save

    def fail_second_save(self, *args, **kwargs):
        if self.pk == 546:
            raise RuntimeError('simulated database failure')
        return original_save(self, *args, **kwargs)

    monkeypatch.setattr(Race, 'save', fail_second_save)
    backup = tmp_path / 'verified-before-image.json'
    with pytest.raises(RuntimeError, match='simulated database failure'):
        curation.apply_manifest(batch['manifest'], apply=True, backup_path=backup)
    assert database_snapshot() == before
    assert backup.exists()


@pytest.mark.parametrize('field,new_value', [
    ('id', 'replacement-course'), ('code', 'HM'), ('name', '하프'),
    ('distance_meter', 21097),
])
def test_course_identity_changes_fail_closed(batch, field, new_value):
    batch['manifest']['races'][0]['changes']['distances'][0][field] = new_value
    before = database_snapshot()
    with pytest.raises(curation.CurationConflict):
        curation.apply_manifest(batch['manifest'])
    assert database_snapshot() == before


@pytest.mark.parametrize('change', [
    {'fee': -1}, {'fee': 4.5}, {'fee': True},
    {'start_time': '24:00'}, {'start_time': '9:00'}, {'start_time': '08:60'},
])
def test_malformed_course_prices_and_start_times_fail_closed(batch, change):
    batch['manifest']['races'][0]['changes']['distances'][0].update(change)
    before = database_snapshot()
    with pytest.raises(curation.CurationConflict):
        curation.apply_manifest(batch['manifest'])
    assert database_snapshot() == before


@pytest.mark.parametrize('field,new_value', [
    ('status', 'registration_open'), ('slug', 'replacement-slug'),
    ('official_url', 'https://other.example/'),
])
def test_unapproved_race_changes_fail_closed(batch, field, new_value):
    entry = batch['manifest']['races'][0]
    entry['changes'][field] = new_value
    entry['expected'][field] = curation.json_value(getattr(batch['races'][0], field))
    before = database_snapshot()
    with pytest.raises(curation.CurationConflict):
        curation.apply_manifest(batch['manifest'])
    assert database_snapshot() == before


@pytest.mark.parametrize('description', [
    '<p>Official source https://pohangmarathon.com/</p>',
    '<p>공식 확인: 2026년 11월 8일</p>',
])
def test_visible_verification_date_and_source_are_required(batch, description):
    batch['manifest']['races'][0]['changes']['description'] = description
    with pytest.raises(curation.CurationConflict):
        curation.apply_manifest(batch['manifest'])


def test_fee_edit_does_not_autofill_preexisting_missing_course_distance(batch, tmp_path):
    """Legacy course JSON must retain distance identity even through Race.save()."""
    race = batch['races'][0]
    old_distances = copy.deepcopy(race.distances)
    old_distances[0].pop('distance_meter')
    Race.objects.filter(pk=race.pk).update(distances=old_distances)
    entry = batch['manifest']['races'][0]
    entry['expected']['distances'] = old_distances
    entry['changes']['distances'] = copy.deepcopy(old_distances)
    entry['changes']['distances'][0]['fee'] = 50000
    before = database_snapshot()
    backup = tmp_path / 'legacy.json'
    try:
        curation.apply_manifest(batch['manifest'], apply=True, backup_path=backup)
    except curation.CurationConflict:
        # Explicitly declining a legacy row is also safe, before any batch write.
        assert database_snapshot() == before
        assert not backup.exists()
        return
    race.refresh_from_db()
    assert 'distance_meter' not in race.distances[0]
