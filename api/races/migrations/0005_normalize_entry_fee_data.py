import json
import re

from django.db import migrations


def _fee_to_numeric_string(value):
    if value is None:
        return ''
    if isinstance(value, bool):
        return '1' if value else '0'
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value == int(value) else str(value)
    s = str(value).strip()
    digits = re.sub(r'[^\d]', '', s)
    return digits if digits else s


def _coerce_entry_fee(raw):
    """Match races.serializers.normalize_entry_fee_for_api (list | null)."""
    if raw is None:
        return None
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return [
            {'distance': str(k), 'fee': _fee_to_numeric_string(v)}
            for k, v in raw.items()
        ]
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return None
        if s.startswith('{') or s.startswith('['):
            try:
                parsed = json.loads(s)
                return _coerce_entry_fee(parsed)
            except json.JSONDecodeError:
                pass
        return [{'distance': '', 'fee': _fee_to_numeric_string(s)}]
    return None


def forwards(apps, schema_editor):
    Race = apps.get_model('races', 'Race')
    for race in Race.objects.exclude(entry_fee__isnull=True).iterator(chunk_size=200):
        fixed = _coerce_entry_fee(race.entry_fee)
        if fixed != race.entry_fee:
            race.entry_fee = fixed
            race.save(update_fields=['entry_fee'])


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('races', '0004_json_to_jsonb'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
