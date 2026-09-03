from django.db import migrations
from django.utils import timezone


POPUP_NAME = '2026 커피 쿠폰 이벤트'


def set_seven_day_dismissal(apps, schema_editor):
    Popup = apps.get_model('notices', 'Popup')
    # updated_at also changes the frontend dismissal key, clearing any period that
    # was previously stored automatically merely by following the CTA.
    Popup.objects.filter(name=POPUP_NAME).update(
        dismiss_days=7,
        updated_at=timezone.now(),
    )


def restore_one_day_dismissal(apps, schema_editor):
    Popup = apps.get_model('notices', 'Popup')
    Popup.objects.filter(name=POPUP_NAME).update(
        dismiss_days=1,
        updated_at=timezone.now(),
    )


class Migration(migrations.Migration):

    dependencies = [
        ('notices', '0005_notice_slug_seed_coffee_event'),
    ]

    operations = [
        migrations.RunPython(set_seven_day_dismissal, restore_one_day_dismissal),
    ]
