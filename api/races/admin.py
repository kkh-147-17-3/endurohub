import os
import uuid

from django.conf import settings
from django.contrib import admin
from django.db.models import IntegerField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin

from .forms import RaceAdminForm
from .models import DeviceToken, Race, RacePendingChange, Review


def _save_upload(f, subdir='races'):
    """Save an uploaded file and return the relative path."""
    ext = os.path.splitext(f.name)[1].lower()
    filename = f'{uuid.uuid4().hex}{ext}'
    rel_path = f'{subdir}/{filename}'
    abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, 'wb+') as dest:
        for chunk in f.chunks():
            dest.write(chunk)
    return rel_path


SORTABLE_SCRIPT = mark_safe('''<script>
(function() {
    function initGalleries() {
        document.querySelectorAll(".sortable-gallery:not([data-init])").forEach(function(el) {
            new Sortable(el, {animation: 150, ghostClass: "sortable-ghost"});
            el.dataset.init = "1";
        });
    }
    if (typeof Sortable !== "undefined") {
        initGalleries();
    } else if (!window._sortableLoading) {
        window._sortableLoading = true;
        var s = document.createElement("script");
        s.src = "https://cdn.jsdelivr.net/npm/sortablejs@1.15.6/Sortable.min.js";
        s.onload = initGalleries;
        document.head.appendChild(s);
    } else {
        var t = setInterval(function() {
            if (typeof Sortable !== "undefined") { clearInterval(t); initGalleries(); }
        }, 50);
    }
})();
</script>
<style>.sortable-ghost { opacity: 0.4; }</style>
''')


FILE_PREVIEW_SCRIPT = mark_safe('''<script>
document.addEventListener("DOMContentLoaded", function() {
    function setupPreview(inputId) {
        var input = document.getElementById(inputId);
        if (!input) return;
        var container = document.createElement("div");
        container.style.cssText = "display:flex; flex-wrap:wrap; gap:8px; margin-top:8px;";
        input.closest(".flex-col, .form-row, div").appendChild(container);
        input.addEventListener("change", function() {
            container.innerHTML = "";
            Array.from(this.files).forEach(function(file) {
                if (!file.type.startsWith("image/")) return;
                var reader = new FileReader();
                reader.onload = function(e) {
                    var img = document.createElement("img");
                    img.src = e.target.result;
                    img.style.cssText = "max-height:120px; border-radius:4px; border:2px solid #22c55e;";
                    container.appendChild(img);
                };
                reader.readAsDataURL(file);
            });
        });
    }
    setupPreview("id_image_file");
    setupPreview("id_course_image_files");
    setupPreview("id_giveaway_image_files");
});
</script>''')


@admin.register(Race)
class RaceAdmin(ModelAdmin):
    form = RaceAdminForm

    list_display = [
        'race_date', 'title_short', 'sport_badge', 'region',
        'status_badge', 'source_badge', 'verified_icon',
        'pending_changes_badge',
    ]
    list_filter = ['sport', 'region', 'source']
    search_fields = ['title', 'region']
    ordering = ['race_date']
    readonly_fields = [
        'view_count', 'verified_at', 'verified_by', 'created_at', 'updated_at',
        'image_preview', 'course_images_preview', 'giveaway_images_preview',
    ]

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
            'fields': ('image_preview', 'image_file', 'image_path', 'image_url'),
        }),
        ('코스 이미지', {
            'fields': ('course_images_preview', 'course_image_files'),
        }),
        ('사은품', {
            'fields': ('giveaways', 'giveaway_images_preview', 'giveaway_image_files'),
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

    # --- Image previews ---

    @admin.display(description='현재 이미지')
    def image_preview(self, obj):
        if not obj.pk:
            return format_html('이미지 없음{}', FILE_PREVIEW_SCRIPT)
        src = obj.image_src
        if src:
            return format_html(
                '<div>'
                '<img src="{}" style="max-height:200px; border-radius:8px;" />'
                '<label style="display:block; margin-top:8px; cursor:pointer;">'
                '<input type="checkbox" name="_delete_image" value="1" /> 이미지 삭제'
                '</label>'
                '</div>{}',
                src, FILE_PREVIEW_SCRIPT,
            )
        return format_html('이미지 없음{}', FILE_PREVIEW_SCRIPT)

    @admin.display(description='코스 이미지 미리보기')
    def course_images_preview(self, obj):
        return self._image_gallery(obj, 'course')

    @admin.display(description='기념품 이미지 미리보기')
    def giveaway_images_preview(self, obj):
        return self._image_gallery(obj, 'giveaway')

    def _image_gallery(self, obj, kind):
        if not obj.pk:
            return '-'

        if kind == 'course':
            external = list(obj.course_images or [])
            uploads = list(obj.course_image_uploads or [])
        else:
            external = list(obj.giveaway_images or [])
            uploads = list(obj.giveaway_image_uploads or [])

        if not external and not uploads:
            return '이미지 없음'

        gallery_id = f'gallery-{kind}'
        order_name = f'_{kind}_order'
        delete_name = f'_delete_{kind}_image'

        items = []
        # External images (from scraper etc.)
        for path in external:
            src = path if path.startswith(('http://', 'https://')) else f'{settings.STORAGE_URL}{path}'
            items.append(format_html(
                '<div style="cursor:grab; text-align:center; padding:8px; '
                'border:1px solid #e5e7eb; border-radius:8px; background:white;">'
                '<input type="hidden" name="{}" value="ext:{}">'
                '<img src="{}" style="max-height:150px; border-radius:4px;" />'
                '<br>'
                '<label style="font-size:12px; cursor:pointer; color:#ef4444;">'
                '<input type="checkbox" name="{}" value="ext:{}"> 삭제'
                '</label>'
                '</div>',
                order_name, path, src, delete_name, path,
            ))
        # Uploaded images (local paths)
        for path in uploads:
            src = f'{settings.STORAGE_URL}{path}'
            items.append(format_html(
                '<div style="cursor:grab; text-align:center; padding:8px; '
                'border:1px solid #e5e7eb; border-radius:8px; background:white;">'
                '<input type="hidden" name="{}" value="up:{}">'
                '<img src="{}" style="max-height:150px; border-radius:4px;" />'
                '<br>'
                '<label style="font-size:12px; cursor:pointer; color:#ef4444;">'
                '<input type="checkbox" name="{}" value="up:{}"> 삭제'
                '</label>'
                '</div>',
                order_name, path, src, delete_name, path,
            ))

        return format_html(
            '<div id="{}" class="sortable-gallery" '
            'style="display:flex; flex-wrap:wrap; gap:12px;">'
            '{}</div>'
            '<p style="font-size:12px; color:#6b7280; margin-top:8px;">'
            'drag &amp; drop으로 순서를 변경할 수 있습니다</p>'
            '{}',
            gallery_id,
            mark_safe(''.join(items)),
            SORTABLE_SCRIPT,
        )

    # --- File upload / delete / reorder handling ---

    def save_model(self, request, obj, form, change):
        # Main image: delete / upload
        if request.POST.get('_delete_image'):
            obj.image_path = None
        image_file = form.cleaned_data.get('image_file')
        if image_file:
            obj.image_path = _save_upload(image_file, 'races')

        # Course & giveaway images: reorder / delete / upload
        for kind in ('course', 'giveaway'):
            order = request.POST.getlist(f'_{kind}_order')
            deletes = set(request.POST.getlist(f'_delete_{kind}_image'))

            if order:
                # Gallery was rendered → use submitted order
                ordered = [p for p in order if p not in deletes]
            else:
                # No gallery (new race or no images) → keep existing
                ext = [f'ext:{p}' for p in (getattr(obj, f'{kind}_images') or [])]
                up = [f'up:{p}' for p in (getattr(obj, f'{kind}_image_uploads') or [])]
                ordered = [p for p in (ext + up) if p not in deletes]

            # Split back by source prefix
            new_ext = [p[4:] for p in ordered if p.startswith('ext:')]
            new_up = [p[3:] for p in ordered if p.startswith('up:')]

            # Append newly uploaded files
            new_files = request.FILES.getlist(f'{kind}_image_files')
            for f in new_files:
                new_up.append(_save_upload(f, f'races/{kind}'))

            setattr(obj, f'{kind}_images', new_ext or None)
            setattr(obj, f'{kind}_image_uploads', new_up or None)

        super().save_model(request, obj, form, change)

    # --- List display ---

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
