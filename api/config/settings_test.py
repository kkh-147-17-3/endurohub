"""테스트 전용 설정 — Postgres 없이 로컬/CI에서 돌릴 수 있게 SQLite 사용."""
from .settings import *  # noqa: F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

CELERY_TASK_ALWAYS_EAGER = True
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Postgres 전용 데이터 마이그레이션(예: 0004_json_to_jsonb)을 피하기 위해
# 프로젝트 앱은 마이그레이션 없이 현재 모델 상태로 테이블을 생성한다.
MIGRATION_MODULES = {
    'core': None,
    'races': None,
    'posts': None,
    'accounts': None,
    'notices': None,
    'rewards': None,
}
