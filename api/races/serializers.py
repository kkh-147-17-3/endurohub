from rest_framework import serializers

from .models import DeviceToken, Race, RaceParticipation, Review


class RaceSerializer(serializers.ModelSerializer):
    sport_label = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    image_src = serializers.SerializerMethodField()
    image_src_thumb = serializers.SerializerMethodField()
    course_image_srcs = serializers.SerializerMethodField()
    giveaway_image_srcs = serializers.SerializerMethodField()
    days_until_race = serializers.SerializerMethodField()
    days_until_registration_end = serializers.SerializerMethodField()
    is_registration_open = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()
    verified_at = serializers.DateTimeField(read_only=True)
    verified_by = serializers.CharField(read_only=True)
    url = serializers.SerializerMethodField()
    entry_fee = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Race
        fields = [
            'id', 'slug', 'title', 'edition', 'sport', 'sport_label',
            'race_date', 'race_end_date', 'start_time',
            'location', 'address', 'latitude', 'longitude', 'region',
            'distances',
            'registration_start', 'registration_end', 'registration_phases',
            'entry_fee',
            'official_url', 'source', 'source_url',
            'status', 'status_label',
            'description', 'organizer', 'organizer_contact', 'organizer_email',
            'image_src', 'image_src_thumb', 'giveaways', 'course_image_srcs', 'giveaway_image_srcs',
            'view_count', 'days_until_race', 'days_until_registration_end',
            'is_registration_open', 'is_verified', 'verified_at', 'verified_by',
            'recap_url', 'ai_summary', 'url',
            'is_favorited',
            'weather_forecast',
            'course_surface', 'course_difficulty', 'aid_stations',
            'timing_method', 'parking',
            'created_at', 'updated_at',
        ]

    def get_sport_label(self, obj):
        return obj.sport_label

    def get_status(self, obj):
        return obj.computed_status

    def get_status_label(self, obj):
        return obj.status_label

    def get_image_src(self, obj):
        return obj.image_src

    def get_image_src_thumb(self, obj):
        return obj.image_src_thumb

    def get_course_image_srcs(self, obj):
        return obj.course_image_srcs

    def get_giveaway_image_srcs(self, obj):
        return obj.giveaway_image_srcs

    def get_days_until_race(self, obj):
        return obj.days_until_race

    def get_days_until_registration_end(self, obj):
        return obj.days_until_registration_end

    def get_is_registration_open(self, obj):
        return obj.is_registration_open

    def get_is_verified(self, obj):
        return bool(obj.verified_at)

    def get_url(self, obj):
        return obj.url

    def get_entry_fee(self, obj):
        """Derive entry_fee from distances for backward compatibility."""
        if not obj.distances or not isinstance(obj.distances, list):
            return None
        result = []
        for d in obj.distances:
            if isinstance(d, dict) and d.get('fee') is not None:
                result.append({
                    'distance': d.get('name', ''),
                    'fee': str(d['fee']),
                })
        return result or None

    def get_is_favorited(self, obj):
        favorite_ids = self.context.get('favorite_race_ids')
        if favorite_ids is None:
            return False
        return obj.id in favorite_ids


class RaceListSerializer(serializers.ModelSerializer):
    """Slim serializer for list/card views.

    Drops heavy fields (description, ai_summary, weather_forecast,
    image/course/giveaway uploads, organizer, registration_phases, etc.)
    and avoids any filesystem-checking image properties. Keeps only what
    list pages (yearly, calendar, races list, home cards/rows) actually use.
    """

    days_until_race = serializers.SerializerMethodField()
    days_until_registration_end = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    entry_fee = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Race
        fields = [
            'id', 'slug', 'title', 'sport',
            'race_date', 'region',
            'distances', 'entry_fee',
            'status', 'url',
            'days_until_race', 'days_until_registration_end',
            'is_favorited',
        ]

    def get_days_until_race(self, obj):
        return obj.days_until_race

    def get_days_until_registration_end(self, obj):
        return obj.days_until_registration_end

    def get_status(self, obj):
        return obj.computed_status

    def get_url(self, obj):
        return obj.url

    def get_entry_fee(self, obj):
        if not obj.distances or not isinstance(obj.distances, list):
            return None
        result = []
        for d in obj.distances:
            if isinstance(d, dict) and d.get('fee') is not None:
                result.append({
                    'distance': d.get('name', ''),
                    'fee': str(d['fee']),
                })
        return result or None

    def get_is_favorited(self, obj):
        favorite_ids = self.context.get('favorite_race_ids')
        if favorite_ids is None:
            return False
        return obj.id in favorite_ids


class TaggedRaceSerializer(serializers.ModelSerializer):
    sport_label = serializers.SerializerMethodField()

    class Meta:
        model = Race
        fields = ['id', 'slug', 'title', 'sport', 'sport_label']

    def get_sport_label(self, obj):
        return obj.sport_label


class UpcomingRaceSerializer(serializers.ModelSerializer):
    sport_label = serializers.SerializerMethodField()
    race_date = serializers.SerializerMethodField()

    class Meta:
        model = Race
        fields = ['id', 'title', 'sport', 'sport_label', 'race_date']

    def get_sport_label(self, obj):
        return obj.sport_label

    def get_race_date(self, obj):
        if obj.race_date:
            return obj.race_date.strftime('%Y.%m.%d')
        return None


class ReviewSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'nickname', 'rating', 'comment',
            'completion_time', 'course_difficulty',
            'operation_satisfaction', 'recommendation_tags',
            'created_at', 'created_at_formatted',
            'like_count', 'has_liked',
        ]

    def get_nickname(self, obj):
        return obj.display_nickname

    def get_like_count(self, obj):
        if hasattr(obj, '_like_count'):
            return obj._like_count
        return obj.like_count

    def get_has_liked(self, obj):
        # 목록에서는 뷰가 미리 구한 id 집합을 넘긴다 (리뷰당 쿼리 방지).
        liked_ids = self.context.get('liked_review_ids')
        if liked_ids is not None:
            return obj.id in liked_ids
        ip_hash = self.context.get('ip_hash')
        if not ip_hash:
            return False
        return obj.likes.filter(ip_hash=ip_hash).exists()

    def get_created_at_formatted(self, obj):
        if obj.created_at:
            return obj.created_at.strftime('%Y.%m.%d')
        return ''


class ReviewCreateSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(min_length=5, max_length=200)
    completion_time = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    course_difficulty = serializers.ChoiceField(
        choices=['easy', 'normal', 'hard'],
        required=False, allow_blank=True, allow_null=True,
    )
    operation_satisfaction = serializers.IntegerField(
        min_value=1, max_value=5, required=False, allow_null=True,
    )
    recommendation_tags = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False, allow_null=True, max_length=10,
    )

    def validate_rating(self, value):
        if not isinstance(value, int) or value < 1:
            raise serializers.ValidationError('별점을 선택해주세요.')
        if value > 5:
            raise serializers.ValidationError('별점은 5점 이하이어야 합니다.')
        return value

    def validate_comment(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('한줄평을 입력해주세요.')
        if len(value.strip()) < 5:
            raise serializers.ValidationError('한줄평은 최소 5자 이상 입력해주세요.')
        if len(value) > 200:
            raise serializers.ValidationError('한줄평은 최대 200자까지 입력 가능합니다.')
        return value.strip()

    default_error_messages = {
        'required': '이 필드는 필수입니다.',
    }


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['id', 'token', 'platform', 'subscribed_sports', 'subscribed_regions',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DeviceTokenCreateSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)
    platform = serializers.ChoiceField(choices=['android', 'ios'])
    subscribed_sports = serializers.ListField(
        child=serializers.ChoiceField(
            choices=['running', 'swimming', 'cycling', 'triathlon', 'trail_running']
        ),
        required=False,
        allow_null=True,
    )
    subscribed_regions = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_null=True,
    )


class DeviceTokenUpdateSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)
    subscribed_sports = serializers.ListField(
        child=serializers.ChoiceField(
            choices=['running', 'swimming', 'cycling', 'triathlon', 'trail_running']
        ),
        required=False,
        allow_null=True,
    )
    subscribed_regions = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_null=True,
    )


class RaceParticipationWriteSerializer(serializers.Serializer):
    """Upsert a user's planning state (관심 / 참가 예정) for one race."""

    status = serializers.ChoiceField(
        choices=[RaceParticipation.STATUS_MAYBE, RaceParticipation.STATUS_GOING],
        required=False,
        default=RaceParticipation.STATUS_MAYBE,
    )
    planned_codes = serializers.ListField(
        child=serializers.CharField(max_length=20, allow_blank=True),
        required=False,
        allow_empty=True,
        default=list,
    )
    main_goal = serializers.BooleanField(required=False, default=False)
    note = serializers.CharField(max_length=200, required=False, allow_blank=True, default='')

    def validate(self, attrs):
        # 관심(maybe) 상태에서는 종목을 미정으로 둔다.
        if attrs.get('status') == RaceParticipation.STATUS_MAYBE:
            attrs['planned_codes'] = []
        else:
            attrs['planned_codes'] = [c.strip() for c in (attrs.get('planned_codes') or []) if c.strip()]
        attrs['note'] = (attrs.get('note') or '').strip()
        return attrs
