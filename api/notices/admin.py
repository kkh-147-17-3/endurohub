from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.contrib.forms.widgets import WysiwygWidget

from core.sanitize import sanitize_notice_html
from .models import Notice, Popup, invalidate_popup_cache


@admin.register(Notice)
class NoticeAdmin(ModelAdmin):
    list_display = ['id', 'title_short', 'category', 'pinned', 'view_count', 'published_at']
    list_filter = ['category', 'pinned', 'published_at']
    search_fields = ['title', 'slug', 'content', 'author']
    ordering = ['-pinned', '-published_at']
    readonly_fields = ['view_count', 'created_at', 'updated_at']

    formfield_overrides = {
        models.TextField: {'widget': WysiwygWidget},
    }

    fieldsets = (
        ('분류 / 고정', {
            'fields': ('category', 'slug', 'pinned', 'author', 'published_at'),
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


@admin.register(Popup)
class PopupAdmin(ModelAdmin):
    list_display = ['name', 'live_badge', 'thumb', 'placement', 'starts_at', 'ends_at', 'notice', 'priority']
    list_filter = ['active', 'placement']
    search_fields = ['name', 'image_alt']
    ordering = ['-priority', '-starts_at']
    readonly_fields = ['preview', 'created_at', 'updated_at']
    autocomplete_fields = ['notice']

    fieldsets = (
        ('게시', {
            'fields': ('name', 'active', 'starts_at', 'ends_at', 'placement', 'priority', 'dismiss_days'),
            'description': (
                '게시 체크 + 시작~종료 사이일 때만 팝업이 뜹니다. 종료를 비우면 무기한입니다. '
                '"다시 보지 않기(일)"은 방문자가 팝업을 닫고 다시 보지 않기를 선택했을 때 숨겨지는 기간입니다.'
            ),
        }),
        ('내용 (이미지)', {
            'fields': ('image', 'image_alt', 'preview'),
            'description': (
                '팝업 내용은 이미지 한 장입니다. 모달 폭이 640px 이므로 가로 1280px 안팎(2배수)에 '
                '세로로 긴 비율을 권합니다. 모바일에서는 화면 폭에 맞춰 줄어드니 이미지 안 글씨가 '
                '너무 작지 않은지 확인해 주세요.'
            ),
        }),
        ('이동 링크', {
            'fields': ('cta_label', 'cta_url', 'notice'),
            'description': (
                '이미지를 누르거나 아래 버튼을 누르면 이 링크로 이동합니다. 링크를 비우면 연결된 '
                '공지사항 상세로 갑니다. 공지사항을 연결하면 그 상세 페이지 상단에도 같은 이미지가 붙습니다.'
            ),
        }),
        ('메타 정보', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description='상태', boolean=True)
    def live_badge(self, obj):
        return obj.is_live

    @admin.display(description='이미지')
    def thumb(self, obj):
        if not obj.image:
            return '—'
        return format_html(
            '<img src="{}" style="height:44px; width:auto; border-radius:4px;" alt="" />',
            obj.image.url,
        )

    @admin.display(description='미리보기 (모달 폭 640px 기준)')
    def preview(self, obj):
        if not obj.image:
            return '이미지를 올리고 저장하면 여기에 표시됩니다.'
        return format_html(
            '<div style="max-width:640px; border:1px solid rgba(128,128,128,.35); border-radius:6px; overflow:hidden;">'
            '<img src="{}" style="display:block; width:100%; height:auto;" alt="" />'
            '<div style="height:66px; display:flex; align-items:center; justify-content:center; '
            'background:#1f9d55; color:#fff; font-weight:700; font-size:20px;">{}</div>'
            '</div>',
            obj.image.url,
            obj.cta_label or '(버튼 없음 — 이미지 클릭만)',
        )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        invalidate_popup_cache()
