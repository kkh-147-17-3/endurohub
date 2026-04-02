from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_analytics_event'),
    ]

    operations = [
        migrations.AddField(
            model_name='analyticsevent',
            name='item_id',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='analyticsevent',
            name='item_type',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.AddField(
            model_name='analyticsevent',
            name='session_id',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AddIndex(
            model_name='analyticsevent',
            index=models.Index(fields=['user', 'event_type'], name='analytics_e_user_id_a1b2c3_idx'),
        ),
        migrations.AddIndex(
            model_name='analyticsevent',
            index=models.Index(fields=['item_type', 'item_id'], name='analytics_e_item_ty_d4e5f6_idx'),
        ),
        migrations.AddIndex(
            model_name='analyticsevent',
            index=models.Index(fields=['session_id'], name='analytics_e_session_g7h8i9_idx'),
        ),
    ]
