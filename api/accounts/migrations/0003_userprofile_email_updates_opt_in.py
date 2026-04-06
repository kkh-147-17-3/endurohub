from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_pending_social_login'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='email_updates_opt_in',
            field=models.BooleanField(default=False),
        ),
    ]
