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
    _alter_existing_columns(schema_editor, 'jsonb')


def backwards(apps, schema_editor):
    _alter_existing_columns(schema_editor, 'json')


def _alter_existing_columns(schema_editor, target_type):
    """Legacy DB에 실제로 존재하는 JSON 컬럼만 변환한다.

    ``pending_changes``는 현재 모델에서는 컬럼이 아닌 reverse relation이고,
    ``posts``는 이 migration보다 나중에 생성될 수 있으므로 신규 DB에서는
    둘 다 존재하지 않을 수 있다.
    """
    connection = schema_editor.connection
    existing_tables = set(connection.introspection.table_names())

    for table, columns in JSON_COLUMNS.items():
        if table not in existing_tables:
            continue

        with connection.cursor() as cursor:
            descriptions = connection.introspection.get_table_description(cursor, table)
        existing_columns = {description.name for description in descriptions}

        for col in columns:
            if col not in existing_columns:
                continue

            quoted_table = schema_editor.quote_name(table)
            quoted_column = schema_editor.quote_name(col)
            schema_editor.execute(
                f'ALTER TABLE {quoted_table} ALTER COLUMN {quoted_column} '
                f'TYPE {target_type} USING {quoted_column}::{target_type}'
            )


class Migration(migrations.Migration):

    dependencies = [
        ('races', '0003_review_structured_fields'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
