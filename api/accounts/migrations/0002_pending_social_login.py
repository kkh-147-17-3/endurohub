from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PendingSocialLogin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=64, unique=True)),
                ('provider', models.CharField(choices=[('kakao', '카카오'), ('naver', '네이버'), ('google', '구글')], max_length=20)),
                ('provider_uid', models.CharField(max_length=255)),
                ('email', models.EmailField(blank=True, default='', max_length=254)),
                ('access_token', models.TextField(blank=True, default='')),
                ('refresh_token', models.TextField(blank=True, default='')),
                ('extra_data', models.JSONField(blank=True, default=dict)),
                ('verification_code', models.CharField(blank=True, default='', max_length=6)),
                ('verification_expires_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'pending_social_logins',
                'unique_together': {('provider', 'provider_uid')},
            },
        ),
    ]
