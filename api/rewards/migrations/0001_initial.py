import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('races', '0013_review_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='RewardCampaign',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('prize_name', models.CharField(default='스타벅스 기프티콘', max_length=120)),
                ('starts_at', models.DateTimeField()),
                ('ends_at', models.DateTimeField()),
                ('winners_count', models.PositiveSmallIntegerField(default=1)),
                ('status', models.CharField(choices=[('draft', '준비 중'), ('open', '응모 중'), ('drawn', '추첨 완료'), ('completed', '발송 완료'), ('cancelled', '취소')], default='draft', max_length=20)),
                ('candidate_count', models.PositiveIntegerField(default=0)),
                ('candidate_hash', models.CharField(blank=True, default='', max_length=64)),
                ('draw_seed', models.CharField(blank=True, default='', max_length=64)),
                ('drawn_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'reward_campaigns',
                'ordering': ['-starts_at', '-id'],
            },
        ),
        migrations.CreateModel(
            name='CampaignEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='rewards.rewardcampaign')),
                ('review', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reward_entries', to='races.review')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reward_entries', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'reward_campaign_entries',
                'ordering': ['created_at', 'id'],
            },
        ),
        migrations.CreateModel(
            name='CampaignWinner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('status', models.CharField(choices=[('pending', '발송 대기'), ('sending', '발송 중'), ('sent', '발송 완료'), ('failed', '발송 실패')], default='pending', max_length=20)),
                ('email_attempts', models.PositiveSmallIntegerField(default=0)),
                ('delivery_started_at', models.DateTimeField(blank=True, null=True)),
                ('email_sent_at', models.DateTimeField(blank=True, null=True)),
                ('last_error', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='winners', to='rewards.rewardcampaign')),
                ('entry', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='winner', to='rewards.campaignentry')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reward_wins', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'reward_campaign_winners',
                'ordering': ['created_at', 'id'],
            },
        ),
        migrations.CreateModel(
            name='GiftCoupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, default='', max_length=255)),
                ('redemption_url', models.URLField(blank=True, default='', max_length=1000)),
                ('image', models.ImageField(blank=True, upload_to='rewards/coupons/')),
                ('expires_on', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('available', '사용 가능'), ('assigned', '당첨자 할당'), ('sent', '발송 완료')], default='available', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coupons', to='rewards.rewardcampaign')),
                ('winner', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='coupon', to='rewards.campaignwinner')),
            ],
            options={
                'db_table': 'reward_gift_coupons',
                'ordering': ['id'],
            },
        ),
        migrations.AddConstraint(
            model_name='campaignentry',
            constraint=models.UniqueConstraint(fields=('campaign', 'user'), name='uniq_reward_entry_per_member'),
        ),
        migrations.AddConstraint(
            model_name='campaignentry',
            constraint=models.UniqueConstraint(fields=('campaign', 'review'), name='uniq_reward_entry_per_review'),
        ),
        migrations.AddConstraint(
            model_name='campaignwinner',
            constraint=models.UniqueConstraint(fields=('campaign', 'user'), name='uniq_reward_winner_per_member'),
        ),
    ]
