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
