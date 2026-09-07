from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('races', '0013_review_user'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='review',
            index=models.Index(
                fields=['-created_at', '-id'],
                name='review_recent_idx',
            ),
        ),
    ]
