from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from .models import (
    EmailVerification,
    PendingSocialLogin,
    RaceRecord,
    SocialAccount,
    UserProfile,
)


@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    list_display = ['nickname', 'user', 'email_verified', 'email_updates_opt_in', 'created_at']
    list_filter = ['email_verified', 'email_updates_opt_in']
    search_fields = ['nickname', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(RaceRecord)
class RaceRecordAdmin(ModelAdmin):
    list_display = [
        'user', 'race_link', 'sport', 'distance',
        'duration_display', 'is_personal_best', 'is_public', 'record_date', 'created_at',
    ]
    list_filter = ['sport', 'is_personal_best', 'is_public', 'created_at']
    search_fields = ['user__email', 'name', 'race__title']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['race']

    @admin.display(description='대회명')
    def race_link(self, obj):
        if obj.race:
            url = reverse('admin:races_race_change', args=[obj.race_id])
            return format_html('<a href="{}">{}</a>', url, obj.race.title[:30])
        return obj.name or '(자유 입력)'

    @admin.display(description='기록', ordering='duration_seconds')
    def duration_display(self, obj):
        total = obj.duration_seconds or 0
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return f'{h:d}:{m:02d}:{s:02d}'


@admin.register(SocialAccount)
class SocialAccountAdmin(ModelAdmin):
    list_display = ['user', 'provider', 'email', 'created_at']
    list_filter = ['provider']
    search_fields = ['email', 'provider_uid', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EmailVerification)
class EmailVerificationAdmin(ModelAdmin):
    list_display = ['email', 'user', 'code', 'is_used', 'expires_at', 'created_at']
    list_filter = ['is_used']
    search_fields = ['email']
    readonly_fields = ['created_at']


@admin.register(PendingSocialLogin)
class PendingSocialLoginAdmin(ModelAdmin):
    list_display = ['provider', 'email', 'created_at', 'verification_expires_at']
    list_filter = ['provider']
    search_fields = ['email', 'provider_uid']
    readonly_fields = ['token', 'created_at', 'updated_at']
