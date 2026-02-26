from django.conf import settings


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
