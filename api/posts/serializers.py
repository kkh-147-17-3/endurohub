from rest_framework import serializers

from core.sanitize import html_to_text, sanitize_html
from .models import Post, PostComment, PostLike


class PostCommentSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField()
    is_reply = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = [
            'id', 'post_id', 'parent_id', 'nickname', 'content',
            'is_reply', 'created_at', 'created_at_formatted', 'replies',
            'is_owner',
        ]

    def get_nickname(self, obj):
        return obj.display_nickname

    def get_is_reply(self, obj):
        return obj.is_reply

    def get_created_at_formatted(self, obj):
        if obj.created_at:
            return obj.created_at.strftime('%Y.%m.%d %H:%M')
        return ''

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.user_id == request.user.id if obj.user_id else False
        return False

    def get_replies(self, obj):
        if obj.parent_id is not None:
            return []
        replies = obj.replies.all().order_by('created_at')
        return PostCommentSerializer(replies, many=True, context=self.context).data


class PostSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField()
    image_srcs = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    tagged_races = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    content_text = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'nickname', 'title', 'content', 'content_text',
            'category',
            'images', 'image_srcs',
            'view_count', 'comment_count', 'like_count',
            'created_at', 'created_at_formatted', 'updated_at',
            'tagged_races', 'comments', 'is_owner',
        ]

    def get_nickname(self, obj):
        return obj.display_nickname

    def get_image_srcs(self, obj):
        return obj.image_srcs

    def get_comment_count(self, obj):
        if hasattr(obj, '_comment_count'):
            return obj._comment_count
        return obj.comment_count

    def get_like_count(self, obj):
        if hasattr(obj, '_like_count'):
            return obj._like_count
        return obj.like_count

    def get_created_at_formatted(self, obj):
        if obj.created_at:
            return obj.created_at.strftime('%Y.%m.%d %H:%M')
        return ''

    def get_tagged_races(self, obj):
        include_races = self.context.get('include_tagged_races', False)
        if not include_races:
            return None
        from races.serializers import TaggedRaceSerializer
        return TaggedRaceSerializer(obj.races.all(), many=True).data

    def get_comments(self, obj):
        include_comments = self.context.get('include_comments', False)
        if not include_comments:
            return None
        root_comments = obj.comments.filter(
            parent_id__isnull=True
        ).prefetch_related('replies').order_by('-created_at')
        return PostCommentSerializer(root_comments, many=True, context=self.context).data

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.user_id == request.user.id if obj.user_id else False
        return False

    def get_content_text(self, obj):
        text = html_to_text(obj.content) if obj.content else ''
        return text[:500]


class PostListSerializer(serializers.ModelSerializer):
    """Lighter serializer for post listings (no comments)."""
    nickname = serializers.SerializerMethodField()
    image_srcs = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    tagged_races = serializers.SerializerMethodField()
    content_text = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'nickname', 'title', 'content', 'content_text',
            'category',
            'images', 'image_srcs',
            'view_count', 'comment_count', 'like_count',
            'created_at', 'created_at_formatted', 'updated_at',
            'tagged_races',
        ]

    def get_nickname(self, obj):
        return obj.display_nickname

    def get_image_srcs(self, obj):
        return obj.image_srcs

    def get_comment_count(self, obj):
        if hasattr(obj, '_comment_count'):
            return obj._comment_count
        return obj.comment_count

    def get_like_count(self, obj):
        if hasattr(obj, '_like_count'):
            return obj._like_count
        return obj.like_count

    def get_created_at_formatted(self, obj):
        if obj.created_at:
            return obj.created_at.strftime('%Y.%m.%d %H:%M')
        return ''

    def get_tagged_races(self, obj):
        from races.serializers import TaggedRaceSerializer
        return TaggedRaceSerializer(obj.races.all(), many=True).data

    def get_content_text(self, obj):
        text = html_to_text(obj.content) if obj.content else ''
        return text[:500]


class PostCreateSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    title = serializers.CharField(max_length=100)
    content = serializers.CharField()
    password = serializers.CharField(min_length=4, max_length=50, required=False, allow_blank=True, default='')
    category = serializers.ChoiceField(
        choices=[c[0] for c in Post.CATEGORY_CHOICES],
        required=False, allow_null=True, allow_blank=True,
    )
    race_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_null=True,
        max_length=5,
    )

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('제목을 입력해주세요.')
        if len(value) > 100:
            raise serializers.ValidationError('제목은 최대 100자까지 입력 가능합니다.')
        return value.strip()

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('내용을 입력해주세요.')
        # Sanitize HTML
        sanitized = sanitize_html(value)
        # Validate text length (excluding HTML tags)
        text = html_to_text(sanitized)
        if len(text) > 10000:
            raise serializers.ValidationError('내용은 최대 10000자까지 입력 가능합니다.')
        return sanitized

    def validate(self, attrs):
        # Password is required only for unauthenticated users
        request = self.context.get('request')
        is_authenticated = request and hasattr(request, 'user') and request.user.is_authenticated
        password = attrs.get('password', '')
        if not is_authenticated and (not password or len(password) < 4):
            raise serializers.ValidationError({'password': ['비밀번호는 최소 4자 이상이어야 합니다.']})
        return attrs

    def validate_race_ids(self, value):
        if value and len(value) > 5:
            raise serializers.ValidationError('대회 태그는 최대 5개까지 선택 가능합니다.')
        if value:
            from races.models import Race
            existing = Race.objects.filter(id__in=value).count()
            if existing != len(value):
                raise serializers.ValidationError('존재하지 않는 대회가 포함되어 있습니다.')
        return value


class PostUpdateSerializer(serializers.Serializer):
    edit_token = serializers.CharField(required=False, allow_blank=True, default='')
    nickname = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    title = serializers.CharField(max_length=100)
    content = serializers.CharField()
    category = serializers.ChoiceField(
        choices=[c[0] for c in Post.CATEGORY_CHOICES],
        required=False, allow_null=True, allow_blank=True,
    )
    race_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_null=True,
        max_length=5,
    )
    existing_images = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_null=True,
    )

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('제목을 입력해주세요.')
        return value.strip()

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('내용을 입력해주세요.')
        # Sanitize HTML
        sanitized = sanitize_html(value)
        # Validate text length (excluding HTML tags)
        text = html_to_text(sanitized)
        if len(text) > 10000:
            raise serializers.ValidationError('내용은 최대 10000자까지 입력 가능합니다.')
        return sanitized


class CommentCreateSerializer(serializers.Serializer):
    parent_id = serializers.IntegerField(required=False, allow_null=True)
    nickname = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    content = serializers.CharField(max_length=1000)
    password = serializers.CharField(min_length=4, max_length=50, required=False, allow_blank=True, default='')

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('댓글 내용을 입력해주세요.')
        if len(value) > 1000:
            raise serializers.ValidationError('댓글은 최대 1000자까지 입력 가능합니다.')
        return value.strip()

    def validate(self, attrs):
        request = self.context.get('request')
        is_authenticated = request and hasattr(request, 'user') and request.user.is_authenticated
        password = attrs.get('password', '')
        if not is_authenticated and (not password or len(password) < 4):
            raise serializers.ValidationError({'password': ['비밀번호는 최소 4자 이상이어야 합니다.']})
        return attrs


class CommentUpdateSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=1000)
    password = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('댓글 내용을 입력해주세요.')
        return value.strip()


class CommentDeleteSerializer(serializers.Serializer):
    password = serializers.CharField(required=False, allow_blank=True, default='')
