from rest_framework import serializers

from .models import Notice, Popup

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


class PopupSerializer(serializers.ModelSerializer):
    """팝업 배너 — 모달과 공지 상세 히어로가 같은 이미지를 쓴다."""
    image = serializers.CharField(source='image_url', read_only=True)
    target_url = serializers.CharField(read_only=True)
    is_live = serializers.BooleanField(read_only=True)
    notice_id = serializers.IntegerField(read_only=True)
    version = serializers.SerializerMethodField()

    class Meta:
        model = Popup
        fields = [
            'id', 'version', 'placement', 'dismiss_days', 'notice_id',
            'is_live', 'image', 'image_alt', 'image_width', 'image_height',
            'cta_label', 'target_url',
        ]

    def get_version(self, obj):
        """내용이 바뀌면 값이 바뀐다 — 프론트의 '다시 보지 않기' 키에 쓰인다."""
        return int(obj.updated_at.timestamp())
