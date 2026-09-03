from django.core.cache import cache
from django.db import models
from django.utils import timezone


class Notice(models.Model):
    CATEGORY_CHOICES = [
        ('urgent', '긴급'),
        ('notice', '공지'),
        ('racenews', '대회소식'),
        ('event', '이벤트'),
    ]

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='notice')
    slug = models.SlugField(max_length=100, unique=True, null=True, blank=True, default=None)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, default='')
    author = models.CharField(max_length=50, default='ENDUROHUB 운영팀')
    pinned = models.BooleanField(default=False)
    published_at = models.DateTimeField(default=timezone.now)
    view_count = models.PositiveIntegerField(default=0)
    attachments = models.JSONField(null=True, blank=True)
    related_race = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        db_table = 'notices'
        ordering = ['-pinned', '-published_at']

    def __str__(self):
        return self.title

    @property
    def is_urgent(self):
        return self.category == 'urgent'

    def increment_view_count(self):
        Notice.objects.filter(pk=self.pk).update(
            view_count=models.F('view_count') + 1
        )


POPUP_CACHE_KEY = 'notices:popup:live:v1'


def invalidate_popup_cache():
    cache.delete(POPUP_CACHE_KEY)


class Popup(models.Model):
    """팝업 배너 — 이미지 한 장과 게시기간을 관리자에서 관리한다.

    배너 내용은 통째로 이미지다. 디자인은 이미지 안에서 끝내고, 코드가
    관여하는 건 "언제 띄우고"(게시기간·노출 위치) "어디로 보내는지"(링크)
    둘뿐이다. 이미지를 눌러도, 아래 버튼을 눌러도 같은 곳으로 간다.

    링크를 비워 두면 연결된 공지(notice) 상세로 보낸다. 같은 이미지를 그
    공지 상세 상단에도 히어로로 붙인다.
    """

    PLACEMENT_CHOICES = [
        ('home', '홈에서만'),
        ('all', '모든 페이지'),
    ]

    name = models.CharField('관리용 이름', max_length=100)
    active = models.BooleanField('게시', default=False)
    starts_at = models.DateTimeField('게시 시작', default=timezone.now)
    ends_at = models.DateTimeField('게시 종료', null=True, blank=True)
    placement = models.CharField('노출 위치', max_length=10, choices=PLACEMENT_CHOICES, default='home')
    priority = models.IntegerField('우선순위', default=0)
    dismiss_days = models.PositiveSmallIntegerField('다시 보지 않기(일)', default=7)

    notice = models.ForeignKey(
        Notice, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='popups', verbose_name='상세 공지사항',
    )

    # ── 내용 (이미지 한 장) ──
    image = models.ImageField(
        '팝업 이미지', upload_to='popups/%Y-%m/',
        width_field='image_width', height_field='image_height',
    )
    # 원본 크기. <img width height> 로 내려보내 이미지가 뜨기 전에도 자리를
    # 잡아 둔다 — 팝업이 열리자마자 내용이 튀는 걸 막는다.
    image_width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    image_height = models.PositiveIntegerField(null=True, blank=True, editable=False)
    image_alt = models.CharField(
        '이미지 설명', max_length=120, blank=True, default='',
        help_text='이미지를 못 보는 사람(스크린리더·로딩 실패)에게 읽히는 대체 텍스트입니다.',
    )

    # ── CTA ──
    cta_label = models.CharField(
        'CTA 문구', max_length=40, blank=True, default='자세히 보기',
        help_text='비워 두면 버튼 없이 이미지만 눌러 이동합니다.',
    )
    cta_url = models.CharField(
        'CTA 링크', max_length=300, blank=True, default='',
        help_text='비워 두면 연결된 공지사항 상세(/notice/<id>)로 이동합니다.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notice_popups'
        ordering = ['-priority', '-starts_at']
        verbose_name = '팝업 배너'
        verbose_name_plural = '팝업 배너'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invalidate_popup_cache()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        invalidate_popup_cache()

    @property
    def is_live(self):
        """지금이 게시기간 안인가."""
        if not self.active:
            return False
        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True

    @property
    def image_url(self):
        return self.image.url if self.image else ''

    @property
    def target_url(self):
        if self.cta_url:
            return self.cta_url
        if self.notice_id:
            return f'/notice/{self.notice_id}'
        return ''

    @classmethod
    def live(cls):
        """게시기간 안인 팝업 중 우선순위가 가장 높은 하나.

        이미지가 없으면 띄울 내용이 없다 — 아예 후보에서 뺀다.
        """
        now = timezone.now()
        return (
            cls.objects
            .filter(active=True, starts_at__lte=now)
            .filter(models.Q(ends_at__isnull=True) | models.Q(ends_at__gte=now))
            .exclude(image='')
            .first()
        )
