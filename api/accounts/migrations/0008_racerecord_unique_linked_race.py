from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_racerecord_course_code_racerecord_is_personal_best_and_more'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='racerecord',
            constraint=models.UniqueConstraint(
                condition=models.Q(race__isnull=False),
                fields=('user', 'race'),
                name='uniq_linked_race_record_per_user',
            ),
        ),
    ]
