from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    nickname = models.CharField(max_length=50, unique=True, null=True, blank=True)
    profile_image = models.URLField(blank=True, default='')
    email_verified = models.BooleanField(default=False)
    email_updates_opt_in = models.BooleanField(default=False)
    preferred_sports = models.JSONField(null=True, blank=True)
    preferred_regions = models.JSONField(null=True, blank=True)
    onboarding_completed = models.BooleanField(default=False)
    welcome_email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return self.nickname or f'user:{self.user_id}'

    @property
    def needs_onboarding(self):
        return (
            bool(self.nickname)
            and self.email_verified
            and not self.onboarding_completed
        )


class RaceRecord(models.Model):
    """A user's recent race result, collected during onboarding.

    Private by default (본인만 열람). Stored under the accounts app since it
    belongs to the user profile, not the public race catalogue.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='race_records',
    )
    # Optional link to a curated catalogue race. When set, this record is the
    # user's 완주 기록 for that race and powers the "logged" state in 내 시즌.
    # Free-form onboarding records leave this null.
    race = models.ForeignKey(
        'races.Race',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='records',
    )
    # Sport key matching races.constants.SPORT_LABELS (running, trail_running, ...)
    sport = models.CharField(max_length=20)
    # Distance / category — a preset label (e.g. '풀코스') or free-form custom text.
    distance = models.CharField(max_length=80)
    # Which course/종목 of the linked race was run (e.g. 'HM'); blank for free-form records.
    course_code = models.CharField(max_length=20, blank=True, default='')
    name = models.CharField(max_length=200, blank=True, default='')
    # Free-form race date as entered (e.g. '2025-03-16'); blank when skipped.
    record_date = models.CharField(max_length=20, blank=True, default='')
    duration_seconds = models.PositiveIntegerField()
    is_personal_best = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'race_records'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.sport}:{self.distance} ({self.duration_seconds}s)'


class SocialAccount(models.Model):
    PROVIDER_CHOICES = [
        ('kakao', '카카오'),
        ('naver', '네이버'),
        ('google', '구글'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='social_accounts',
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_uid = models.CharField(max_length=255)
    email = models.EmailField()
    access_token = models.TextField(blank=True, default='')
    refresh_token = models.TextField(blank=True, default='')
    extra_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'social_accounts'
        unique_together = [('provider', 'provider_uid')]

    def __str__(self):
        return f'{self.provider}:{self.provider_uid}'


class PendingSocialLogin(models.Model):
    PROVIDER_CHOICES = SocialAccount.PROVIDER_CHOICES

    token = models.CharField(max_length=64, unique=True)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_uid = models.CharField(max_length=255)
    email = models.EmailField(blank=True, default='')
    access_token = models.TextField(blank=True, default='')
    refresh_token = models.TextField(blank=True, default='')
    extra_data = models.JSONField(default=dict, blank=True)
    verification_code = models.CharField(max_length=6, blank=True, default='')
    verification_expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pending_social_logins'
        unique_together = [('provider', 'provider_uid')]

    def __str__(self):
        return f'pending:{self.provider}:{self.provider_uid}'


class EmailVerification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_verifications',
    )
    email = models.EmailField()
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'email_verifications'

    def __str__(self):
        return f'{self.email} ({self.code})'
