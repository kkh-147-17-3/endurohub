from rest_framework import serializers

from .models import Notice, Popup, PopupStep

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


class PopupStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopupStep
        fields = ['order', 'title', 'description']


class PopupSerializer(serializers.ModelSerializer):
    """팝업 배너 — 모달과 공지 상세 히어로가 같은 페이로드를 쓴다."""
    steps = PopupStepSerializer(many=True, read_only=True)
    prize_image = serializers.SerializerMethodField()
    target_url = serializers.CharField(read_only=True)
    dday = serializers.IntegerField(read_only=True)
    is_live = serializers.BooleanField(read_only=True)
    notice_id = serializers.IntegerField(read_only=True)
    version = serializers.SerializerMethodField()

    class Meta:
        model = Popup
        fields = [
            'id', 'version', 'placement', 'dismiss_days', 'notice_id', 'target_url',
            'tag', 'headline', 'headline_accent', 'subtitle',
            'meta_period', 'meta_winners', 'show_dday', 'dday', 'is_live',
            'prize_image', 'prize_note', 'prize_name', 'prize_count',
            'cta_label',
            'fine_period', 'fine_announce', 'fine_note',
            'steps',
        ]

    def get_prize_image(self, obj):
        return obj.prize_image.url if obj.prize_image else ''

    def get_version(self, obj):
        """내용이 바뀌면 값이 바뀐다 — 프론트의 '다시 보지 않기' 키에 쓰인다."""
        return int(obj.updated_at.timestamp())
