from pathlib import Path

from django.core.cache import cache
from django.db import migrations
from django.utils import timezone


POPUP_NAME = '2026 커피 쿠폰 이벤트'
IMAGE_NAME = 'popups/2026-09/coffee-coupon-event-poster-original.webp'
PREVIOUS_IMAGE_NAME = 'popups/2026-09/coffee-coupon-event-poster.webp'


def restore_original_popup(apps, schema_editor):
    Popup = apps.get_model('notices', 'Popup')
    image_field = Popup._meta.get_field('image')
    storage = image_field.storage
    asset = (
        Path(__file__).resolve().parent.parent
        / 'assets'
        / 'coffee-coupon-event-poster-original.webp'
    )

    if storage.exists(IMAGE_NAME):
        storage.delete(IMAGE_NAME)
    with asset.open('rb') as source:
        saved_name = storage.save(IMAGE_NAME, source)

    # 0008 replaced the administrator-uploaded collage with a different poster.
    # Point the seeded event back at the original design and preserve its ratio.
    Popup.objects.filter(name=POPUP_NAME).update(
        image=saved_name,
        image_width=1122,
        image_height=1402,
        updated_at=timezone.now(),
    )
    cache.delete('notices:popup:live:v1')


def restore_previous_popup(apps, schema_editor):
    Popup = apps.get_model('notices', 'Popup')
    image_field = Popup._meta.get_field('image')
    storage = image_field.storage

    Popup.objects.filter(name=POPUP_NAME, image=IMAGE_NAME).update(
        image=PREVIOUS_IMAGE_NAME,
        image_width=800,
        image_height=1251,
        updated_at=timezone.now(),
    )
    if not Popup.objects.filter(image=IMAGE_NAME).exists():
        storage.delete(IMAGE_NAME)


class Migration(migrations.Migration):

    dependencies = [
        ('notices', '0008_optimize_coffee_popup_image'),
    ]

    operations = [
        migrations.RunPython(restore_original_popup, restore_previous_popup),
    ]
