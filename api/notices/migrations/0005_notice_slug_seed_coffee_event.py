from datetime import datetime, timezone

from django.db import migrations, models


SLUG = 'coffee-coupon-event'
POPUP_NAME = '2026 커피 쿠폰 이벤트'


def seed_coffee_event_notice(apps, schema_editor):
    Notice = apps.get_model('notices', 'Notice')
    Popup = apps.get_model('notices', 'Popup')

    notice, _ = Notice.objects.update_or_create(
        slug=SLUG,
        defaults={
            'category': 'event',
            'title': '스타벅스 카페 아메리카노 T 이벤트',
            'author': 'ENDUROHUB 운영팀',
            'published_at': datetime(2026, 9, 3, tzinfo=timezone.utc),
            'content': '',
            'pinned': False,
        },
    )
    Popup.objects.filter(name=POPUP_NAME).update(notice_id=notice.pk)


def remove_coffee_event_notice(apps, schema_editor):
    Notice = apps.get_model('notices', 'Notice')
    Popup = apps.get_model('notices', 'Popup')

    Popup.objects.filter(name=POPUP_NAME, notice__slug=SLUG).update(notice_id=None)
    Notice.objects.filter(slug=SLUG).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('notices', '0004_seed_coffee_coupon_popup'),
    ]

    operations = [
        migrations.AddField(
            model_name='notice',
            name='slug',
            field=models.SlugField(blank=True, default=None, max_length=100, null=True, unique=True),
        ),
        migrations.RunPython(seed_coffee_event_notice, remove_coffee_event_notice),
    ]
