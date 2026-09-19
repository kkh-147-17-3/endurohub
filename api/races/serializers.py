from typing import Any, NotRequired, TypedDict, cast

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework import serializers

from accounts.models import RaceRecord
from accounts.serializers import RaceResultInputSerializer, course_code_for

from .models import DeviceToken, Race, RaceParticipation, Review


class ReviewCreateData(TypedDict):
    rating: int
    comment: str
    nickname: NotRequired[str | None]
    completion_time: NotRequired[str | None]
    course_difficulty: NotRequired[str | None]
    operation_satisfaction: NotRequired[int | None]
    recommendation_tags: NotRequired[list[str] | None]


class DeviceTokenCreateData(TypedDict):
    token: str
    platform: str
    subscribed_sports: NotRequired[list[str] | None]
    subscribed_regions: NotRequired[list[str] | None]


class DeviceTokenUpdateData(TypedDict):
    token: str
    subscribed_sports: NotRequired[list[str] | None]
    subscribed_regions: NotRequired[list[str] | None]


class RaceParticipationWriteData(TypedDict):
    status: NotRequired[str]
    planned_codes: NotRequired[list[str]]
    main_goal: NotRequired[bool]
    note: NotRequired[str]


class RaceSerializer(serializers.ModelSerializer[Race]):
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

    def get_sport_label(self, obj: Race) -> str:
        label: str = obj.sport_label
        return label

    def get_status(self, obj: Race) -> str:
        value: str = obj.computed_status
        return value

    def get_status_label(self, obj: Race) -> str:
        label: str = obj.status_label
        return label

    def get_image_src(self, obj: Race) -> str | None:
        src: str | None = obj.image_src
        return src

    def get_image_src_thumb(self, obj: Race) -> str | None:
        src: str | None = obj.image_src_thumb
        return src

    def get_course_image_srcs(self, obj: Race) -> list[str]:
        srcs: list[str] = obj.course_image_srcs
        return srcs

    def get_giveaway_image_srcs(self, obj: Race) -> list[str]:
        srcs: list[str] = obj.giveaway_image_srcs
        return srcs

    def get_days_until_race(self, obj: Race) -> int:
        days: int = obj.days_until_race
        return days

    def get_days_until_registration_end(self, obj: Race) -> int | None:
        days: int | None = obj.days_until_registration_end
        return days

    def get_is_registration_open(self, obj: Race) -> bool:
        return bool(obj.is_registration_open)

    def get_is_verified(self, obj: Race) -> bool:
        return bool(obj.verified_at)

    def get_url(self, obj: Race) -> str:
        url: str = obj.url
        return url

    def get_entry_fee(self, obj: Race) -> list[dict[str, str]] | None:
        """Derive entry_fee from distances for backward compatibility."""
        if not obj.distances or not isinstance(obj.distances, list):
            return None
        result: list[dict[str, str]] = []
        for d in obj.distances:
            if isinstance(d, dict) and d.get('fee') is not None:
                result.append({
                    'distance': d.get('name', ''),
                    'fee': str(d['fee']),
                })
        return result or None

    def get_is_favorited(self, obj: Race) -> bool:
        favorite_ids = self.context.get('favorite_race_ids')
        if favorite_ids is None:
            return False
        return obj.id in favorite_ids


class RaceListSerializer(serializers.ModelSerializer[Race]):
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

    def get_days_until_race(self, obj: Race) -> int:
        days: int = obj.days_until_race
        return days

    def get_days_until_registration_end(self, obj: Race) -> int | None:
        days: int | None = obj.days_until_registration_end
        return days

    def get_status(self, obj: Race) -> str:
        value: str = obj.computed_status
        return value

    def get_url(self, obj: Race) -> str:
        url: str = obj.url
        return url

    def get_entry_fee(self, obj: Race) -> list[dict[str, str]] | None:
        if not obj.distances or not isinstance(obj.distances, list):
            return None
        result: list[dict[str, str]] = []
        for d in obj.distances:
            if isinstance(d, dict) and d.get('fee') is not None:
                result.append({
                    'distance': d.get('name', ''),
                    'fee': str(d['fee']),
                })
        return result or None

    def get_is_favorited(self, obj: Race) -> bool:
        favorite_ids = self.context.get('favorite_race_ids')
        if favorite_ids is None:
            return False
        return obj.id in favorite_ids


class TaggedRaceSerializer(serializers.ModelSerializer[Race]):
    sport_label = serializers.SerializerMethodField()

    class Meta:
        model = Race
        fields = ['id', 'slug', 'title', 'sport', 'sport_label']

    def get_sport_label(self, obj: Race) -> str:
        label: str = obj.sport_label
        return label


class UpcomingRaceSerializer(serializers.ModelSerializer[Race]):
    sport_label = serializers.SerializerMethodField()
    race_date = serializers.SerializerMethodField()

    class Meta:
        model = Race
        fields = ['id', 'title', 'sport', 'sport_label', 'race_date']

    def get_sport_label(self, obj: Race) -> str:
        label: str = obj.sport_label
        return label

    def get_race_date(self, obj: Race) -> str | None:
        if obj.race_date:
            return obj.race_date.strftime('%Y.%m.%d')
        return None


class ReviewSerializer(serializers.ModelSerializer[Review]):
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

    def get_nickname(self, obj: Review) -> str:
        nickname: str = obj.display_nickname
        return nickname

    def get_like_count(self, obj: Review) -> int:
        annotated: Any = getattr(obj, '_like_count', None)
        if annotated is not None:
            return cast(int, annotated)
        return obj.like_count

    def get_has_liked(self, obj: Review) -> bool:
        # 목록에서는 뷰가 미리 구한 id 집합을 넘긴다 (리뷰당 쿼리 방지).
        liked_ids = self.context.get('liked_review_ids')
        if liked_ids is not None:
            return obj.id in liked_ids
        ip_hash = self.context.get('ip_hash')
        if not ip_hash:
            return False
        return obj.likes.filter(ip_hash=ip_hash).exists()

    def get_created_at_formatted(self, obj: Review) -> str:
        if obj.created_at:
            return obj.created_at.strftime('%Y.%m.%d')
        return ''


class HomeActivityRaceSerializer(serializers.ModelSerializer[Race]):
    """Small race reference shared by the home review and finish feeds."""

    sport_label = serializers.SerializerMethodField()

    class Meta:
        model = Race
        fields = ['id', 'slug', 'title', 'sport', 'sport_label', 'race_date']

    def get_sport_label(self, obj: Race) -> str:
        return obj.sport_label


class HomeReviewSerializer(ReviewSerializer):
    race = HomeActivityRaceSerializer(read_only=True)

    class Meta(ReviewSerializer.Meta):
        fields = [*ReviewSerializer.Meta.fields, 'race']


class HomeRaceRecordSerializer(serializers.ModelSerializer[RaceRecord]):
    """Public, catalogue-linked finish shown in the home activity board."""

    nickname = serializers.SerializerMethodField()
    sport = serializers.CharField(source='race.sport', read_only=True)
    sport_label = serializers.CharField(source='race.sport_label', read_only=True)
    course_label = serializers.CharField(source='distance', read_only=True)
    time = serializers.SerializerMethodField()
    metric_label = serializers.SerializerMethodField()
    metric_value = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    me = serializers.SerializerMethodField()
    race = HomeActivityRaceSerializer(read_only=True)

    class Meta:
        model = RaceRecord
        fields = [
            'id', 'nickname', 'sport', 'sport_label',
            'course_code', 'course_label', 'time', 'metric_label', 'metric_value', 'date',
            'duration_seconds', 'me', 'created_at', 'race',
        ]

    def get_nickname(self, obj: RaceRecord) -> str:
        try:
            return obj.user.profile.nickname or '러너'
        except (AttributeError, ObjectDoesNotExist):
            return '러너'

    def get_time(self, obj: RaceRecord) -> str:
        total = obj.duration_seconds or 0
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{hours}:{minutes:02d}:{seconds:02d}'

    def _distance_meters(self, obj: RaceRecord) -> int | None:
        if not obj.race_id or not obj.course_code or not obj.duration_seconds:
            return None
        race = cast(Race, obj.race)
        for distance in race.distances or []:
            if not isinstance(distance, dict) or course_code_for(distance) != obj.course_code:
                continue
            meters = distance.get('distance_meter')
            if meters and meters > 0:
                return cast(int, meters)
            return None
        return None

    def get_metric_label(self, obj: RaceRecord) -> str:
        race = cast(Race, obj.race)
        if race.sport == 'cycling':
            return '평균 속도'
        if race.sport in ('running', 'trail_running', 'swimming'):
            return '평균 페이스'
        return '평균 페이스 · 속도'

    def get_metric_value(self, obj: RaceRecord) -> str:
        race = cast(Race, obj.race)
        meters = self._distance_meters(obj)
        if not meters or not obj.duration_seconds:
            return '—'
        if race.sport in ('running', 'trail_running'):
            seconds_per_km = int(round(obj.duration_seconds / (meters / 1000)))
            minutes, seconds = divmod(seconds_per_km, 60)
            return f'{minutes}′{seconds:02d}″/km'
        if race.sport == 'cycling':
            kilometers_per_hour = (meters / 1000) / (obj.duration_seconds / 3600)
            return f'{kilometers_per_hour:.1f} km/h'
        if race.sport == 'swimming':
            seconds_per_100m = int(round(obj.duration_seconds / (meters / 100)))
            minutes, seconds = divmod(seconds_per_100m, 60)
            return f'{minutes}′{seconds:02d}″/100m'
        return '—'

    def get_date(self, obj: RaceRecord) -> str | None:
        return timezone.localdate(obj.created_at).isoformat() if obj.created_at else None

    def get_me(self, obj: RaceRecord) -> bool:
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        return bool(user and user.is_authenticated and user.pk == obj.user_id)


class ReviewCreateSerializer(serializers.Serializer[ReviewCreateData]):
    nickname = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(min_length=5, max_length=200)
    race_record = RaceResultInputSerializer()
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

    def validate_rating(self, value: Any) -> Any:
        if not isinstance(value, int) or value < 1:
            raise serializers.ValidationError('별점을 선택해주세요.')
        if value > 5:
            raise serializers.ValidationError('별점은 5점 이하이어야 합니다.')
        return value

    def validate_comment(self, value: Any) -> Any:
        if not value or not value.strip():
            raise serializers.ValidationError('한줄평을 입력해주세요.')
        if len(value.strip()) < 5:
            raise serializers.ValidationError('한줄평은 최소 5자 이상 입력해주세요.')
        if len(value) > 200:
            raise serializers.ValidationError('한줄평은 최대 200자까지 입력 가능합니다.')
        return value.strip()

    def validate(self, attrs: Any) -> Any:
        if attrs.get('race_record', {}).get('is_public') is not True:
            raise serializers.ValidationError({
                'race_record': ['리뷰와 완주 기록 공개에 동의해주세요.'],
            })
        return attrs

    default_error_messages = {
        'required': '이 필드는 필수입니다.',
    }


class DeviceTokenSerializer(serializers.ModelSerializer[DeviceToken]):
    class Meta:
        model = DeviceToken
        fields = ['id', 'token', 'platform', 'subscribed_sports', 'subscribed_regions',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DeviceTokenCreateSerializer(serializers.Serializer[DeviceTokenCreateData]):
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


class DeviceTokenUpdateSerializer(serializers.Serializer[DeviceTokenUpdateData]):
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


class RaceParticipationWriteSerializer(serializers.Serializer[RaceParticipationWriteData]):
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

    def validate(self, attrs: RaceParticipationWriteData) -> RaceParticipationWriteData:
        # 관심(maybe) 상태에서는 종목을 미정으로 둔다.
        if attrs.get('status') == RaceParticipation.STATUS_MAYBE:
            attrs['planned_codes'] = []
        else:
            attrs['planned_codes'] = [c.strip() for c in (attrs.get('planned_codes') or []) if c.strip()]
        attrs['note'] = (attrs.get('note') or '').strip()
        return attrs
