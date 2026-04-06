from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    nickname = models.CharField(max_length=50, unique=True)
    profile_image = models.URLField(blank=True, default='')
    email_verified = models.BooleanField(default=False)
    email_updates_opt_in = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return self.nickname


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
