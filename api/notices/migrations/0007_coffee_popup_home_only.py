from django.db import migrations


POPUP_NAME = '2026 커피 쿠폰 이벤트'


def set_home_only(apps, schema_editor):
    Popup = apps.get_model('notices', 'Popup')
    Popup.objects.filter(name=POPUP_NAME).update(placement='home')


def restore_all_pages(apps, schema_editor):
    Popup = apps.get_model('notices', 'Popup')
    Popup.objects.filter(name=POPUP_NAME).update(placement='all')


class Migration(migrations.Migration):

    dependencies = [
        ('notices', '0006_coffee_popup_dismiss_for_seven_days'),
    ]

    operations = [
        migrations.RunPython(set_home_only, restore_all_pages),
    ]
