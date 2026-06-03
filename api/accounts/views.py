import logging
import random
import secrets
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.analytics import track

from .models import EmailVerification, PendingSocialLogin, RaceRecord, SocialAccount, UserProfile
from .providers import OAuthError, get_provider
from .serializers import (
    EmailSendSerializer,
    NicknameSetupSerializer,
    OnboardingSerializer,
    ProfilePreferencesSerializer,
    RaceRecordCreateSerializer,
    RaceRecordSerializer,
    UserMeSerializer,
)
from .tokens import create_access_token

logger = logging.getLogger(__name__)
User = get_user_model()
PENDING_SOCIAL_LOGIN_TTL = timezone.timedelta(minutes=30)


def coalesce_email(current_value: str, new_value: str) -> str:
    """Keep the existing email when the provider no longer returns one."""
    return (new_value or current_value or '').strip()


def generate_verification_code() -> str:
    return ''.join(random.choices(string.digits, k=6))


def parse_checkbox_value(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {'1', 'true', 'on', 'yes'}


def send_verification_email(email: str, code: str) -> None:
    html_message = render_to_string('emails/verification_code.html', {'code': code})
    send_mail(
        subject='[EnduroHub] 이메일 인증 코드',
        message=f'인증 코드: {code}\n\n이 코드는 10분간 유효합니다.',
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


def get_pending_social_login(request) -> PendingSocialLogin | None:
    pending_token = (
        request.data.get('pending_token', '').strip()
        or request.COOKIES.get('pending_social_token', '').strip()
    )
    if not pending_token:
        return None

    return PendingSocialLogin.objects.filter(
        token=pending_token,
        updated_at__gte=timezone.now() - PENDING_SOCIAL_LOGIN_TTL,
    ).first()


def ensure_profile(
    user,
    user_info: dict,
    mark_email_verified: bool = False,
    email_updates_opt_in: bool | None = None,
):
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'profile_image': user_info.get('profile_image', ''),
            'email_verified': mark_email_verified,
            'email_updates_opt_in': email_updates_opt_in if email_updates_opt_in is not None else False,
        },
    )

    updated_fields: list[str] = []
    if not profile.profile_image and user_info.get('profile_image'):
        profile.profile_image = user_info['profile_image']
        updated_fields.append('profile_image')
    if mark_email_verified and not profile.email_verified:
        profile.email_verified = True
        updated_fields.append('email_verified')
    if email_updates_opt_in is not None and profile.email_updates_opt_in != email_updates_opt_in:
        profile.email_updates_opt_in = email_updates_opt_in
        updated_fields.append('email_updates_opt_in')
    if updated_fields:
        updated_fields.append('updated_at')
        profile.save(update_fields=updated_fields)

    return profile, created


def build_auth_response(
    request,
    user,
    user_info: dict,
    provider: str,
    is_new_user: bool,
    mark_email_verified: bool = False,
    email_updates_opt_in: bool | None = None,
):
    profile, _ = ensure_profile(
        user,
        user_info,
        mark_email_verified=mark_email_verified,
        email_updates_opt_in=email_updates_opt_in,
    )
    jwt_token = create_access_token(user.id)

    track('auth_login', request, {
        'provider': provider,
        'is_new_user': is_new_user,
    }, user=user)

    return Response({
        'token': jwt_token,
        'user': UserMeSerializer(profile).data,
    })


class OAuthLoginView(APIView):
    """POST /api/v1/auth/{provider}/login/ — returns OAuth authorize URL."""

    def post(self, request, provider):
        try:
            oauth = get_provider(provider)
        except OAuthError:
            return Response(
                {'error': '지원하지 않는 소셜 로그인입니다.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        redirect_uri = request.data.get('redirect_uri', '')
        if not redirect_uri:
            return Response(
                {'error': 'redirect_uri가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        kwargs = {'redirect_uri': redirect_uri}
        if provider == 'naver':
            state = secrets.token_urlsafe(16)
            kwargs['state'] = state

        authorize_url = oauth.get_authorize_url(**kwargs)

        response_data = {'authorize_url': authorize_url}
        if provider == 'naver':
            response_data['state'] = state

        return Response(response_data)


class OAuthCallbackView(APIView):
    """POST /api/v1/auth/{provider}/callback/ — exchange code for JWT."""

    def post(self, request, provider):
        try:
            oauth = get_provider(provider)
        except OAuthError:
            return Response(
                {'error': '지원하지 않는 소셜 로그인입니다.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        code = request.data.get('code', '')
        redirect_uri = request.data.get('redirect_uri', '')
        state = request.data.get('state', '')

        if not code or not redirect_uri:
            return Response(
                {'error': 'code와 redirect_uri가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Exchange code for tokens
            kwargs = {'code': code, 'redirect_uri': redirect_uri}
            if provider == 'naver':
                kwargs['state'] = state
            token_data = oauth.exchange_code(**kwargs)

            access_token = token_data.get('access_token', '')
            refresh_token = token_data.get('refresh_token', '')

            # Get user info from provider
            user_info = oauth.get_user_info(access_token)
        except OAuthError as e:
            logger.error('OAuth error', extra={'provider': provider, 'error': str(e)})
            return Response(
                {'error': '소셜 로그인에 실패했습니다. 다시 시도해주세요.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        provider_uid = user_info['provider_uid']
        email = user_info.get('email', '').strip()

        social_account = SocialAccount.objects.filter(
            provider=provider,
            provider_uid=provider_uid,
        ).select_related('user', 'user__profile').first()

        if social_account:
            email = coalesce_email(social_account.email, email)
            social_account.access_token = access_token
            social_account.refresh_token = refresh_token
            social_account.email = email
            social_account.extra_data = user_info
            social_account.save(update_fields=[
                'access_token', 'refresh_token', 'email', 'extra_data', 'updated_at',
            ])
            user = social_account.user
            if email and user.email != email:
                user.email = email
                user.save(update_fields=['email'])
            PendingSocialLogin.objects.filter(provider=provider, provider_uid=provider_uid).delete()
            return build_auth_response(
                request, user, user_info, provider, is_new_user=False,
            )

        if not email:
            pending_token = secrets.token_urlsafe(32)
            pending_social, _ = PendingSocialLogin.objects.update_or_create(
                provider=provider,
                provider_uid=provider_uid,
                defaults={
                    'token': pending_token,
                    'email': '',
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'extra_data': user_info,
                    'verification_code': '',
                    'verification_expires_at': None,
                },
            )
            return Response({
                'pendingToken': pending_social.token,
            })

        existing_social = SocialAccount.objects.filter(
            email__iexact=email,
        ).select_related('user').first()
        existing_user = User.objects.filter(email__iexact=email).first()

        is_new_user = False
        if existing_social:
            user = existing_social.user
        elif existing_user:
            user = existing_user
        else:
            username = f'{provider}_{provider_uid}'
            user = User.objects.create_user(
                username=username,
                email=email,
            )
            is_new_user = True

        if user.email != email:
            user.email = email
            user.save(update_fields=['email'])

        SocialAccount.objects.create(
            user=user,
            provider=provider,
            provider_uid=provider_uid,
            email=email,
            access_token=access_token,
            refresh_token=refresh_token,
            extra_data=user_info,
        )
        PendingSocialLogin.objects.filter(provider=provider, provider_uid=provider_uid).delete()

        return build_auth_response(
            request, user, user_info, provider, is_new_user=is_new_user,
        )


class NicknameSetupView(APIView):
    """POST /api/v1/auth/nickname/ — set nickname after first login."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = NicknameSetupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        nickname = serializer.validated_data['nickname']

        profile, _ = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'nickname': nickname},
        )
        if profile.nickname != nickname:
            profile.nickname = nickname
            profile.save(update_fields=['nickname', 'updated_at'])

        return Response({
            'success': True,
            'user': UserMeSerializer(profile).data,
        })


class EmailSendView(APIView):
    """POST /api/v1/auth/email/send/ — send verification code email."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = EmailSendSerializer(data=request.data, context={'user': user})
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        email = serializer.validated_data['email']
        profile, _ = UserProfile.objects.get_or_create(user=user)

        if user.email != email:
            user.email = email
            user.save(update_fields=['email'])

        if profile.email_verified:
            profile.email_verified = False
            profile.save(update_fields=['email_verified', 'updated_at'])

        # Check for recent verification to prevent spam
        recent = EmailVerification.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timezone.timedelta(minutes=1),
        ).exists()
        if recent:
            return Response(
                {'error': '1분 후에 다시 시도해주세요.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        code = generate_verification_code()
        expires_at = timezone.now() + timezone.timedelta(minutes=10)

        EmailVerification.objects.create(
            user=user,
            email=email,
            code=code,
            expires_at=expires_at,
        )

        try:
            send_verification_email(email, code)
        except Exception:
            logger.exception('Failed to send verification email', extra={'email': email})
            return Response(
                {'error': '이메일 발송에 실패했습니다. 잠시 후 다시 시도해주세요.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({
            'success': True,
            'message': f'{email}로 인증 코드를 발송했습니다.',
        })


class PendingSocialEmailSendView(APIView):
    """POST /api/v1/auth/pending/email/send/ — verify email for pending social login."""

    def post(self, request):
        pending_social = get_pending_social_login(request)
        if not pending_social:
            return Response(
                {'error': '진행 중인 소셜 로그인 정보를 찾을 수 없습니다. 다시 로그인해주세요.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = EmailSendSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if (
            pending_social.verification_code
            and pending_social.updated_at >= timezone.now() - timezone.timedelta(minutes=1)
        ):
            return Response(
                {'error': '1분 후에 다시 시도해주세요.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        email = serializer.validated_data['email']
        code = generate_verification_code()

        pending_social.email = email
        pending_social.verification_code = code
        pending_social.verification_expires_at = timezone.now() + timezone.timedelta(minutes=10)
        pending_social.save(update_fields=[
            'email', 'verification_code', 'verification_expires_at', 'updated_at',
        ])

        try:
            send_verification_email(email, code)
        except Exception:
            logger.exception('Failed to send pending social verification email', extra={'email': email})
            return Response(
                {'error': '이메일 발송에 실패했습니다. 잠시 후 다시 시도해주세요.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({
            'success': True,
            'message': f'{email}로 인증 코드를 발송했습니다.',
        })


class EmailVerifyView(APIView):
    """POST /api/v1/auth/email/verify/ — verify email with code."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get('code', '').strip()
        email_updates_opt_in = parse_checkbox_value(request.data.get('email_updates_opt_in'))
        if not code or len(code) != 6:
            return Response(
                {'errors': {'code': ['6자리 인증 코드를 입력해주세요.']}},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        verification = EmailVerification.objects.filter(
            user=request.user,
            code=code,
            is_used=False,
            expires_at__gte=timezone.now(),
        ).order_by('-created_at').first()

        if not verification:
            return Response(
                {'errors': {'code': ['유효하지 않거나 만료된 인증 코드입니다.']}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        verification.is_used = True
        verification.save(update_fields=['is_used'])

        # Mark profile as verified
        profile = UserProfile.objects.get(user=request.user)
        updated_fields = ['updated_at']
        if not profile.email_verified:
            profile.email_verified = True
            updated_fields.append('email_verified')
        if profile.email_updates_opt_in != email_updates_opt_in:
            profile.email_updates_opt_in = email_updates_opt_in
            updated_fields.append('email_updates_opt_in')
        profile.save(update_fields=updated_fields)

        return Response({
            'success': True,
            'message': '이메일 인증이 완료되었습니다.',
            'user': UserMeSerializer(profile).data,
        })


class PendingSocialEmailVerifyView(APIView):
    """POST /api/v1/auth/pending/email/verify/ — finish social signup after email verification."""

    def post(self, request):
        pending_social = get_pending_social_login(request)
        email_updates_opt_in = parse_checkbox_value(request.data.get('email_updates_opt_in'))
        if not pending_social:
            return Response(
                {'error': '진행 중인 소셜 로그인 정보를 찾을 수 없습니다. 다시 로그인해주세요.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        code = request.data.get('code', '').strip()
        if not code or len(code) != 6:
            return Response(
                {'errors': {'code': ['6자리 인증 코드를 입력해주세요.']}},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if (
            pending_social.verification_code != code
            or not pending_social.verification_expires_at
            or pending_social.verification_expires_at < timezone.now()
        ):
            return Response(
                {'errors': {'code': ['유효하지 않거나 만료된 인증 코드입니다.']}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = pending_social.email.strip().lower()
        if not email:
            return Response(
                {'errors': {'email': ['이메일을 먼저 입력해주세요.']}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        social_account = SocialAccount.objects.filter(
            provider=pending_social.provider,
            provider_uid=pending_social.provider_uid,
        ).select_related('user').first()
        existing_social = SocialAccount.objects.filter(email__iexact=email).select_related('user').first()
        existing_user = User.objects.filter(email__iexact=email).first()

        is_new_user = False
        if social_account:
            user = social_account.user
        elif existing_social:
            user = existing_social.user
        elif existing_user:
            user = existing_user
        else:
            user = User.objects.create_user(
                username=f'{pending_social.provider}_{pending_social.provider_uid}',
                email=email,
            )
            is_new_user = True

        if user.email != email:
            user.email = email
            user.save(update_fields=['email'])

        if not social_account:
            SocialAccount.objects.create(
                user=user,
                provider=pending_social.provider,
                provider_uid=pending_social.provider_uid,
                email=email,
                access_token=pending_social.access_token,
                refresh_token=pending_social.refresh_token,
                extra_data=pending_social.extra_data,
            )
        else:
            social_account.email = email
            social_account.access_token = pending_social.access_token
            social_account.refresh_token = pending_social.refresh_token
            social_account.extra_data = pending_social.extra_data
            social_account.save(update_fields=[
                'email', 'access_token', 'refresh_token', 'extra_data', 'updated_at',
            ])

        pending_social.delete()

        return build_auth_response(
            request,
            user,
            pending_social.extra_data,
            pending_social.provider,
            is_new_user=is_new_user,
            mark_email_verified=True,
            email_updates_opt_in=email_updates_opt_in,
        )


class MeView(APIView):
    """GET /api/v1/auth/me/ — current user info (optional auth)."""

    def get(self, request):
        if not request.user or not request.user.is_authenticated:
            return Response({'user': None})

        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return Response({'user': None})

        return Response({
            'user': UserMeSerializer(profile).data,
        })


class ProfilePreferencesView(APIView):
    """POST /api/v1/auth/preferences/ — update profile preferences."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProfilePreferencesSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return Response(
                {'errors': {'profile': ['프로필 정보를 찾을 수 없습니다. 다시 로그인해주세요.']}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if profile.email_updates_opt_in != serializer.validated_data['email_updates_opt_in']:
            profile.email_updates_opt_in = serializer.validated_data['email_updates_opt_in']
            profile.save(update_fields=['email_updates_opt_in', 'updated_at'])

        return Response({
            'success': True,
            'message': '알림 설정이 저장되었습니다.',
            'user': UserMeSerializer(profile).data,
        })


class OnboardingView(APIView):
    """POST /api/v1/auth/onboarding/ — save preferences and trigger welcome email."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OnboardingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return Response(
                {'errors': {'profile': ['프로필 정보를 찾을 수 없습니다.']}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        preferred_sports = serializer.validated_data.get('preferred_sports') or []
        preferred_regions = serializer.validated_data.get('preferred_regions') or []

        updated_fields = ['onboarding_completed', 'updated_at']
        profile.onboarding_completed = True
        if preferred_sports:
            profile.preferred_sports = preferred_sports
            updated_fields.append('preferred_sports')
        if preferred_regions:
            profile.preferred_regions = preferred_regions
            updated_fields.append('preferred_regions')

        profile.save(update_fields=updated_fields)

        # Trigger welcome email asynchronously
        if profile.email_verified and not profile.welcome_email_sent:
            try:
                from accounts.tasks import send_welcome_email_task
                send_welcome_email_task.delay(request.user.id)
            except Exception:
                logger.exception('Failed to queue welcome email for user %s', request.user.id)

        return Response({
            'success': True,
            'message': '관심사가 저장되었습니다.',
            'user': UserMeSerializer(profile).data,
        })


class RaceRecordListCreateView(APIView):
    """GET/POST /api/v1/me/records/ — list or add the current user's race records.

    POST accepts a single record object or a list of records (bulk create from
    the onboarding records step).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        records = RaceRecord.objects.filter(user=request.user)
        return Response({'records': RaceRecordSerializer(records, many=True).data})

    def post(self, request):
        payload = request.data
        items = payload if isinstance(payload, list) else [payload]

        created: list[RaceRecord] = []
        first_error = None
        for item in items:
            serializer = RaceRecordCreateSerializer(data=item, context={'user': request.user})
            if not serializer.is_valid():
                if first_error is None:
                    first_error = serializer.errors
                continue
            created.append(serializer.save())

        if not created:
            return Response(
                {'errors': first_error or {'records': ['저장할 기록이 없습니다.']}},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        return Response(
            {'records': RaceRecordSerializer(created, many=True).data},
            status=status.HTTP_201_CREATED,
        )


class RaceRecordDetailView(APIView):
    """DELETE /api/v1/me/records/{id}/ — remove one of the current user's records."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        deleted, _ = RaceRecord.objects.filter(user=request.user, pk=pk).delete()
        if not deleted:
            return Response(
                {'error': '기록을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({'success': True})


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — placeholder for future token blacklist."""

    def post(self, request):
        return Response({'success': True, 'message': '로그아웃되었습니다.'})


class MyFavoriteRacesView(APIView):
    """GET /api/v1/me/favorites/races/ — paginated list of current user's favorite races."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from core.pagination import LaravelStylePagination
        from races.models import Race, RaceFavorite
        from races.serializers import RaceSerializer

        favorite_race_ids_qs = RaceFavorite.objects.filter(
            user=request.user,
        ).order_by('-created_at').values_list('race_id', flat=True)

        favorite_ids = list(favorite_race_ids_qs)
        id_order = {race_id: idx for idx, race_id in enumerate(favorite_ids)}
        races = list(Race.objects.filter(id__in=favorite_ids))
        races.sort(key=lambda r: id_order.get(r.id, 0))

        paginator = LaravelStylePagination()
        per_page = request.query_params.get('per_page')
        if per_page:
            paginator.page_size = min(int(per_page), 100)

        page = paginator.paginate_queryset(races, request)
        favorite_set = set(favorite_ids)
        serializer = RaceSerializer(
            page, many=True,
            context={'favorite_race_ids': favorite_set},
        )
        return paginator.get_paginated_response(serializer.data)
