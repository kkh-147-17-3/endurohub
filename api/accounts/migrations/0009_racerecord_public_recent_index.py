from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_racerecord_unique_linked_race'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='racerecord',
            index=models.Index(
                condition=models.Q(is_public=True, race__isnull=False),
                fields=['-created_at', '-id'],
                name='rr_public_recent_idx',
            ),
        ),
    ]
