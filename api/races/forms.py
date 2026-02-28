from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Race


# ---------------------------------------------------------------------------
# Custom widgets for JSON array fields
# ---------------------------------------------------------------------------

class TagInputWidget(forms.Widget):
    """Tag-style input for JSON array of strings.

    Renders clickable tag pills with remove buttons and a text input.
    Press Enter or comma to add a tag. Paste comma-separated values.
    Backspace on empty input removes the last tag.
    """

    def __init__(self, attrs=None, placeholder='입력 후 Enter'):
        self.placeholder = placeholder
        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        if value is None or value == '' or value == 'null':
            value = '[]'

        widget_id = f'tag-widget-{name}'

        html = format_html(
            '<input type="hidden" name="{}" id="id_{}" value="{}">'
            '<div id="{}" data-placeholder="{}"></div>',
            name, name, value, widget_id, self.placeholder,
        )

        js = '''<script>
(function() {
    var hidden = document.getElementById("id_''' + name + '''");
    var widget = document.getElementById("''' + widget_id + '''");
    var items;
    try { items = JSON.parse(hidden.value); } catch(e) { items = []; }
    if (!Array.isArray(items)) items = [];

    function sync() { hidden.value = JSON.stringify(items); }

    function addItem(val) {
        val = val.trim();
        if (val && items.indexOf(val) === -1) { items.push(val); sync(); }
    }

    function render() {
        widget.innerHTML = "";
        var wrap = document.createElement("div");
        wrap.style.cssText = "display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:8px 10px;border:1px solid #d1d5db;border-radius:8px;min-height:42px;background:white;cursor:text;";

        items.forEach(function(tag, idx) {
            var pill = document.createElement("span");
            pill.style.cssText = "display:inline-flex;align-items:center;gap:4px;background:#dbeafe;color:#1e40af;padding:4px 10px;border-radius:16px;font-size:13px;white-space:nowrap;";
            pill.textContent = tag;
            var btn = document.createElement("button");
            btn.type = "button";
            btn.textContent = "\\u00d7";
            btn.style.cssText = "background:none;border:none;color:#1e40af;cursor:pointer;font-size:16px;line-height:1;padding:0 0 0 2px;";
            btn.onclick = function() { items.splice(idx, 1); sync(); render(); };
            pill.appendChild(btn);
            wrap.appendChild(pill);
        });

        var inp = document.createElement("input");
        inp.type = "text";
        inp.placeholder = widget.dataset.placeholder || "";
        inp.style.cssText = "border:none;outline:none;flex:1;min-width:120px;padding:4px;font-size:13px;background:transparent;";

        inp.addEventListener("keydown", function(e) {
            if (e.key === "Enter" || e.key === ",") {
                e.preventDefault();
                var parts = this.value.split(/[,\\uFF0C]/).map(function(s){return s.trim();}).filter(Boolean);
                parts.forEach(addItem);
                render();
            }
            if (e.key === "Backspace" && !this.value && items.length) {
                items.pop(); sync(); render();
            }
        });

        inp.addEventListener("paste", function(e) {
            e.preventDefault();
            var text = (e.clipboardData || window.clipboardData).getData("text");
            var parts = text.split(/[,\\uFF0C\\n]/).map(function(s){return s.trim();}).filter(Boolean);
            parts.forEach(addItem);
            render();
        });

        wrap.appendChild(inp);
        wrap.addEventListener("click", function() { inp.focus(); });
        widget.appendChild(wrap);
    }

    render();
})();
</script>'''

        return mark_safe(str(html) + js)

    def value_from_datadict(self, data, files, name):
        return data.get(name)


class RepeaterWidget(forms.Widget):
    """Repeater-style input for JSON array of {distance, fee} objects.

    Renders a table with distance + fee columns, add/remove row buttons.
    """

    def render(self, name, value, attrs=None, renderer=None):
        if value is None or value == '' or value == 'null':
            value = '[]'

        widget_id = f'repeater-widget-{name}'

        html = format_html(
            '<input type="hidden" name="{}" id="id_{}" value="{}">'
            '<div id="{}"></div>',
            name, name, value, widget_id,
        )

        js = '''<script>
(function() {
    var hidden = document.getElementById("id_''' + name + '''");
    var widget = document.getElementById("''' + widget_id + '''");
    var items;
    try { items = JSON.parse(hidden.value); } catch(e) { items = []; }
    if (!Array.isArray(items)) items = [];
    items.forEach(function(item) { if (item.fee != null) item.fee = parseInt(item.fee, 10) || null; });

    function sync() { hidden.value = JSON.stringify(items); }

    function render() {
        widget.innerHTML = "";
        var box = document.createElement("div");
        box.style.cssText = "border:1px solid #d1d5db;border-radius:8px;overflow:hidden;background:white;";

        if (items.length > 0) {
            var hdr = document.createElement("div");
            hdr.style.cssText = "display:grid;grid-template-columns:1fr 1fr 36px;gap:8px;padding:8px 12px;background:#f9fafb;border-bottom:1px solid #e5e7eb;font-size:12px;color:#6b7280;font-weight:600;";
            hdr.innerHTML = "<span>\\uc885\\ubaa9</span><span>\\ucc38\\uac00\\ube44</span><span></span>";
            box.appendChild(hdr);
        }

        items.forEach(function(item, idx) {
            var row = document.createElement("div");
            row.style.cssText = "display:grid;grid-template-columns:1fr 1fr 36px;gap:8px;padding:8px 12px;align-items:center;" + (idx > 0 ? "border-top:1px solid #f3f4f6;" : "");

            var di = document.createElement("input");
            di.type = "text"; di.value = item.distance || "";
            di.placeholder = "\\uc608: 10km";
            di.style.cssText = "padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;width:100%;box-sizing:border-box;";
            di.oninput = function() { items[idx].distance = this.value; sync(); };

            var fi = document.createElement("input");
            fi.type = "number"; fi.value = item.fee != null ? item.fee : "";
            fi.placeholder = "\\uc608: 50000";
            fi.min = "0";
            fi.style.cssText = "padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;width:100%;box-sizing:border-box;";
            fi.oninput = function() { items[idx].fee = this.value ? parseInt(this.value, 10) : null; sync(); };

            var rb = document.createElement("button");
            rb.type = "button"; rb.textContent = "\\u00d7";
            rb.style.cssText = "width:28px;height:28px;background:#fef2f2;border:1px solid #fecaca;border-radius:6px;color:#ef4444;cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center;padding:0;";
            rb.onclick = function() { items.splice(idx, 1); sync(); render(); };

            row.appendChild(di); row.appendChild(fi); row.appendChild(rb);
            box.appendChild(row);
        });

        if (items.length === 0) {
            var empty = document.createElement("div");
            empty.style.cssText = "padding:16px;text-align:center;color:#9ca3af;font-size:13px;";
            empty.textContent = "\\ud56d\\ubaa9\\uc774 \\uc5c6\\uc2b5\\ub2c8\\ub2e4. \\uc544\\ub798 \\ubc84\\ud2bc\\uc744 \\ub20c\\ub7ec \\ucd94\\uac00\\ud558\\uc138\\uc694.";
            box.appendChild(empty);
        }

        widget.appendChild(box);

        var addBtn = document.createElement("button");
        addBtn.type = "button";
        addBtn.textContent = "+ \\ud589 \\ucd94\\uac00";
        addBtn.style.cssText = "margin-top:8px;padding:6px 16px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;color:#15803d;cursor:pointer;font-size:13px;";
        addBtn.onclick = function() { items.push({distance:"",fee:""}); sync(); render(); };
        widget.appendChild(addBtn);
    }

    render();
})();
</script>'''

        return mark_safe(str(html) + js)

    def value_from_datadict(self, data, files, name):
        return data.get(name)


class MultiFileInput(forms.ClearableFileInput):
    """FileInput that allows multiple file selection."""
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.attrs.setdefault('multiple', True)

    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):
            return files.getlist(name)
        return files.get(name)


class MultipleFileField(forms.FileField):
    """FileField that accepts multiple files from MultiFileInput.

    save_model reads from request.FILES.getlist() directly,
    so this field only needs to pass validation without breaking.
    """

    def clean(self, data, initial=None):
        if not data or data == []:
            if self.required:
                raise forms.ValidationError(self.error_messages['required'])
            return []
        if isinstance(data, (list, tuple)):
            single_clean = super().clean
            return [single_clean(d, initial) for d in data]
        return [super().clean(data, initial)]


SPORT_CHOICES = [
    ('', '---------'),
    ('running', '러닝'),
    ('swimming', '수영'),
    ('cycling', '사이클'),
    ('triathlon', '트라이애슬론'),
    ('trail_running', '트레일러닝'),
]

REGION_CHOICES = [
    ('', '---------'),
    ('서울', '서울'), ('경기', '경기'), ('인천', '인천'),
    ('강원', '강원'), ('충북', '충북'), ('충남', '충남'),
    ('대전', '대전'), ('세종', '세종'), ('전북', '전북'),
    ('전남', '전남'), ('광주', '광주'), ('대구', '대구'),
    ('경북', '경북'), ('경남', '경남'), ('부산', '부산'),
    ('울산', '울산'), ('제주', '제주'), ('기타', '기타'),
]

STATUS_CHOICES = [
    ('', '자동 (날짜 기반)'),
    ('upcoming', '예정'),
    ('registration_open', '접수중'),
    ('registration_closed', '접수마감'),
]

SOURCE_CHOICES = [
    ('manual', '수동 입력'),
    ('crawl', '크롤링'),
]

LOCKED_FIELD_CHOICES = [
    ('race_date', '대회일'),
    ('race_end_date', '대회종료일'),
    ('location', '장소'),
    ('entry_fee', '참가비'),
    ('registration_start', '접수시작일'),
    ('registration_end', '접수마감일'),
    ('distances', '종목'),
    ('title', '대회명'),
    ('official_url', '공식 URL'),
]


class RaceAdminForm(forms.ModelForm):
    image_file = forms.ImageField(
        required=False,
        label='대표 이미지 업로드',
        help_text='업로드하면 기존 image_path를 덮어씁니다.',
        widget=forms.FileInput(attrs={'accept': 'image/*'}),
    )
    course_image_files = MultipleFileField(
        required=False,
        label='코스 이미지 추가',
        help_text='여러 파일 선택 가능. 기존 이미지 뒤에 추가됩니다.',
        widget=MultiFileInput(attrs={'accept': 'image/*'}),
    )
    giveaway_image_files = MultipleFileField(
        required=False,
        label='기념품 이미지 추가',
        help_text='여러 파일 선택 가능. 기존 이미지 뒤에 추가됩니다.',
        widget=MultiFileInput(attrs={'accept': 'image/*'}),
    )

    class Meta:
        model = Race
        exclude = [
            'course_images', 'course_image_uploads',
            'giveaway_images', 'giveaway_image_uploads',
        ]
        labels = {
            'title': '대회명',
            'slug': '슬러그',
            'sport': '종목',
            'description': '설명',
            'race_date': '대회 시작일',
            'race_end_date': '대회 종료일',
            'start_time': '출발 시간',
            'registration_start': '접수 시작일',
            'registration_end': '접수 마감일',
            'entry_fee': '참가비',
            'location': '장소',
            'region': '지역',
            'address': '상세 주소',
            'latitude': '위도',
            'longitude': '경도',
            'distances': '거리',
            'organizer': '주최',
            'organizer_contact': '연락처',
            'organizer_email': '이메일',
            'image_path': '이미지 경로',
            'image_url': '이미지 URL',
            'giveaways': '사은품 목록',
            'status': '상태 오버라이드',
            'official_url': '공식 홈페이지',
            'recap_url': '대회 후기 URL',
            'source': '출처',
            'source_url': '출처 URL',
            'external_id': '외부 ID',
            'auto_update_enabled': '자동 업데이트 허용',
            'verified_at': '검증일시',
            'verified_by': '검증자',
            'locked_fields': '잠금 필드',
            'view_count': '조회수',
            'created_at': '등록일시',
            'updated_at': '수정일시',
        }
        help_texts = {
            'distances': '거리를 입력하고 Enter를 눌러 추가하세요. 쉼표로 여러 개를 한번에 입력할 수도 있습니다.',
            'status': '비워두면 날짜 기반으로 자동 계산됩니다. 수동으로 설정하면 날짜와 관계없이 선택한 상태가 적용됩니다.',
            'auto_update_enabled': '비활성화하면 크롤러가 이 대회 정보를 수정하지 않습니다.',
            'locked_fields': '선택한 필드는 크롤러가 수정할 수 없습니다.',
            'entry_fee': '종목별 참가비를 입력하세요. 행 추가 버튼으로 항목을 추가합니다.',
            'recap_url': '블로그 대회 후기 링크',
            'image_url': '외부 이미지 URL. 업로드 이미지가 없으면 이 URL이 사용됩니다.',
        }
        widgets = {
            'sport': forms.Select(choices=SPORT_CHOICES),
            'region': forms.Select(choices=REGION_CHOICES),
            'status': forms.Select(choices=STATUS_CHOICES),
            'source': forms.Select(choices=SOURCE_CHOICES),
            'description': forms.Textarea(attrs={'rows': 4}),
            'locked_fields': forms.CheckboxSelectMultiple(choices=LOCKED_FIELD_CHOICES),
            'distances': TagInputWidget(placeholder='거리 입력 후 Enter (예: 5km)'),
            'entry_fee': RepeaterWidget(),
            'giveaways': TagInputWidget(placeholder='사은품 입력 후 Enter (예: 완주메달)'),
        }
