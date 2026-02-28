from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('races', '0002_race_ai_summary'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='completion_time',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='review',
            name='course_difficulty',
            field=models.CharField(
                blank=True,
                choices=[('easy', '쉬움'), ('normal', '보통'), ('hard', '어려움')],
                max_length=10,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='review',
            name='operation_satisfaction',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='review',
            name='recommendation_tags',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
