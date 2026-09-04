import re

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import RaceRecord, SocialAccount, UserProfile

User = get_user_model()


class UserMeSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='user.id')
    email = serializers.CharField(source='user.email', allow_blank=True)
    nickname = serializers.CharField(allow_null=True, allow_blank=True)
    profile_image = serializers.URLField(allow_blank=True)
    email_verified = serializers.BooleanField()
    email_updates_opt_in = serializers.BooleanField()
    preferred_sports = serializers.JSONField(default=None)
    preferred_regions = serializers.JSONField(default=None)
    onboarding_completed = serializers.BooleanField()
    needs_nickname = serializers.SerializerMethodField()
    needs_email_verification = serializers.SerializerMethodField()
    needs_onboarding = serializers.BooleanField()

    def get_needs_nickname(self, obj):
        return not obj.nickname

    def get_needs_email_verification(self, obj):
        return bool(obj.user.email) and bool(obj.nickname) and not obj.email_verified


class NicknameSetupSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=50, min_length=2)

    def validate_nickname(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('닉네임을 입력해주세요.')
        if len(value) < 2:
            raise serializers.ValidationError('닉네임은 최소 2자 이상이어야 합니다.')
        if len(value) > 50:
            raise serializers.ValidationError('닉네임은 최대 50자까지 가능합니다.')
        if not re.match(r'^[가-힣a-zA-Z0-9_\- ]+$', value):
            raise serializers.ValidationError('닉네임은 한글, 영문, 숫자, 밑줄, 하이픈만 사용 가능합니다.')
        if UserProfile.objects.filter(nickname=value).exists():
            raise serializers.ValidationError('이미 사용 중인 닉네임입니다.')
        return value


class EmailSendSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)

    def validate(self, attrs):
        user = self.context.get('user')
        email = (attrs.get('email') or (user.email if user else '') or '').strip().lower()

        if not email:
            raise serializers.ValidationError({'email': ['이메일을 입력해주세요.']})

        # Pending social signup: an address already on file is not a conflict — the
        # code we send to that inbox is what decides whether the social identity may
        # attach to that account.
        if self.context.get('allow_existing'):
            attrs['email'] = email
            return attrs

        if user:
            duplicate_user_exists = User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists()
            duplicate_social_exists = SocialAccount.objects.filter(email__iexact=email).exclude(user=user).exists()
        else:
            duplicate_user_exists = User.objects.filter(email__iexact=email).exists()
            duplicate_social_exists = SocialAccount.objects.filter(email__iexact=email).exists()

        if duplicate_user_exists or duplicate_social_exists:
            raise serializers.ValidationError({'email': ['이미 사용 중인 이메일입니다.']})

        attrs['email'] = email
        return attrs


class ProfilePreferencesSerializer(serializers.Serializer):
    email_updates_opt_in = serializers.BooleanField()


class OnboardingSerializer(serializers.Serializer):
    preferred_sports = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False,
        allow_empty=True,
        default=list,
    )
    preferred_regions = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False,
        allow_empty=True,
        default=list,
    )

    def validate_preferred_sports(self, value):
        from races.constants import SPORT_LABELS
        valid = set(SPORT_LABELS.keys())
        for sport in value:
            if sport not in valid:
                raise serializers.ValidationError(f'유효하지 않은 종목입니다: {sport}')
        return value

    def validate_preferred_regions(self, value):
        from races.constants import REGIONS
        for region in value:
            if region not in REGIONS:
                raise serializers.ValidationError(f'유효하지 않은 지역입니다: {region}')
        return value


class RaceRecordSerializer(serializers.ModelSerializer):
    """Read serializer for a stored race record."""

    sport_label = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()

    class Meta:
        model = RaceRecord
        fields = [
            'id', 'sport', 'sport_label', 'distance', 'name',
            'course_code', 'record_date', 'duration_seconds', 'time',
            'is_personal_best', 'is_public', 'created_at',
        ]

    def get_sport_label(self, obj):
        from races.constants import SPORT_LABELS
        return SPORT_LABELS.get(obj.sport, obj.sport)

    def get_time(self, obj):
        total = obj.duration_seconds or 0
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{hours:02d}:{minutes:02d}:{seconds:02d}'


class RaceRecordCreateSerializer(serializers.Serializer):
    """Write serializer accepting a sport, distance, and HH/MM/SS time parts."""

    sport = serializers.CharField(max_length=20)
    distance = serializers.CharField(max_length=80)
    name = serializers.CharField(max_length=200, required=False, allow_blank=True, default='')
    record_date = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    hours = serializers.IntegerField(required=False, min_value=0, max_value=99, default=0)
    minutes = serializers.IntegerField(required=False, min_value=0, max_value=59, default=0)
    seconds = serializers.IntegerField(required=False, min_value=0, max_value=59, default=0)
    is_public = serializers.BooleanField(required=False, default=False)

    def validate_sport(self, value):
        from races.constants import SPORT_LABELS
        if value not in SPORT_LABELS:
            raise serializers.ValidationError(f'유효하지 않은 종목입니다: {value}')
        return value

    def validate_distance(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('거리 / 종목 카테고리를 입력해주세요.')
        return value

    def validate(self, attrs):
        total = attrs.get('hours', 0) * 3600 + attrs.get('minutes', 0) * 60 + attrs.get('seconds', 0)
        if total <= 0:
            raise serializers.ValidationError({'time': ['기록 시간을 입력해주세요.']})
        attrs['duration_seconds'] = total
        return attrs

    def create(self, validated_data):
        return RaceRecord.objects.create(
            user=self.context['user'],
            sport=validated_data['sport'],
            distance=validated_data['distance'].strip(),
            name=(validated_data.get('name') or '').strip(),
            record_date=(validated_data.get('record_date') or '').strip(),
            duration_seconds=validated_data['duration_seconds'],
            is_public=validated_data.get('is_public', False),
        )


def course_code_for(distance: dict) -> str:
    """Mirror the frontend's course-code derivation for a race distance entry."""
    meters = distance.get('distance_meter') if isinstance(distance, dict) else None
    if meters and meters > 0:
        km = meters / 1000
        return f'{int(km)}K' if float(km).is_integer() else f'{km:.1f}K'
    name = (distance.get('name') if isinstance(distance, dict) else '') or ''
    return name[:4].upper()


def race_course_options(race) -> list[tuple[str, str]]:
    """Return the valid ``(code, label)`` pairs for a curated race.

    Races without a usable distance entry use the canonical backend sport code.
    Empty derived codes are deliberately ignored so malformed distance data cannot
    turn an empty string into a valid course choice.
    """
    options = []
    seen_codes = set()
    for distance in race.distances or []:
        if not isinstance(distance, dict):
            continue
        code = course_code_for(distance)
        if not code or code in seen_codes:
            continue
        seen_codes.add(code)
        options.append((code, distance.get('name') or code))

    if options:
        return options

    from races.constants import SPORT_CODES

    fallback = SPORT_CODES.get(race.sport, '')
    return [(fallback, race.sport_label)] if fallback else []


def upsert_linked_race_record(*, user, race, result_data):
    """Create or update the user's result for a curated race.

    Only explicitly supplied visibility/PB flags are updated. This lets callers
    such as review creation amend the finish without silently resetting an
    existing record's user-controlled settings.
    """
    code = result_data['course_code']
    label = next(
        (label for option_code, label in race_course_options(race) if option_code == code),
        code,
    )
    defaults = {
        'sport': race.sport,
        'distance': label,
        'course_code': code,
        'name': race.title,
        'record_date': race.race_date.isoformat() if race.race_date else '',
        'duration_seconds': result_data['duration_seconds'],
    }
    for field in ('is_personal_best', 'is_public'):
        if field in result_data:
            defaults[field] = result_data[field]

    record, _ = RaceRecord.objects.update_or_create(
        user=user,
        race=race,
        defaults=defaults,
    )
    return record


class RaceResultInputSerializer(serializers.Serializer):
    """Validate a course choice and finish time for a curated race.

    Requires the target Race in ``context['race']``. Persistence is intentionally
    separate so this serializer can also be nested in review creation.
    """

    course_code = serializers.CharField(max_length=20)
    hours = serializers.IntegerField(required=False, min_value=0, max_value=99, default=0)
    minutes = serializers.IntegerField(required=False, min_value=0, max_value=59, default=0)
    seconds = serializers.IntegerField(required=False, min_value=0, max_value=59, default=0)

    def validate_course_code(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('완주한 종목을 선택해주세요.')
        race = self.context['race']
        codes = {code for code, _ in race_course_options(race) if code}
        # The timeline used ``CYCLE`` before the backend sport-code contract was
        # aligned to ``CYC``. Accept and normalize that legacy fallback so an
        # existing cycling record can still be edited during a rolling deploy.
        if value == 'CYCLE' and 'CYC' in codes:
            value = 'CYC'
        if value not in codes:
            raise serializers.ValidationError(f'이 대회에 없는 종목입니다: {value}')
        return value

    def validate(self, attrs):
        total = attrs.get('hours', 0) * 3600 + attrs.get('minutes', 0) * 60 + attrs.get('seconds', 0)
        if total <= 0:
            raise serializers.ValidationError({'time': ['기록 시간을 입력해주세요.']})
        attrs['duration_seconds'] = total
        return attrs


class RaceResultCreateSerializer(RaceResultInputSerializer):
    """Log a finish for a curated race → a RaceRecord linked to that race."""

    is_personal_best = serializers.BooleanField(required=False)
    is_public = serializers.BooleanField(required=False)

    def create(self, validated_data):
        return upsert_linked_race_record(
            user=self.context['user'],
            race=self.context['race'],
            result_data=validated_data,
        )
