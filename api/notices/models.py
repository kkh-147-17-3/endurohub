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
    """팝업 배너 — 게시기간과 내용을 관리자에서 관리한다.

    배너 자체(팝업 모달)만 이 모델이 들고, 상세 페이지는 연결된 공지사항
    (Notice)이 담당한다. CTA 를 비워 두면 연결된 공지 상세로 보낸다.
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

    # ── 상단 잉크 블록 ──
    tag = models.CharField('태그', max_length=30, blank=True, default='이벤트')
    headline = models.TextField('헤드라인')
    headline_accent = models.CharField('헤드라인 강조 단어', max_length=40, blank=True, default='')
    subtitle = models.TextField('설명', blank=True, default='')

    # ── 3칸 메타 ──
    meta_period = models.CharField('메타 · 기간', max_length=40, blank=True, default='')
    meta_winners = models.CharField('메타 · 당첨', max_length=40, blank=True, default='')
    show_dday = models.BooleanField('마감 D-day 표시', default=True)

    # ── 경품 ──
    prize_image = models.ImageField('경품 이미지', upload_to='popups/%Y-%m/', null=True, blank=True)
    prize_note = models.CharField('경품 부가설명', max_length=60, blank=True, default='')
    prize_name = models.CharField('경품 이름', max_length=80, blank=True, default='')
    prize_count = models.CharField('경품 수량', max_length=20, blank=True, default='')

    # ── CTA ──
    cta_label = models.CharField('CTA 문구', max_length=40, blank=True, default='자세히 보기')
    cta_url = models.CharField(
        'CTA 링크', max_length=300, blank=True, default='',
        help_text='비워 두면 연결된 공지사항 상세(/notice/<id>)로 이동합니다.',
    )

    # ── 하단 세부 ──
    fine_period = models.CharField('세부 · 기간', max_length=80, blank=True, default='')
    fine_announce = models.CharField('세부 · 발표', max_length=120, blank=True, default='')
    fine_note = models.TextField('세부 · 유의사항', blank=True, default='')

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
    def dday(self):
        """마감까지 남은 일수. 종료일이 없으면 None."""
        if not self.ends_at:
            return None
        return (self.ends_at - timezone.now()).days

    @property
    def target_url(self):
        if self.cta_url:
            return self.cta_url
        if self.notice_id:
            return f'/notice/{self.notice_id}'
        return ''

    @classmethod
    def live(cls):
        """게시기간 안인 팝업 중 우선순위가 가장 높은 하나."""
        now = timezone.now()
        return (
            cls.objects
            .filter(active=True, starts_at__lte=now)
            .filter(models.Q(ends_at__isnull=True) | models.Q(ends_at__gte=now))
            .prefetch_related('steps')
            .first()
        )


class PopupStep(models.Model):
    """팝업 배너의 참여 단계 (01 / 02 / 03 …)."""

    popup = models.ForeignKey(Popup, on_delete=models.CASCADE, related_name='steps')
    order = models.PositiveSmallIntegerField('순서', default=1)
    title = models.CharField('제목', max_length=80)
    description = models.TextField('설명', blank=True, default='')

    class Meta:
        db_table = 'notice_popup_steps'
        ordering = ['order', 'id']
        verbose_name = '참여 단계'
        verbose_name_plural = '참여 단계'

    def __str__(self):
        return f'{self.order:02d} {self.title}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invalidate_popup_cache()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        invalidate_popup_cache()
