"""Preview/apply the reviewed November 2026 official-information batch.

Runs inside the existing Django API container; it never changes race identity,
course identity, user content, or the running application checkout.
"""

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit


ALLOWED_IDS = {341, 546, 569, 621, 623, 626, 660, 679}
ALLOWED_FIELDS = {
    'description', 'ai_summary', 'distances', 'start_time', 'race_end_date',
    'registration_end', 'status',
    'official_url', 'location', 'address',
}


class CurationConflict(ValueError):
    pass


def json_value(value):
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return copy.deepcopy(value)


def validate_manifest(manifest):
    if manifest.get('schema_version') != 1 or manifest.get('checked_on') != '2026-11-08':
        raise CurationConflict('Unexpected manifest version or verification date.')
    entries = manifest.get('races', [])
    ids = [row['id'] for row in entries]
    if not ids or len(ids) != len(set(ids)) or not set(ids) <= ALLOWED_IDS:
        raise CurationConflict('Duplicate or out-of-scope race IDs.')
    for row in entries:
        changes = row['changes']
        if not changes or not set(changes) <= ALLOWED_FIELDS:
            raise CurationConflict(f"Unsupported changes for race {row['id']}.")
        if 'status' in changes and changes['status'] != 'registration_closed':
            raise CurationConflict('Only officially confirmed registration closure is in scope.')
        if set(row['expected']) != set(changes):
            raise CurationConflict('Every changed field needs an expected before-value.')
        if row['race_date'] != '2026-11-14':
            raise CurationConflict('Unexpected race edition/date.')
        if not row.get('sources'):
            raise CurationConflict('Official sources are required.')
        if 'official_url' in changes and changes['official_url'] not in {
            source['url'] for source in row['sources']
        }:
            raise CurationConflict('Official URL must be one of the reviewed official sources.')
        for source in row['sources']:
            url = urlsplit(source['url'])
            if url.scheme not in {'http', 'https'} or not url.netloc or url.username:
                raise CurationConflict('Source must be a public HTTP(S) URL.')
        if 'description' in changes:
            description = changes['description']
            if '2026년 11월 8일' not in description:
                raise CurationConflict('Visible official verification date is required.')
            if not all(source['url'].replace('&', '&amp;') in description
                       for source in row['sources']):
                raise CurationConflict('Every official source must be visible in the description.')
        if 'distances' in changes:
            before, after = row['expected']['distances'], changes['distances']
            if len(before) != len(after):
                raise CurationConflict('Course identity/count must be preserved.')
            for old, new in zip(before, after):
                if old.get('name') != new.get('name') or old.get('distance_meter') != new.get('distance_meter'):
                    raise CurationConflict('Course names and distances must be preserved.')
                if not isinstance(old.get('distance_meter'), (int, float)) or old['distance_meter'] <= 0:
                    raise CurationConflict('A stored course distance is required to avoid implicit model backfills.')
                for key in set(old) | set(new):
                    if old.get(key) != new.get(key) and key not in {'fee', 'start_time', 'cutoff'}:
                        raise CurationConflict(f'Unsupported course change: {key}.')
                fee = new.get('fee')
                if fee is not None and (type(fee) is not int or fee < 0):
                    raise CurationConflict('Fees must be nonnegative integer KRW values.')
                start = new.get('start_time')
                if start is not None and not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', start):
                    raise CurationConflict('Course start must be HH:mm.')


def prepare_entries(manifest):
    from races.admin_api import RaceAdminEditSerializer
    from races.models import Race

    validate_manifest(manifest)
    rows = {race.pk: race for race in Race.objects.select_for_update().filter(
        pk__in=sorted(row['id'] for row in manifest['races'])
    ).order_by('pk')}
    prepared = []
    for entry in manifest['races']:
        race = rows.get(entry['id'])
        if race is None or race.slug != entry['slug'] or race.race_date.isoformat() != entry['race_date']:
            raise CurationConflict(f"Race identity changed: {entry['id']}.")
        serializer = RaceAdminEditSerializer(race, data=entry['changes'], partial=True)
        serializer.is_valid(raise_exception=True)
        desired = {key: json_value(value) for key, value in serializer.validated_data.items()}
        before = {key: json_value(getattr(race, key)) for key in desired}
        for key, actual in before.items():
            if actual != entry['expected'][key] and actual != desired[key]:
                raise CurationConflict(f"Concurrent edit on race {race.pk}, field {key}; no batch changes saved.")
        changed = [key for key in desired if before[key] != desired[key]]
        prepared.append((race, serializer.validated_data, {
            'id': race.pk, 'title': race.title, 'slug': race.slug,
            'race_date': race.race_date.isoformat(), 'changed_fields': changed,
            'before': before, 'after': desired,
            'locked_fields_before': copy.deepcopy(race.locked_fields),
            'updated_at_before': race.updated_at.isoformat(),
            'context': {'raw_status': race.status},
        }))
    return prepared


def apply_manifest(manifest, *, apply=False, backup_path=None, manifest_sha256=None):
    from django.core.cache import cache
    from django.db import transaction

    with transaction.atomic():
        prepared = prepare_entries(manifest)
        receipt = {
            'mode': 'apply' if apply else 'preview',
            'checked_on': manifest['checked_on'], 'manifest_sha256': manifest_sha256,
            'races': [item[2] for item in prepared],
        }
        if apply:
            if backup_path is None:
                raise CurationConflict('A private before-image backup is required before applying.')
            # Fail closed before any write if the backup cannot be created.
            fd = os.open(backup_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w', encoding='utf-8') as backup:
                json.dump(receipt, backup, ensure_ascii=False, indent=2)
                backup.flush()
                os.fsync(backup.fileno())
            for race, values, item in prepared:
                changed = item['changed_fields']
                if not changed:
                    continue
                for key in changed:
                    setattr(race, key, copy.deepcopy(values[key]))
                race.lock_fields_for_edit(changed)
                race.save(update_fields=[*changed, 'locked_fields', 'updated_at'])
            if any(item[2]['changed_fields'] for item in prepared):
                # Home/calendar/year caches include fees and registration dates.
                # A cache outage must not misreport an already committed update.
                def invalidate_cache():
                    try:
                        cache.clear()
                    except Exception as exc:
                        print(f'CURATION_CACHE_WARNING: {type(exc).__name__}', file=sys.stderr)
                transaction.on_commit(invalidate_cache)
        return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--backup')
    args = parser.parse_args()
    sys.path.insert(0, os.getcwd())
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()
    raw = Path(args.manifest).read_bytes()
    receipt = apply_manifest(
        json.loads(raw), apply=args.apply, backup_path=args.backup,
        manifest_sha256=hashlib.sha256(raw).hexdigest(),
    )
    print('CURATION_RECEIPT_BEGIN')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    print('CURATION_RECEIPT_END')


if __name__ == '__main__':
    main()
