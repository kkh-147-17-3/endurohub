from django.db import migrations


def add_id_to_legacy_join_table(apps, schema_editor):
    """구버전의 복합 PK 조인 테이블에만 surrogate PK를 추가한다.

    신규 설치에서는 0001이 이미 ``id``를 생성하므로 아무 작업도 하지 않는다.
    """
    connection = schema_editor.connection
    if 'post_race' not in connection.introspection.table_names():
        return

    with connection.cursor() as cursor:
        descriptions = connection.introspection.get_table_description(cursor, 'post_race')
    if any(description.name == 'id' for description in descriptions):
        return

    schema_editor.execute('ALTER TABLE post_race DROP CONSTRAINT IF EXISTS post_race_pkey')
    schema_editor.execute('ALTER TABLE post_race ADD COLUMN id BIGSERIAL PRIMARY KEY')
    schema_editor.execute(
        'CREATE UNIQUE INDEX IF NOT EXISTS post_race_post_id_race_id_uniq '
        'ON post_race (post_id, race_id)'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0003_post_user_postcomment_user_alter_post_password_and_more'),
    ]

    operations = [
        migrations.RunPython(add_id_to_legacy_join_table, migrations.RunPython.noop),
    ]
