from django.db import migrations


JSON_COLUMNS = {
    'races': [
        'distances', 'entry_fee', 'giveaways',
        'course_images', 'giveaway_images',
        'course_image_uploads', 'giveaway_image_uploads',
        'locked_fields', 'pending_changes',
    ],
    'device_tokens': [
        'subscribed_sports', 'subscribed_regions',
    ],
    'posts': [
        'images',
    ],
}


def forwards(apps, schema_editor):
    for table, columns in JSON_COLUMNS.items():
        for col in columns:
            schema_editor.execute(
                f'ALTER TABLE {table} ALTER COLUMN {col} TYPE jsonb USING {col}::jsonb'
            )


def backwards(apps, schema_editor):
    for table, columns in JSON_COLUMNS.items():
        for col in columns:
            schema_editor.execute(
                f'ALTER TABLE {table} ALTER COLUMN {col} TYPE json USING {col}::json'
            )


class Migration(migrations.Migration):

    dependencies = [
        ('races', '0003_review_structured_fields'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
