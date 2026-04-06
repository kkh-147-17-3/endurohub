from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import EmailVerification, PendingSocialLogin, SocialAccount, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    list_display = ['nickname', 'user', 'email_verified', 'email_updates_opt_in', 'created_at']
    list_filter = ['email_verified', 'email_updates_opt_in']
    search_fields = ['nickname', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


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
