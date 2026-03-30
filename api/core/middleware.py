import hashlib
import logging
import time

from django.conf import settings

from core.notifications import notify_server_error

request_logger = logging.getLogger('api.request')

IGNORED_PATHS = frozenset({'/health', '/favicon.ico'})


class RequestLoggingMiddleware:
    """모든 API 요청을 JSON 구조화 로그로 기록한다."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in IGNORED_PATHS:
            return self.get_response(request)

        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - start) * 1000)

        request_logger.info('', extra={
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration_ms': duration_ms,
            'query': request.META.get('QUERY_STRING', '') or None,
            'user_id': getattr(request.user, 'id', None),
            'ip': request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
                  or request.META.get('REMOTE_ADDR'),
        })
        return response


class ErrorNotificationMiddleware:
    """500 에러 발생 시 Telegram으로 알림을 보낸다. 동일 에러는 60초간 중복 전송하지 않는다."""

    _recent_errors = {}
    COOLDOWN = 60  # seconds

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # 중복 알림 방지: 같은 에러 타입+경로는 60초간 1번만
        key = hashlib.md5(
            f'{type(exception).__name__}:{request.path}'.encode()
        ).hexdigest()
        now = time.time()

        if key in self._recent_errors and now - self._recent_errors[key] < self.COOLDOWN:
            return None

        self._recent_errors[key] = now

        # 오래된 항목 정리
        cutoff = now - self.COOLDOWN
        self._recent_errors = {
            k: v for k, v in self._recent_errors.items() if v > cutoff
        }

        notify_server_error(request, exception)
        return None


class AdminTokenCookieMiddleware:
    """
    Django Admin에 로그인한 staff 유저에게 admin_token 쿠키를 설정한다.
    SvelteKit이 이 쿠키를 읽어 isAdmin 여부를 판별한다.
    로그아웃하면 쿠키를 삭제한다.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        admin_secret = getattr(settings, 'ADMIN_SECRET', '')
        if not admin_secret:
            return response

        cookie_name = 'admin_token'
        has_cookie = cookie_name in request.COOKIES

        if request.user.is_authenticated and request.user.is_staff:
            if not has_cookie or request.COOKIES[cookie_name] != admin_secret:
                response.set_cookie(
                    cookie_name,
                    admin_secret,
                    path='/',
                    httponly=True,
                    samesite='Lax',
                    secure=not settings.DEBUG,
                    max_age=60 * 60 * 24 * 7,  # 7 days
                )
        else:
            if has_cookie:
                response.delete_cookie(cookie_name, path='/')

        return response
