from django.contrib import admin
from django.db.models import IntegerField, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from .models import DeviceToken, Race, RacePendingChange, Review


@admin.register(Race)
class RaceAdmin(ModelAdmin):
    list_display = [
        'race_date', 'title_short', 'sport_badge', 'region',
        'status_badge', 'source_badge', 'verified_icon',
        'pending_changes_badge',
    ]
    list_filter = ['sport', 'region', 'source']
    search_fields = ['title', 'region']
    ordering = ['race_date']
    readonly_fields = ['view_count', 'verified_at', 'verified_by', 'created_at', 'updated_at']

    fieldsets = (
        ('기본 정보', {
            'fields': ('title', 'slug', 'sport', 'description'),
        }),
        ('일정', {
            'fields': (
                'race_date', 'race_end_date', 'start_time',
                'registration_start', 'registration_end', 'entry_fee',
            ),
        }),
        ('장소', {
            'fields': ('location', 'region', 'address', 'latitude', 'longitude'),
        }),
        ('종목/거리', {
            'fields': ('distances',),
        }),
        ('주최 정보', {
            'fields': ('organizer', 'organizer_contact', 'organizer_email'),
        }),
        ('대표 이미지', {
            'fields': ('image_path', 'image_url'),
        }),
        ('코스 이미지', {
            'fields': ('course_images', 'course_image_uploads'),
        }),
        ('사은품', {
            'fields': ('giveaways', 'giveaway_images', 'giveaway_image_uploads'),
        }),
        ('상태 관리', {
            'fields': ('status',),
            'description': '비워두면 날짜 기반으로 자동 계산됩니다.',
        }),
        ('링크', {
            'fields': ('official_url', 'recap_url', 'source', 'source_url', 'external_id'),
        }),
        ('크롤러 보호 설정', {
            'fields': (
                'auto_update_enabled', 'verified_at', 'verified_by', 'locked_fields',
            ),
            'description': '검증된 정보가 크롤러에 의해 덮어쓰기 되는 것을 방지합니다.',
        }),
        ('메타 정보', {
            'fields': ('view_count', 'created_at', 'updated_at'),
        }),
    )

    def get_queryset(self, request):
        from django.db.models import Count as DjangoCount
        pending_count = Coalesce(
            Subquery(
                RacePendingChange.objects.filter(
                    race_id=OuterRef('pk'),
                    status='pending',
                )
                .order_by()
                .values('race_id')
                .annotate(c=DjangoCount('id'))
                .values('c'),
                output_field=IntegerField(),
            ),
            Value(0),
        )
        return super().get_queryset(request).annotate(
            _pending_changes_count=pending_count,
        )

    @admin.display(description='대회명')
    def title_short(self, obj):
        return obj.title[:30] + ('...' if len(obj.title) > 30 else '')

    @admin.display(description='종목')
    def sport_badge(self, obj):
        colors = {
            'running': '#22c55e',
            'swimming': '#3b82f6',
            'cycling': '#f59e0b',
            'triathlon': '#ef4444',
            'trail_running': '#8b5cf6',
        }
        color = colors.get(obj.sport, '#6b7280')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; '
            'border-radius:4px; font-size:12px;">{}</span>',
            color, obj.sport_label,
        )

    @admin.display(description='상태')
    def status_badge(self, obj):
        status = obj.computed_status
        colors = {
            'upcoming': '#6b7280',
            'registration_open': '#22c55e',
            'registration_closed': '#f59e0b',
            'finished': '#ef4444',
        }
        color = colors.get(status, '#6b7280')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; '
            'border-radius:4px; font-size:12px;">{}</span>',
            color, obj.status_label,
        )

    @admin.display(description='출처')
    def source_badge(self, obj):
        label = '크롤링' if obj.source == 'crawl' else '수동'
        return format_html(
            '<span style="padding:2px 6px; border-radius:4px; '
            'font-size:11px; border:1px solid #d1d5db;">{}</span>',
            label,
        )

    @admin.display(description='검증', boolean=True)
    def verified_icon(self, obj):
        return obj.verified_at is not None

    @admin.display(description='대기')
    def pending_changes_badge(self, obj):
        count = getattr(obj, '_pending_changes_count', 0)
        if not count:
            return '-'
        return format_html(
            '<span style="background:#f59e0b; color:white; padding:2px 8px; '
            'border-radius:10px; font-size:12px;">{}</span>',
            count,
        )

    @admin.action(description='선택된 대회 검증 완료 처리')
    def verify_races(self, request, queryset):
        now = timezone.now()
        user = request.user.get_username() or 'admin'
        queryset.filter(verified_at__isnull=True).update(
            verified_at=now,
            verified_by=user,
        )

    @admin.action(description='선택된 대회 접수마감 처리')
    def close_registration(self, request, queryset):
        queryset.update(status='registration_closed')

    actions = ['verify_races', 'close_registration']


@admin.register(RacePendingChange)
class RacePendingChangeAdmin(ModelAdmin):
    list_display = [
        'race_link', 'field_label_display', 'status_badge',
        'source', 'created_at',
    ]
    list_filter = ['status', 'field_name']
    search_fields = ['race__title']
    ordering = ['-created_at']
    readonly_fields = [
        'race', 'field_name', 'old_value', 'new_value',
        'source', 'status', 'reviewed_by', 'reviewed_at',
    ]

    @admin.display(description='대회명')
    def race_link(self, obj):
        if obj.race:
            return format_html(
                '<a href="/admin/races/race/{}/change/">{}</a>',
                obj.race_id, obj.race.title[:30],
            )
        return '-'

    @admin.display(description='필드')
    def field_label_display(self, obj):
        return obj.field_label

    @admin.display(description='상태')
    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'approved': '#22c55e',
            'rejected': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; '
            'border-radius:4px; font-size:12px;">{}</span>',
            color, obj.status_display,
        )

    @admin.action(description='선택된 변경사항 일괄 승인')
    def bulk_approve(self, request, queryset):
        user = request.user.get_username() or 'admin'
        count = 0
        for change in queryset.filter(status='pending'):
            change.approve(reviewed_by=user)
            count += 1
        self.message_user(request, f'{count}건의 변경이 승인되었습니다.')

    @admin.action(description='선택된 변경사항 일괄 거부')
    def bulk_reject(self, request, queryset):
        user = request.user.get_username() or 'admin'
        count = 0
        for change in queryset.filter(status='pending'):
            change.reject(reviewed_by=user)
            count += 1
        self.message_user(request, f'{count}건의 변경이 거부되었습니다.')

    actions = ['bulk_approve', 'bulk_reject']


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ['race_link', 'display_nickname_col', 'rating_stars', 'comment_short', 'created_at']
    list_filter = ['rating']
    search_fields = ['race__title', 'nickname', 'comment']
    ordering = ['-created_at']
    readonly_fields = ['race', 'nickname', 'rating', 'ip_hash', 'created_at']

    fieldsets = (
        ('리뷰 정보', {
            'fields': ('race', 'nickname', 'rating', 'comment'),
        }),
    )

    @admin.display(description='대회명')
    def race_link(self, obj):
        if obj.race:
            return format_html(
                '<a href="/admin/races/race/{}/change/">{}</a>',
                obj.race_id, obj.race.title[:30],
            )
        return '-'

    @admin.display(description='닉네임')
    def display_nickname_col(self, obj):
        return obj.display_nickname

    @admin.display(description='평점')
    def rating_stars(self, obj):
        stars = '\u2605' * obj.rating + '\u2606' * (5 - obj.rating)
        if obj.rating >= 4:
            color = '#22c55e'
        elif obj.rating >= 3:
            color = '#f59e0b'
        else:
            color = '#ef4444'
        return format_html(
            '<span style="color:{};">{}</span>',
            color, stars,
        )

    @admin.display(description='내용')
    def comment_short(self, obj):
        return obj.comment[:40] + ('...' if len(obj.comment) > 40 else '')


@admin.register(DeviceToken)
class DeviceTokenAdmin(ModelAdmin):
    list_display = ['token_short', 'platform', 'subscribed_sports', 'subscribed_regions', 'created_at']
    list_filter = ['platform']
    search_fields = ['token']
    ordering = ['-created_at']

    @admin.display(description='토큰')
    def token_short(self, obj):
        return obj.token[:20] + '...'
