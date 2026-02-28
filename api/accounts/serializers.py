import re

from rest_framework import serializers

from .models import UserProfile


class UserMeSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='user.id')
    email = serializers.EmailField(source='user.email')
    nickname = serializers.CharField()
    profile_image = serializers.URLField(allow_blank=True)
    email_verified = serializers.BooleanField()
    needs_nickname = serializers.SerializerMethodField()
    needs_email_verification = serializers.SerializerMethodField()

    def get_needs_nickname(self, obj):
        return not obj.nickname

    def get_needs_email_verification(self, obj):
        return bool(obj.nickname) and not obj.email_verified


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
