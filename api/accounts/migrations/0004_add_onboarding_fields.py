from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_userprofile_email_updates_opt_in'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='preferred_sports',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='preferred_regions',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='onboarding_completed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='welcome_email_sent',
            field=models.BooleanField(default=False),
        ),
    ]
