import os
import uuid

from django.conf import settings
from django.contrib import admin
from django.db.models import IntegerField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponseRedirect
from django.urls import reverse
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
    function setupPreview(inputId, galleryId) {
        var input = document.getElementById(inputId);
        if (!input) return;
        input.addEventListener("change", function() {
            // Remove old previews from this input
            var old = document.querySelectorAll(".file-preview-" + inputId);
            old.forEach(function(el) { el.remove(); });
            // Find gallery or create preview container
            var gallery = galleryId ? document.getElementById(galleryId) : null;
            Array.from(this.files).forEach(function(file, idx) {
                if (!file.type.startsWith("image/")) return;
                var reader = new FileReader();
                reader.onload = function(e) {
                    var div = document.createElement("div");
                    div.className = "file-preview-" + inputId;
                    div.dataset.fileIdx = idx;
                    div.style.cssText = "text-align:center; padding:8px; border:2px solid #22c55e; border-radius:8px; background:white; position:relative;";
                    var removeBtn = document.createElement("button");
                    removeBtn.type = "button";
                    removeBtn.textContent = "\\u00d7";
                    removeBtn.style.cssText = "position:absolute; top:2px; right:2px; width:22px; height:22px; border-radius:50%; border:none; background:#ef4444; color:white; font-size:14px; cursor:pointer; line-height:1;";
                    removeBtn.onclick = function() {
                        div.remove();
                        var dt = new DataTransfer();
                        var kept = document.querySelectorAll(".file-preview-" + inputId);
                        var keptIdx = new Set();
                        kept.forEach(function(p) { keptIdx.add(parseInt(p.dataset.fileIdx)); });
                        Array.from(input.files).forEach(function(f, i) {
                            if (keptIdx.has(i)) dt.items.add(f);
                        });
                        input.files = dt.files;
                        document.querySelectorAll(".file-preview-" + inputId).forEach(function(p, ni) { p.dataset.fileIdx = ni; });
                    };
                    var img = document.createElement("img");
                    img.src = e.target.result;
                    img.style.cssText = "max-height:150px; border-radius:4px;";
                    var label = document.createElement("span");
                    label.style.cssText = "display:block; font-size:11px; color:#22c55e; margin-top:4px;";
                    label.textContent = "\\uc0c8 \\ud30c\\uc77c";
                    div.appendChild(removeBtn);
                    div.appendChild(img);
                    div.appendChild(label);
                    if (gallery) {
                        gallery.appendChild(div);
                    } else {
                        var container = document.getElementById("preview-" + inputId);
                        if (!container) {
                            container = document.createElement("div");
                            container.id = "preview-" + inputId;
                            container.style.cssText = "display:flex; flex-wrap:wrap; gap:8px; margin-top:8px;";
                            var parent = input.closest(".flex-col, .form-row, div");
                            if (parent) parent.appendChild(container);
                        }
                        container.appendChild(div);
                    }
                };
                reader.readAsDataURL(file);
            });
        });
    }
    setupPreview("id_image_file", null);
    setupPreview("id_course_image_files", "gallery-course");
    setupPreview("id_giveaway_image_files", "gallery-giveaway");

    // --- Clipboard paste support ---
    var pasteTargets = [
        {inputId: "id_image_file", galleryId: null},
        {inputId: "id_course_image_files", galleryId: "gallery-course"},
        {inputId: "id_giveaway_image_files", galleryId: "gallery-giveaway"},
    ];
    var hoveredFieldset = null;

    // Track which fieldset (image section) the mouse is over
    pasteTargets.forEach(function(t) {
        var input = document.getElementById(t.inputId);
        if (!input) return;
        var fieldset = input.closest("fieldset, .module, div.form-row")?.closest("fieldset") || input.closest("fieldset, .module");
        if (!fieldset) return;
        t.fieldset = fieldset;
        fieldset.addEventListener("mouseenter", function() {
            hoveredFieldset = t;
            fieldset.style.outline = "2px dashed #f59e0b";
            fieldset.style.outlineOffset = "-2px";
        });
        fieldset.addEventListener("mouseleave", function() {
            fieldset.style.outline = "";
            fieldset.style.outlineOffset = "";
            if (hoveredFieldset === t) hoveredFieldset = null;
        });
    });

    document.addEventListener("paste", function(e) {
        var items = e.clipboardData && e.clipboardData.items;
        if (!items) return;

        var imageFile = null;
        for (var i = 0; i < items.length; i++) {
            if (items[i].type.indexOf("image") !== -1) {
                imageFile = items[i].getAsFile();
                break;
            }
        }
        if (!imageFile) return;

        // Determine target: hovered fieldset, or fall back to main image
        var target = hoveredFieldset || pasteTargets[0];
        var input = document.getElementById(target.inputId);
        if (!input) return;

        e.preventDefault();
        e.stopImmediatePropagation();

        // Give pasted file a proper name with timestamp
        var ext = imageFile.type.split("/")[1] || "png";
        var name = "pasted-" + Date.now() + "." + ext;
        var namedFile = new File([imageFile], name, {type: imageFile.type});

        // Merge with existing files
        var dt = new DataTransfer();
        if (input.files) {
            Array.from(input.files).forEach(function(f) { dt.items.add(f); });
        }
        dt.items.add(namedFile);
        input.files = dt.files;

        // Trigger change event to show preview
        input.dispatchEvent(new Event("change", {bubbles: true}));
    }, true);
});
</script>''')


# ---------------------------------------------------------------------------
# Custom list filters
# ---------------------------------------------------------------------------

class StatusFilter(admin.SimpleListFilter):
    """Filter races by computed status (handles both DB status and date-based auto-calculation)."""
    title = '상태'
    parameter_name = 'computed_status'

    def lookups(self, request, model_admin):
        return [
            ('upcoming', '예정'),
            ('registration_open', '접수중'),
            ('registration_closed', '접수마감'),
            ('finished', '종료'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.by_status(self.value())
        return queryset


class PendingStatusDefaultFilter(admin.SimpleListFilter):
    """Status filter for RacePendingChange that defaults to 'pending'."""
    title = '상태'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return [
            ('all', '전체'),
            ('pending', '대기중'),
            ('approved', '승인됨'),
            ('rejected', '거부됨'),
        ]

    def choices(self, changelist):
        """Override to set default selection to 'pending' instead of 'All'."""
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == str(lookup) or (self.value() is None and str(lookup) == 'pending'),
                'query_string': changelist.get_query_string({self.parameter_name: lookup}),
                'display': title,
            }

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'all':
            return queryset
        if value is None:
            # Default to pending
            return queryset.filter(status='pending')
        return queryset.filter(status=value)


# ---------------------------------------------------------------------------
# RaceAdmin
# ---------------------------------------------------------------------------

@admin.register(Race)
class RaceAdmin(ModelAdmin):
    form = RaceAdminForm

    list_display = [
        'race_date', 'title_short', 'sport_badge', 'region',
        'status_badge', 'source_badge', 'verified_icon',
        'pending_changes_badge',
    ]
    list_filter = ['sport', 'region', StatusFilter, 'source']
    search_fields = ['title', 'region']
    ordering = ['race_date']
    readonly_fields = [
        'view_count', 'verified_at', 'verified_by', 'created_at', 'updated_at',
        'image_preview', 'course_images_preview', 'giveaway_images_preview',
        'pending_changes_link',
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
                'pending_changes_link',
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

    # --- Pending changes link (readonly field in form) ---

    @admin.display(description='대기 중인 변경')
    def pending_changes_link(self, obj):
        if not obj.pk:
            return '-'
        count = getattr(obj, '_pending_changes_count', None)
        if count is None:
            count = RacePendingChange.objects.filter(race_id=obj.pk, status='pending').count()
        if not count:
            return '없음'
        url = reverse('admin:races_racependingchange_changelist')
        return format_html(
            '<a href="{}?race__id__exact={}&status=pending" '
            'style="color:#2563eb; text-decoration:underline;">'
            '{}건의 변경이 대기 중입니다</a>',
            url, obj.pk, count,
        )

    def response_change(self, request, obj):
        if '_continue' not in request.POST and '_addanother' not in request.POST:
            return HttpResponseRedirect(request.path)
        return super().response_change(request, obj)

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
                # Gallery was rendered -> use submitted order
                ordered = [p for p in order if p not in deletes]
            else:
                # No gallery (new race or no images) -> keep existing
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


# ---------------------------------------------------------------------------
# RacePendingChangeAdmin
# ---------------------------------------------------------------------------

@admin.register(RacePendingChange)
class RacePendingChangeAdmin(ModelAdmin):
    list_display = [
        'race_link', 'field_label_display', 'value_comparison',
        'status_badge', 'source', 'created_at',
    ]
    list_filter = [PendingStatusDefaultFilter, 'field_name']
    search_fields = ['race__title']
    ordering = ['-created_at']
    readonly_fields = [
        'race', 'field_name', 'old_value', 'new_value',
        'source', 'status', 'reviewed_by', 'reviewed_at',
        'value_comparison_detail',
    ]

    fieldsets = (
        ('변경 정보', {
            'fields': ('race', 'field_name', 'source', 'status'),
        }),
        ('값 비교', {
            'fields': ('value_comparison_detail',),
        }),
        ('검토 정보', {
            'fields': ('reviewed_by', 'reviewed_at'),
        }),
    )

    def get_model_count(self, request):
        """Show pending count as navigation badge (unfold feature)."""
        return RacePendingChange.objects.filter(status='pending').count() or None

    @admin.display(description='대회명')
    def race_link(self, obj):
        if obj.race:
            url = reverse('admin:races_race_change', args=[obj.race_id])
            return format_html(
                '<a href="{}">{}</a>',
                url, obj.race.title[:30],
            )
        return '-'

    @admin.display(description='필드')
    def field_label_display(self, obj):
        return obj.field_label

    @admin.display(description='변경 내용')
    def value_comparison(self, obj):
        old_val = (obj.old_value or '-')[:40]
        new_val = (obj.new_value or '-')[:40]
        return format_html(
            '<span style="color:#ef4444; text-decoration:line-through; font-size:12px;">{}</span>'
            ' &rarr; '
            '<span style="color:#22c55e; font-size:12px;">{}</span>',
            old_val, new_val,
        )

    @admin.display(description='값 비교 (상세)')
    def value_comparison_detail(self, obj):
        old_val = obj.old_value or '(없음)'
        new_val = obj.new_value or '(없음)'
        return format_html(
            '<div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">'
            '<div>'
            '<h4 style="margin:0 0 8px 0; color:#6b7280; font-size:13px;">기존 값</h4>'
            '<div style="padding:12px; background:#fef2f2; border:1px solid #fecaca; '
            'border-radius:8px; white-space:pre-wrap; font-size:13px; word-break:break-all;">{}</div>'
            '</div>'
            '<div>'
            '<h4 style="margin:0 0 8px 0; color:#6b7280; font-size:13px;">새 값</h4>'
            '<div style="padding:12px; background:#f0fdf4; border:1px solid #bbf7d0; '
            'border-radius:8px; white-space:pre-wrap; font-size:13px; word-break:break-all;">{}</div>'
            '</div>'
            '</div>',
            old_val, new_val,
        )

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


# ---------------------------------------------------------------------------
# ReviewAdmin
# ---------------------------------------------------------------------------

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
            url = reverse('admin:races_race_change', args=[obj.race_id])
            return format_html(
                '<a href="{}">{}</a>',
                url, obj.race.title[:30],
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


# ---------------------------------------------------------------------------
# DeviceTokenAdmin
# ---------------------------------------------------------------------------

@admin.register(DeviceToken)
class DeviceTokenAdmin(ModelAdmin):
    list_display = ['token_short', 'platform', 'subscribed_sports', 'subscribed_regions', 'created_at']
    list_filter = ['platform']
    search_fields = ['token']
    ordering = ['-created_at']

    @admin.display(description='토큰')
    def token_short(self, obj):
        return obj.token[:20] + '...'
