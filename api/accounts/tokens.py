import time

import jwt
from django.conf import settings


JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_LIFETIME = 60 * 60 * 24 * 7  # 7 days


def create_access_token(user_id: int) -> str:
    now = int(time.time())
    payload = {
        'user_id': user_id,
        'iat': now,
        'exp': now + JWT_ACCESS_TOKEN_LIFETIME,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
