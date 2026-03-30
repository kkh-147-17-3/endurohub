from django.contrib import admin
from django.db.models import Count
from django.utils import timezone
from unfold.admin import ModelAdmin

from .models import AnalyticsEvent


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(ModelAdmin):
    list_display = ['event_type', 'properties_short', 'user', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['event_type', 'properties']
    ordering = ['-created_at']
    readonly_fields = ['event_type', 'properties', 'ip_hash', 'user', 'created_at']
    date_hierarchy = 'created_at'
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description='속성')
    def properties_short(self, obj):
        text = str(obj.properties)
        return text[:80] + ('...' if len(text) > 80 else '')
