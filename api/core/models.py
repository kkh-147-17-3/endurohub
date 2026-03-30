from django.contrib.auth import get_user_model
from django.db import models


class AnalyticsEvent(models.Model):
    event_type = models.CharField(max_length=50, db_index=True)
    properties = models.JSONField(default=dict, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True, default='')
    user = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_events'
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.event_type} @ {self.created_at:%Y-%m-%d %H:%M}'
