from pathlib import Path

from django.db import migrations
from django.utils import timezone


POPUP_NAME = '2026 커피 쿠폰 이벤트'
OLD_IMAGE_NAME = 'popups/2026-09/coffee-coupon-event-poster.png'
NEW_IMAGE_NAME = 'popups/2026-09/coffee-coupon-event-poster.webp'


def use_optimized_image(apps, schema_editor):
    Popup = apps.get_model('notices', 'Popup')
    image_field = Popup._meta.get_field('image')
    storage = image_field.storage
    asset = (
        Path(__file__).resolve().parent.parent
        / 'assets'
        / 'coffee-coupon-event-poster.webp'
    )

    if storage.exists(NEW_IMAGE_NAME):
        storage.delete(NEW_IMAGE_NAME)
    with asset.open('rb') as source:
        saved_name = storage.save(NEW_IMAGE_NAME, source)

    Popup.objects.filter(name=POPUP_NAME).update(
        image=saved_name,
        image_width=800,
        image_height=1251,
        updated_at=timezone.now(),
    )


def restore_original_image(apps, schema_editor):
    Popup = apps.get_model('notices', 'Popup')
    image_field = Popup._meta.get_field('image')
    storage = image_field.storage

    Popup.objects.filter(name=POPUP_NAME, image=NEW_IMAGE_NAME).update(
        image=OLD_IMAGE_NAME,
        image_width=1003,
        image_height=1568,
        updated_at=timezone.now(),
    )
    if not Popup.objects.filter(image=NEW_IMAGE_NAME).exists():
        storage.delete(NEW_IMAGE_NAME)


class Migration(migrations.Migration):

    dependencies = [
        ('notices', '0007_coffee_popup_home_only'),
    ]

    operations = [
        migrations.RunPython(use_optimized_image, restore_original_image),
    ]
