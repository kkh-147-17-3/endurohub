from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication

from .tokens import decode_access_token

User = get_user_model()


class JWTAuthentication(BaseAuthentication):
    """
    Custom JWT authentication via Authorization header or auth_token cookie.
    """

    def authenticate(self, request):
        token = self._get_token(request)
        if not token:
            return None

        payload = decode_access_token(token)
        if not payload:
            return None

        user_id = payload.get('user_id')
        if not user_id:
            return None

        try:
            user = User.objects.select_related('profile').get(pk=user_id)
        except User.DoesNotExist:
            return None

        return (user, token)

    def _get_token(self, request):
        # 1. Check Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]

        # 2. Check cookie
        return request.COOKIES.get('auth_token')
