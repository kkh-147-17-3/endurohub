from django.contrib import admin
from django.db import models
from unfold.admin import ModelAdmin
from unfold.contrib.forms.widgets import WysiwygWidget

from core.sanitize import sanitize_notice_html
from .models import Notice


@admin.register(Notice)
class NoticeAdmin(ModelAdmin):
    list_display = ['id', 'title_short', 'category', 'pinned', 'view_count', 'published_at']
    list_filter = ['category', 'pinned', 'published_at']
    search_fields = ['title', 'content', 'author']
    ordering = ['-pinned', '-published_at']
    readonly_fields = ['view_count', 'created_at', 'updated_at']

    formfield_overrides = {
        models.TextField: {'widget': WysiwygWidget},
    }

    fieldsets = (
        ('분류 / 고정', {
            'fields': ('category', 'pinned', 'author', 'published_at'),
        }),
        ('내용', {
            'fields': ('title', 'content'),
        }),
        ('첨부 / 연관', {
            'fields': ('attachments', 'related_race'),
            'description': '첨부파일은 [["파일명", "크기"], ...] 형태의 JSON 메타데이터입니다. 예: [["서울마라톤_일정.pdf", "284 KB"]]',
        }),
        ('메타 정보', {
            'fields': ('view_count', 'created_at', 'updated_at'),
        }),
    )

    def save_model(self, request, obj, form, change):
        obj.content = sanitize_notice_html(obj.content or '')
        super().save_model(request, obj, form, change)

    @admin.display(description='제목')
    def title_short(self, obj):
        return obj.title[:40] + ('...' if len(obj.title) > 40 else '')
