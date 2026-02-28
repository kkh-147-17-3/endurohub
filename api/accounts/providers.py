import httpx
from django.conf import settings


class OAuthError(Exception):
    pass


class KakaoOAuth:
    AUTHORIZE_URL = 'https://kauth.kakao.com/oauth/authorize'
    TOKEN_URL = 'https://kauth.kakao.com/oauth/token'
    USER_INFO_URL = 'https://kapi.kakao.com/v2/user/me'

    @classmethod
    def get_authorize_url(cls, redirect_uri: str) -> str:
        params = {
            'client_id': settings.KAKAO_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'account_email profile_nickname profile_image',
        }
        qs = '&'.join(f'{k}={v}' for k, v in params.items())
        return f'{cls.AUTHORIZE_URL}?{qs}'

    @classmethod
    def exchange_code(cls, code: str, redirect_uri: str) -> dict:
        resp = httpx.post(cls.TOKEN_URL, data={
            'grant_type': 'authorization_code',
            'client_id': settings.KAKAO_CLIENT_ID,
            'client_secret': settings.KAKAO_CLIENT_SECRET,
            'redirect_uri': redirect_uri,
            'code': code,
        })
        if resp.status_code != 200:
            raise OAuthError(f'Kakao token exchange failed: {resp.text}')
        return resp.json()

    @classmethod
    def get_user_info(cls, access_token: str) -> dict:
        resp = httpx.get(cls.USER_INFO_URL, headers={
            'Authorization': f'Bearer {access_token}',
        })
        if resp.status_code != 200:
            raise OAuthError(f'Kakao user info failed: {resp.text}')
        data = resp.json()
        account = data.get('kakao_account', {})
        profile = account.get('profile', {})
        return {
            'provider': 'kakao',
            'provider_uid': str(data['id']),
            'email': account.get('email', ''),
            'nickname': profile.get('nickname', ''),
            'profile_image': profile.get('profile_image_url', ''),
        }


class NaverOAuth:
    AUTHORIZE_URL = 'https://nid.naver.com/oauth2.0/authorize'
    TOKEN_URL = 'https://nid.naver.com/oauth2.0/token'
    USER_INFO_URL = 'https://openapi.naver.com/v1/nid/me'

    @classmethod
    def get_authorize_url(cls, redirect_uri: str, state: str = '') -> str:
        params = {
            'client_id': settings.NAVER_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'state': state,
        }
        qs = '&'.join(f'{k}={v}' for k, v in params.items())
        return f'{cls.AUTHORIZE_URL}?{qs}'

    @classmethod
    def exchange_code(cls, code: str, redirect_uri: str, state: str = '') -> dict:
        resp = httpx.post(cls.TOKEN_URL, data={
            'grant_type': 'authorization_code',
            'client_id': settings.NAVER_CLIENT_ID,
            'client_secret': settings.NAVER_CLIENT_SECRET,
            'redirect_uri': redirect_uri,
            'code': code,
            'state': state,
        })
        if resp.status_code != 200:
            raise OAuthError(f'Naver token exchange failed: {resp.text}')
        return resp.json()

    @classmethod
    def get_user_info(cls, access_token: str) -> dict:
        resp = httpx.get(cls.USER_INFO_URL, headers={
            'Authorization': f'Bearer {access_token}',
        })
        if resp.status_code != 200:
            raise OAuthError(f'Naver user info failed: {resp.text}')
        data = resp.json().get('response', {})
        return {
            'provider': 'naver',
            'provider_uid': data.get('id', ''),
            'email': data.get('email', ''),
            'nickname': data.get('nickname', ''),
            'profile_image': data.get('profile_image', ''),
        }


class GoogleOAuth:
    AUTHORIZE_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
    TOKEN_URL = 'https://oauth2.googleapis.com/token'
    USER_INFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'

    @classmethod
    def get_authorize_url(cls, redirect_uri: str) -> str:
        params = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'email profile',
            'access_type': 'offline',
            'prompt': 'consent',
        }
        qs = '&'.join(f'{k}={v}' for k, v in params.items())
        return f'{cls.AUTHORIZE_URL}?{qs}'

    @classmethod
    def exchange_code(cls, code: str, redirect_uri: str) -> dict:
        resp = httpx.post(cls.TOKEN_URL, data={
            'grant_type': 'authorization_code',
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': redirect_uri,
            'code': code,
        })
        if resp.status_code != 200:
            raise OAuthError(f'Google token exchange failed: {resp.text}')
        return resp.json()

    @classmethod
    def get_user_info(cls, access_token: str) -> dict:
        resp = httpx.get(cls.USER_INFO_URL, headers={
            'Authorization': f'Bearer {access_token}',
        })
        if resp.status_code != 200:
            raise OAuthError(f'Google user info failed: {resp.text}')
        data = resp.json()
        return {
            'provider': 'google',
            'provider_uid': data.get('id', ''),
            'email': data.get('email', ''),
            'nickname': data.get('name', ''),
            'profile_image': data.get('picture', ''),
        }


PROVIDERS = {
    'kakao': KakaoOAuth,
    'naver': NaverOAuth,
    'google': GoogleOAuth,
}


def get_provider(name: str):
    provider = PROVIDERS.get(name)
    if not provider:
        raise OAuthError(f'Unknown provider: {name}')
    return provider
