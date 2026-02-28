from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0003_post_user_postcomment_user_alter_post_password_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                'ALTER TABLE post_race DROP CONSTRAINT IF EXISTS post_race_pkey;',
                'ALTER TABLE post_race ADD COLUMN id BIGSERIAL PRIMARY KEY;',
                'CREATE UNIQUE INDEX IF NOT EXISTS post_race_post_id_race_id_uniq ON post_race (post_id, race_id);',
            ],
            reverse_sql=[
                'DROP INDEX IF EXISTS post_race_post_id_race_id_uniq;',
                'ALTER TABLE post_race DROP COLUMN id;',
                'ALTER TABLE post_race ADD PRIMARY KEY (post_id, race_id);',
            ],
        ),
    ]
