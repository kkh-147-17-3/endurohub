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
    item_id = models.CharField(max_length=64, blank=True, default='')
    item_type = models.CharField(max_length=30, blank=True, default='')
    session_id = models.CharField(max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_events'
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'event_type']),
            models.Index(fields=['item_type', 'item_id']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        label = self.event_type
        if self.item_type and self.item_id:
            label += f' {self.item_type}:{self.item_id}'
        return f'{label} @ {self.created_at:%Y-%m-%d %H:%M}'
