from django.contrib import admin
from django.db import models
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.forms.widgets import WysiwygWidget

from core.sanitize import sanitize_notice_html
from .models import Notice, Popup, PopupStep, invalidate_popup_cache


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


class PopupStepInline(TabularInline):
    model = PopupStep
    extra = 3
    fields = ('order', 'title', 'description')
    ordering = ('order', 'id')


@admin.register(Popup)
class PopupAdmin(ModelAdmin):
    list_display = ['name', 'live_badge', 'placement', 'starts_at', 'ends_at', 'notice', 'priority']
    list_filter = ['active', 'placement']
    search_fields = ['name', 'headline', 'subtitle']
    ordering = ['-priority', '-starts_at']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['notice']
    inlines = [PopupStepInline]

    fieldsets = (
        ('게시', {
            'fields': ('name', 'active', 'starts_at', 'ends_at', 'placement', 'priority', 'dismiss_days'),
            'description': (
                '게시 체크 + 시작~종료 사이일 때만 팝업이 뜹니다. 종료를 비우면 무기한입니다. '
                '"다시 보지 않기(일)"은 방문자가 팝업을 닫고 다시 보지 않기를 선택했을 때 숨겨지는 기간입니다.'
            ),
        }),
        ('상세 페이지 연결', {
            'fields': ('notice', 'cta_label', 'cta_url'),
            'description': (
                '상세 페이지는 공지사항으로 만듭니다. 이벤트 카테고리로 공지사항을 하나 등록한 뒤 '
                '여기에 연결하면, 팝업의 버튼이 그 공지 상세로 이어지고 상세 상단에도 같은 배너가 붙습니다.'
            ),
        }),
        ('배너 상단', {
            'fields': ('tag', 'headline', 'headline_accent', 'subtitle'),
            'description': (
                '헤드라인은 줄바꿈이 그대로 반영됩니다. "헤드라인 강조 단어"에 적은 낱말은 '
                '헤드라인 안에서 초록색으로 표시됩니다.'
            ),
        }),
        ('배너 메타 (3칸)', {
            'fields': ('meta_period', 'meta_winners', 'show_dday'),
            'description': '예) 기간 "08·01 — 08·31", 당첨 "30". D-day 는 게시 종료일에서 자동 계산됩니다.',
        }),
        ('경품', {
            'fields': ('prize_image', 'prize_name', 'prize_count', 'prize_note'),
        }),
        ('하단 세부 안내', {
            'fields': ('fine_period', 'fine_announce', 'fine_note'),
        }),
        ('메타 정보', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description='상태', boolean=True)
    def live_badge(self, obj):
        return obj.is_live

    def save_related(self, request, form, formsets, change):
        # 인라인(참여 단계)까지 저장된 뒤 한 번 더 비운다 — 단계만 고쳤을 때도
        # 캐시된 페이로드가 남지 않도록.
        super().save_related(request, form, formsets, change)
        invalidate_popup_cache()
