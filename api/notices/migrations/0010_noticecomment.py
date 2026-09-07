import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notices', '0009_restore_original_coffee_popup'),
    ]

    operations = [
        migrations.CreateModel(
            name='NoticeComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nickname', models.CharField(blank=True, max_length=50, null=True)),
                ('content', models.TextField()),
                ('password', models.CharField(blank=True, default='', max_length=255)),
                ('ip_hash', models.CharField(max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('notice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='notices.notice')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='notices.noticecomment')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notice_comments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'notice_comments',
                'ordering': ['created_at'],
            },
        ),
    ]
