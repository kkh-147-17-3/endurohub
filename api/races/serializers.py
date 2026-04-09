import json
import re

from rest_framework import serializers

from .models import DeviceToken, Race, Review


def _fee_to_numeric_string(value) -> str:
    """Normalize fee for clients that use Number(fee); strip currency text."""
    if value is None:
        return ''
    if isinstance(value, bool):
        return '1' if value else '0'
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value == int(value) else str(value)
    s = str(value).strip()
    digits = re.sub(r'[^\d]', '', s)
    return digits if digits else s


def normalize_entry_fee_for_api(raw):
    """Coerce DB JSONField quirks into list[{distance, fee}]|null for the API."""
    if raw is None:
        return None
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return [
            {'distance': str(k), 'fee': _fee_to_numeric_string(v)}
            for k, v in raw.items()
        ]
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return None
        if s.startswith('{') or s.startswith('['):
            try:
                parsed = json.loads(s)
                return normalize_entry_fee_for_api(parsed)
            except json.JSONDecodeError:
                pass
        return [{'distance': '', 'fee': _fee_to_numeric_string(s)}]
    return None


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

    class Meta:
        model = Race
        fields = [
            'id', 'slug', 'title', 'sport', 'sport_label',
            'race_date', 'race_end_date', 'start_time',
            'location', 'address', 'latitude', 'longitude', 'region',
            'distances',
            'registration_start', 'registration_end', 'entry_fee',
            'official_url', 'source', 'source_url',
            'status', 'status_label',
            'description', 'organizer', 'organizer_contact', 'organizer_email',
            'image_src', 'image_src_thumb', 'giveaways', 'course_image_srcs', 'giveaway_image_srcs',
            'view_count', 'days_until_race', 'days_until_registration_end',
            'is_registration_open', 'is_verified', 'verified_at', 'verified_by',
            'recap_url', 'ai_summary', 'url',
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
        return normalize_entry_fee_for_api(obj.entry_fee)


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

    class Meta:
        model = Review
        fields = [
            'id', 'nickname', 'rating', 'comment',
            'completion_time', 'course_difficulty',
            'operation_satisfaction', 'recommendation_tags',
            'created_at', 'created_at_formatted',
        ]

    def get_nickname(self, obj):
        return obj.display_nickname

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
