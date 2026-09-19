from typing import Any

from rest_framework import serializers

from .models import Notice, NoticeComment, Popup

CATEGORY_LABELS = dict(Notice.CATEGORY_CHOICES)


class NoticeListSerializer(serializers.ModelSerializer[Notice]):
    """Lightweight serializer for the notice list (no content)."""
    category_label = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    views = serializers.IntegerField(source='view_count')
    urgent = serializers.BooleanField(source='is_urgent')
    href = serializers.SerializerMethodField()

    class Meta:
        model = Notice
        fields = [
            'id', 'href', 'category', 'category_label', 'title',
            'date', 'views', 'pinned', 'urgent',
        ]

    def get_category_label(self, obj: Notice) -> str:
        return CATEGORY_LABELS.get(obj.category, obj.category)

    def get_date(self, obj: Notice) -> str:
        return obj.published_at.strftime('%Y·%m·%d') if obj.published_at else ''

    def get_href(self, obj: Notice) -> str | None:
        return f'/notice/{obj.slug}' if obj.slug else None


class NoticeDetailSerializer(NoticeListSerializer):
    """Full serializer for the notice detail page."""
    relatedRace = serializers.CharField(source='related_race')
    comment_count = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()

    class Meta(NoticeListSerializer.Meta):
        fields = NoticeListSerializer.Meta.fields + [
            'content', 'author', 'attachments', 'relatedRace', 'comment_count', 'comments',
        ]

    def get_comment_count(self, obj: Notice) -> int:
        return obj.comments.count()

    def get_comments(self, obj: Notice) -> Any:
        comments = (
            obj.comments.filter(parent__isnull=True)
            .select_related('user__profile')
            .prefetch_related('replies__user__profile')
        )
        return NoticeCommentSerializer(comments, many=True, context=self.context).data


class NoticeCommentSerializer(serializers.ModelSerializer[NoticeComment]):
    nickname = serializers.SerializerMethodField()
    is_reply = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = NoticeComment
        fields = [
            'id', 'notice_id', 'parent_id', 'nickname', 'content',
            'is_reply', 'created_at', 'created_at_formatted', 'replies', 'is_owner',
        ]

    def get_nickname(self, obj: NoticeComment) -> str:
        return obj.display_nickname

    def get_is_reply(self, obj: NoticeComment) -> bool:
        return obj.is_reply

    def get_created_at_formatted(self, obj: NoticeComment) -> str:
        return obj.created_at.strftime('%Y.%m.%d %H:%M') if obj.created_at else ''

    def get_replies(self, obj: NoticeComment) -> Any:
        if obj.parent_id is not None:
            return []
        replies = obj.replies.select_related('user__profile').order_by('created_at')
        return NoticeCommentSerializer(replies, many=True, context=self.context).data

    def get_is_owner(self, obj: NoticeComment) -> bool:
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.user_id == request.user.id if obj.user_id else False
        return False


class NoticeCommentCreateSerializer(serializers.Serializer[dict[str, Any]]):
    parent_id = serializers.IntegerField(required=False, allow_null=True)
    nickname = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    content = serializers.CharField(max_length=1000)
    password = serializers.CharField(min_length=4, max_length=50, required=False, allow_blank=True, default='')

    def validate_content(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError('댓글 내용을 입력해주세요.')
        return value.strip()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        request = self.context.get('request')
        is_authenticated = request and hasattr(request, 'user') and request.user.is_authenticated
        password = attrs.get('password', '')
        if not is_authenticated and (not password or len(password) < 4):
            raise serializers.ValidationError({'password': ['비밀번호는 최소 4자 이상이어야 합니다.']})
        return attrs


class NoticeCommentUpdateSerializer(serializers.Serializer[dict[str, Any]]):
    content = serializers.CharField(max_length=1000)
    password = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_content(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError('댓글 내용을 입력해주세요.')
        return value.strip()


class NoticeCommentDeleteSerializer(serializers.Serializer[dict[str, Any]]):
    password = serializers.CharField(required=False, allow_blank=True, default='')


class PopupSerializer(serializers.ModelSerializer[Popup]):
    """팝업 배너 — 모달과 공지 상세 히어로가 같은 이미지를 쓴다."""
    image = serializers.SerializerMethodField()
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

    def get_version(self, obj: Popup) -> int:
        """내용이 바뀌면 값이 바뀐다 — 프론트의 '다시 보지 않기' 키에 쓰인다."""
        return int(obj.updated_at.timestamp())

    def get_image(self, obj: Popup) -> str:
        """같은 파일명으로 교체해도 브라우저·CDN 캐시를 우회한다."""
        url = obj.image_url
        if not url:
            return ''
        return f'{url}?v={self.get_version(obj)}'
