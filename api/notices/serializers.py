from rest_framework import serializers

from .models import Notice

CATEGORY_LABELS = dict(Notice.CATEGORY_CHOICES)


class NoticeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the notice list (no content)."""
    category_label = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    views = serializers.IntegerField(source='view_count')
    urgent = serializers.BooleanField(source='is_urgent')

    class Meta:
        model = Notice
        fields = [
            'id', 'category', 'category_label', 'title',
            'date', 'views', 'pinned', 'urgent',
        ]

    def get_category_label(self, obj):
        return CATEGORY_LABELS.get(obj.category, obj.category)

    def get_date(self, obj):
        return obj.published_at.strftime('%Y·%m·%d') if obj.published_at else ''


class NoticeDetailSerializer(NoticeListSerializer):
    """Full serializer for the notice detail page."""
    relatedRace = serializers.CharField(source='related_race')

    class Meta(NoticeListSerializer.Meta):
        fields = NoticeListSerializer.Meta.fields + [
            'content', 'author', 'attachments', 'relatedRace',
        ]
