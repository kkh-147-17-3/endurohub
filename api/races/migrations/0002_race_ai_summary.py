from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('races', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='race',
            name='ai_summary',
            field=models.TextField(blank=True, null=True),
        ),
    ]
