from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class RewardCampaign(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_OPEN = 'open'
    STATUS_DRAWN = 'drawn'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_DRAFT, '준비 중'),
        (STATUS_OPEN, '응모 중'),
        (STATUS_DRAWN, '추첨 완료'),
        (STATUS_COMPLETED, '발송 완료'),
        (STATUS_CANCELLED, '취소'),
    ]

    name = models.CharField(max_length=120)
    prize_name = models.CharField(max_length=120, default='스타벅스 기프티콘')
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    winners_count = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )
    candidate_count = models.PositiveIntegerField(default=0)
    candidate_hash = models.CharField(max_length=64, blank=True, default='')
    draw_seed = models.CharField(max_length=64, blank=True, default='')
    drawn_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reward_campaigns'
        ordering = ['-starts_at', '-id']

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.starts_at and self.ends_at and self.starts_at >= self.ends_at:
            raise ValidationError({'ends_at': '종료 시각은 시작 시각보다 늦어야 합니다.'})
        if self.winners_count < 1:
            raise ValidationError({'winners_count': '당첨 인원은 1명 이상이어야 합니다.'})

    @property
    def is_accepting_entries(self):
        now = timezone.now()
        return (
            self.status == self.STATUS_OPEN
            and self.starts_at <= now <= self.ends_at
        )


class CampaignEntry(models.Model):
    campaign = models.ForeignKey(
        RewardCampaign,
        on_delete=models.CASCADE,
        related_name='entries',
    )
    review = models.ForeignKey(
        'races.Review',
        on_delete=models.SET_NULL,
        null=True,
        related_name='reward_entries',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reward_entries',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reward_campaign_entries'
        ordering = ['created_at', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['campaign', 'user'],
                name='uniq_reward_entry_per_member',
            ),
            models.UniqueConstraint(
                fields=['campaign', 'review'],
                name='uniq_reward_entry_per_review',
            ),
        ]

    def __str__(self):
        return f'{self.campaign} / {self.user}'


class CampaignWinner(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_SENDING = 'sending'
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, '발송 대기'),
        (STATUS_SENDING, '발송 중'),
        (STATUS_SENT, '발송 완료'),
        (STATUS_FAILED, '발송 실패'),
    ]

    campaign = models.ForeignKey(
        RewardCampaign,
        on_delete=models.CASCADE,
        related_name='winners',
    )
    entry = models.OneToOneField(
        CampaignEntry,
        on_delete=models.CASCADE,
        related_name='winner',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reward_wins',
    )
    email = models.EmailField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    email_attempts = models.PositiveSmallIntegerField(default=0)
    delivery_started_at = models.DateTimeField(null=True, blank=True)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reward_campaign_winners'
        ordering = ['created_at', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['campaign', 'user'],
                name='uniq_reward_winner_per_member',
            ),
        ]

    def __str__(self):
        return f'{self.campaign} / {self.email}'


class GiftCoupon(models.Model):
    STATUS_AVAILABLE = 'available'
    STATUS_ASSIGNED = 'assigned'
    STATUS_SENT = 'sent'
    STATUS_CHOICES = [
        (STATUS_AVAILABLE, '사용 가능'),
        (STATUS_ASSIGNED, '당첨자 할당'),
        (STATUS_SENT, '발송 완료'),
    ]

    campaign = models.ForeignKey(
        RewardCampaign,
        on_delete=models.CASCADE,
        related_name='coupons',
    )
    code = models.CharField(max_length=255, blank=True, default='')
    redemption_url = models.URLField(max_length=1000, blank=True, default='')
    image = models.ImageField(upload_to='rewards/coupons/', blank=True)
    expires_on = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_AVAILABLE,
    )
    winner = models.OneToOneField(
        CampaignWinner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coupon',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reward_gift_coupons'
        ordering = ['id']

    def __str__(self):
        return f'{self.campaign} / {self.masked_code}'

    def clean(self):
        super().clean()
        if not self.code and not self.redemption_url and not self.image:
            raise ValidationError('쿠폰 코드, 교환 링크, 이미지 중 하나는 입력해야 합니다.')
        if self.winner_id and self.winner.campaign_id != self.campaign_id:
            raise ValidationError({'winner': '같은 캠페인의 당첨자만 선택할 수 있습니다.'})

    @property
    def masked_code(self):
        if not self.code:
            return '(코드 없음)'
        if len(self.code) <= 6:
            return '*' * len(self.code)
        return f'{self.code[:3]}***{self.code[-3:]}'
