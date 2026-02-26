from django import forms

from .models import Race


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
    course_image_files = forms.FileField(
        required=False,
        label='코스 이미지 추가',
        help_text='여러 파일 선택 가능. 기존 이미지 뒤에 추가됩니다.',
        widget=MultiFileInput(attrs={'accept': 'image/*'}),
    )
    giveaway_image_files = forms.FileField(
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
            'distances': '쉼표로 구분 (예: 5km, 10km, 42.195km). JSON 배열 형태로 저장됩니다.',
            'status': '비워두면 날짜 기반으로 자동 계산됩니다. 수동으로 설정하면 날짜와 관계없이 선택한 상태가 적용됩니다.',
            'auto_update_enabled': '비활성화하면 크롤러가 이 대회 정보를 수정하지 않습니다.',
            'locked_fields': '선택한 필드는 크롤러가 수정할 수 없습니다.',
            'entry_fee': 'JSON 형식 (예: [{"distance": "10km", "fee": "50000"}])',
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
        }
