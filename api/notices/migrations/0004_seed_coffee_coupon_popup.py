from datetime import datetime, timezone
from pathlib import Path

from django.db import migrations


POPUP_NAME = '2026 커피 쿠폰 이벤트'
IMAGE_NAME = 'popups/2026-09/coffee-coupon-event-poster.png'


def seed_coffee_coupon_popup(apps, schema_editor):
    Popup = apps.get_model('notices', 'Popup')
    image_field = Popup._meta.get_field('image')
    storage = image_field.storage

    # 이전 배너가 같은 이름으로 남아 있어도 이번 원본으로 확실히 교체한다.
    # 배포 환경마다 MEDIA_ROOT가 별도 볼륨이므로 마이그레이션에서 복사해야 한다.
    if storage.exists(IMAGE_NAME):
        storage.delete(IMAGE_NAME)
    asset = Path(__file__).resolve().parent.parent / 'assets' / 'coffee-coupon-event-poster.png'
    with asset.open('rb') as source:
        saved_name = storage.save(IMAGE_NAME, source)

    Popup.objects.update_or_create(
        name=POPUP_NAME,
        defaults={
            'active': True,
            'starts_at': datetime(2026, 9, 2, 15, tzinfo=timezone.utc),
            'ends_at': datetime(2026, 9, 30, 15, tzinfo=timezone.utc),
            'placement': 'all',
            'priority': 100,
            'dismiss_days': 1,
            'notice_id': None,
            'image': saved_name,
            'image_width': 1003,
            'image_height': 1568,
            'image_alt': (
                '도전한 만큼, 커피 한 잔. 리뷰와 참가 기록을 남기면 '
                '스타벅스 카페 아메리카노 T를 증정하는 회원 이벤트'
            ),
            'cta_label': '이벤트 참여하기',
            'cta_url': '/notice/coffee-coupon-event',
        },
    )


def remove_coffee_coupon_popup(apps, schema_editor):
    Popup = apps.get_model('notices', 'Popup')
    image_field = Popup._meta.get_field('image')
    popup = Popup.objects.filter(name=POPUP_NAME, image=IMAGE_NAME).first()
    if popup is None:
        return

    popup.delete()
    if not Popup.objects.filter(image=IMAGE_NAME).exists():
        image_field.storage.delete(IMAGE_NAME)


class Migration(migrations.Migration):

    dependencies = [
        ('notices', '0003_popup_image'),
    ]

    operations = [
        migrations.RunPython(seed_coffee_coupon_popup, remove_coffee_coupon_popup),
    ]
