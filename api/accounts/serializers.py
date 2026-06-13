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
            'record_date', 'duration_seconds', 'time', 'is_public', 'created_at',
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


class RaceResultCreateSerializer(serializers.Serializer):
    """Log a finish for a curated race → a RaceRecord linked to that race.

    Requires the target Race in context['race']. Derives sport from the race
    and the distance label from the matching course when possible.
    """

    course_code = serializers.CharField(max_length=20)
    hours = serializers.IntegerField(required=False, min_value=0, max_value=99, default=0)
    minutes = serializers.IntegerField(required=False, min_value=0, max_value=59, default=0)
    seconds = serializers.IntegerField(required=False, min_value=0, max_value=59, default=0)
    is_personal_best = serializers.BooleanField(required=False, default=False)
    is_public = serializers.BooleanField(required=False, default=False)

    def validate_course_code(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('완주한 종목을 선택해주세요.')
        race = self.context['race']
        codes = {course_code_for(d) for d in (race.distances or []) if isinstance(d, dict)}
        # Only enforce when the race actually publishes course distances.
        if codes and value not in codes:
            raise serializers.ValidationError(f'이 대회에 없는 종목입니다: {value}')
        return value

    def validate(self, attrs):
        total = attrs.get('hours', 0) * 3600 + attrs.get('minutes', 0) * 60 + attrs.get('seconds', 0)
        if total <= 0:
            raise serializers.ValidationError({'time': ['기록 시간을 입력해주세요.']})
        attrs['duration_seconds'] = total
        return attrs

    def create(self, validated_data):
        race = self.context['race']
        user = self.context['user']
        code = validated_data['course_code']
        # Resolve a human label for the chosen course.
        label = code
        for d in race.distances or []:
            if isinstance(d, dict) and course_code_for(d) == code:
                label = d.get('name') or code
                break

        record, _ = RaceRecord.objects.update_or_create(
            user=user,
            race=race,
            defaults={
                'sport': race.sport,
                'distance': label,
                'course_code': code,
                'name': race.title,
                'record_date': race.race_date.isoformat() if race.race_date else '',
                'duration_seconds': validated_data['duration_seconds'],
                'is_personal_best': validated_data.get('is_personal_best', False),
                'is_public': validated_data.get('is_public', False),
            },
        )
        return record
