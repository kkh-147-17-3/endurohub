from django.db import migrations


def backfill_item_fields(apps, schema_editor):
    AnalyticsEvent = apps.get_model('core', 'AnalyticsEvent')

    mapping = {
        'race_view':     ('race_id', 'race'),
        'review_submit': ('race_id', 'race'),
        'post_view':     ('post_id', 'post'),
        'post_create':   ('post_id', 'post'),
    }

    for event_type, (prop_key, item_type) in mapping.items():
        events = AnalyticsEvent.objects.filter(
            event_type=event_type,
            item_id='',
        )
        to_update = []
        for event in events.iterator(chunk_size=500):
            item_id = event.properties.get(prop_key)
            if item_id is not None:
                event.item_id = str(item_id)
                event.item_type = item_type
                to_update.append(event)
            if len(to_update) >= 500:
                AnalyticsEvent.objects.bulk_update(to_update, ['item_id', 'item_type'])
                to_update = []
        if to_update:
            AnalyticsEvent.objects.bulk_update(to_update, ['item_id', 'item_type'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_item_and_session_to_analytics'),
    ]

    operations = [
        migrations.RunPython(backfill_item_fields, migrations.RunPython.noop),
    ]
