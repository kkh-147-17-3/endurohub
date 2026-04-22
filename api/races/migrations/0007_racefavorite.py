from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('races', '0006_distances_objects_registration_phases'),
    ]

    operations = [
        migrations.CreateModel(
            name='RaceFavorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('race', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to='races.race')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='race_favorites', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'race_favorites',
                'indexes': [models.Index(fields=['user', '-created_at'], name='race_favori_user_id_e8a1f2_idx')],
                'unique_together': {('user', 'race')},
            },
        ),
    ]
