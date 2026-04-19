"""Convert distances from string array to object array, merge entry_fee into
distances, add registration_phases field, and remove entry_fee field."""

import re

from django.db import migrations, models


def _parse_distance_km(s):
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    km_match = re.search(r'([\d,]+\.?\d*)\s*(?:km|K)', s, re.IGNORECASE)
    if km_match:
        try:
            return float(km_match.group(1).replace(',', ''))
        except (ValueError, TypeError):
            return None
    m_match = re.search(r'([\d,]+\.?\d*)\s*m\b', s, re.IGNORECASE)
    if m_match:
        try:
            return float(m_match.group(1).replace(',', '')) / 1000.0
        except (ValueError, TypeError):
            return None
    bare_match = re.match(r'^([\d,]+\.?\d*)$', s)
    if bare_match:
        try:
            return float(bare_match.group(1).replace(',', ''))
        except (ValueError, TypeError):
            return None
    return None


def forwards(apps, schema_editor):
    Race = apps.get_model('races', 'Race')
    for race in Race.objects.exclude(distances__isnull=True).iterator(chunk_size=200):
        dists = race.distances
        if not isinstance(dists, list) or not dists:
            continue

        # Already migrated (first item is a dict)
        if isinstance(dists[0], dict):
            continue

        # Build fee lookup from entry_fee
        fee_map = {}
        if race.entry_fee and isinstance(race.entry_fee, list):
            for ef in race.entry_fee:
                if isinstance(ef, dict) and ef.get('distance') and ef.get('fee'):
                    fee_map[ef['distance']] = ef['fee']

        new_distances = []
        for name in dists:
            if not isinstance(name, str):
                continue
            item = {'name': name}
            km = _parse_distance_km(name)
            if km is not None:
                item['distance_meter'] = round(km * 1000)
            # Try to match fee from entry_fee
            fee = fee_map.get(name)
            if fee is not None:
                try:
                    item['fee'] = int(str(fee).replace(',', '').strip())
                except (ValueError, TypeError):
                    pass
            new_distances.append(item)

        race.distances = new_distances
        race.save(update_fields=['distances'])


def backwards(apps, schema_editor):
    Race = apps.get_model('races', 'Race')
    for race in Race.objects.exclude(distances__isnull=True).iterator(chunk_size=200):
        dists = race.distances
        if not isinstance(dists, list) or not dists:
            continue
        if not isinstance(dists[0], dict):
            continue
        race.distances = [d.get('name', '') for d in dists if isinstance(d, dict)]
        race.save(update_fields=['distances'])


class Migration(migrations.Migration):

    dependencies = [
        ('races', '0005_normalize_entry_fee_data'),
    ]

    operations = [
        # Add registration_phases field
        migrations.AddField(
            model_name='race',
            name='registration_phases',
            field=models.JSONField(blank=True, null=True),
        ),
        # Convert distances data from string array to object array,
        # merging entry_fee data into distances
        migrations.RunPython(forwards, backwards),
        # Remove entry_fee field
        migrations.RemoveField(
            model_name='race',
            name='entry_fee',
        ),
    ]
