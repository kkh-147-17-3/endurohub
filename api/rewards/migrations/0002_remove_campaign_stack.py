from django.db import migrations


REMOVED_MODELS = (
    'campaignentry',
    'campaignwinner',
    'giftcoupon',
    'rewardcampaign',
)


def remove_stale_content_types(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    ContentType.objects.filter(
        app_label='rewards',
        model__in=REMOVED_MODELS,
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('rewards', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(name='GiftCoupon'),
        migrations.DeleteModel(name='CampaignWinner'),
        migrations.DeleteModel(name='CampaignEntry'),
        migrations.DeleteModel(name='RewardCampaign'),
        migrations.RunPython(
            remove_stale_content_types,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
