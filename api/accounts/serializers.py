import re

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import SocialAccount, UserProfile

User = get_user_model()


class UserMeSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='user.id')
    email = serializers.CharField(source='user.email', allow_blank=True)
    nickname = serializers.CharField()
    profile_image = serializers.URLField(allow_blank=True)
    email_verified = serializers.BooleanField()
    email_updates_opt_in = serializers.BooleanField()
    needs_nickname = serializers.SerializerMethodField()
    needs_email_verification = serializers.SerializerMethodField()

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
