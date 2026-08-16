import os
from pathlib import Path
from celery.schedules import crontab
import sentry_sdk

BASE_DIR = Path(__file__).resolve().parent.parent

# Sentry
SENTRY_DSN = os.environ.get('SENTRY_DSN', '')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        send_default_pii=False,
    )

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'insecure-dev-key-change-me')

DEBUG = os.environ.get('DJANGO_DEBUG', 'true').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,api').split(',')
print(f"[settings.py] ALLOWED_HOSTS={ALLOWED_HOSTS}  (raw env={os.environ.get('DJANGO_ALLOWED_HOSTS', 'UNSET')!r})")

# cloudflared 는 항상 평문으로 오리진에 붙으므로 Django 는 자기가 http 로 서비스된다고
# 믿는다. 그 결과 APPEND_SLASH 리다이렉트가 http:// 절대 URL 을 내보내고 있었다
# (/api → http://www.endurohub.kr/api/ → nginx 301 → https://…, 불필요한 2홉).
# 실제 클라이언트 스킴은 Cloudflare 가 붙여주는 X-Forwarded-Proto 에만 남아 있다.
# nginx 쪽도 함께 고쳐야 한다 — 예전엔 $scheme(항상 http)으로 이 헤더를 덮어써서
# 여기만 켜면 아무 효과가 없다. nginx/conf.d/default.conf 의 $forwarded_proto 참고.
# 신뢰 경계: 오리진은 cloudflared 터널로만 닿을 수 있고 Cloudflare 엣지가 이 헤더를
# 클라이언트 값 대신 자기가 판단한 값으로 덮어쓰므로 외부에서 위조할 수 없다.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'django_celery_beat',
    'core',
    'races',
    'posts',
    'accounts',
    'notices',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.RequestLoggingMiddleware',
    'core.middleware.ErrorNotificationMiddleware',
    'core.middleware.AdminTokenCookieMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DATABASE_NAME', 'endurohub'),
        'USER': os.environ.get('DATABASE_USER', 'enduro'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', ''),
        'HOST': os.environ.get('DATABASE_HOST', 'db'),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/storage/'
MEDIA_ROOT = BASE_DIR / 'storage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'djangorestframework_camel_case.render.CamelCaseJSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'djangorestframework_camel_case.parser.CamelCaseJSONParser',
        'djangorestframework_camel_case.parser.CamelCaseFormParser',
        'djangorestframework_camel_case.parser.CamelCaseMultiPartParser',
    ],
    'DEFAULT_PAGINATION_CLASS': None,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'accounts.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
}

# CSRF
CSRF_TRUSTED_ORIGINS = os.environ.get(
    'CSRF_TRUSTED_ORIGINS',
    'https://www.endurohub.kr,https://endurohub.kr,http://localhost'
).split(',')

# CORS
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://localhost:5173'
).split(',')
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True

# Admin secret (shared with SvelteKit for isAdmin cookie)
ADMIN_SECRET = os.environ.get('ADMIN_SECRET', '')

# Crawler API key
CRAWLER_API_KEY = os.environ.get('CRAWLER_API_KEY', '')

# OAuth providers
KAKAO_CLIENT_ID = os.environ.get('KAKAO_CLIENT_ID', '')
KAKAO_CLIENT_SECRET = os.environ.get('KAKAO_CLIENT_SECRET', '')
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID', '')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET', '')
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

# Email
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'contact@endurohub.kr')

# Slack
SLACK_BOT_USER_OAUTH_TOKEN = os.environ.get('SLACK_BOT_USER_OAUTH_TOKEN', '')

# Telegram (error notifications)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# Gemini (image generation)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_IMAGE_MODEL = os.environ.get('GEMINI_IMAGE_MODEL', 'gemini-2.0-flash-exp-image-generation')

# LLM — 자연어 대회 검색 파서
# provider: 'anthropic'(공식 SDK, Claude) | 'openai'(OpenAI 호환 HTTP, 로컬 LM Studio 등)
LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'openai').strip().lower()
LLM_API_KEY = os.environ.get('LLM_API_KEY', '')
# 모델 미지정 시 provider별 기본값을 코드에서 채운다 (anthropic→claude-opus-4-8, openai→gpt-4o-mini).
LLM_MODEL = os.environ.get('LLM_MODEL', '').strip()
LLM_TIMEOUT = float(os.environ.get('LLM_TIMEOUT', '8'))
# --- openai(호환) provider 전용 ---
LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1').rstrip('/')
# JSON 강제 모드: '' (프롬프트만, 모든 서버 호환·기본) | 'json_schema' (LM Studio·최신 OpenAI) | 'json_object' (OpenAI)
LLM_JSON_MODE = os.environ.get('LLM_JSON_MODE', '').strip()

# 끝난 대회 후기 요약 잡 전용 모델. 이 잡만 Responses API 의 web_search 툴을 쓰기 때문에
# 검색 품질이 다른 경로보다 결과를 크게 좌우한다 — nano 로 부실하면 여기만 올릴 수 있게
# 분리해 둔다(nl_search/reg_status 는 LLM_MODEL 을 그대로 쓴다).
AI_RECAP_MODEL = os.environ.get('AI_RECAP_MODEL', '').strip() or LLM_MODEL or 'gpt-5.4-nano'

# Storage URL for generating absolute image URLs
STORAGE_URL = os.environ.get('STORAGE_URL', '/storage/')

# App URL (for email links)
APP_URL = os.environ.get('APP_URL', 'https://www.endurohub.kr').rstrip('/')

# Crawl reporting
CRAWL_REPORT_EMAIL = os.environ.get('CRAWL_REPORT_EMAIL', 'kkh147.17.3@gmail.com')
CRAWL_SEND_EMPTY_REPORT = os.environ.get('CRAWL_SEND_EMPTY_REPORT', 'false').lower() in (
    'true', '1', 'yes'
)

# django-unfold
UNFOLD = {
    'SITE_TITLE': 'EnduroHub Admin',
    'SITE_HEADER': 'EnduroHub',
}

# File upload settings (match nginx client_max_body_size 20M)
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20MB

REDIS_HOST = os.environ.get('REDIS_HOST', 'host.docker.internal')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
_REDIS_AUTH = f':{REDIS_PASSWORD}@' if REDIS_PASSWORD else ''
_DEFAULT_REDIS_URL = f'redis://{_REDIS_AUTH}{REDIS_HOST}:{REDIS_PORT}/0'

# Cache — 브로커와 같은 Redis 인스턴스의 다른 DB(1번)를 쓴다. celery 가 0번을
# 쓰므로 키가 섞이지 않는다.
#
# 파일 기반(BASE_DIR/.cache)에서 옮겨왔다. 파일 캐시는 컨테이너 쓰기 레이어에
# 있어서 (a) 배포로 컨테이너가 새로 뜰 때마다 통째로 사라지고 (b) api 와
# celery-worker 가 서로 다른 캐시를 보게 된다 — 지금은 교차 무효화가 없어
# 문제가 안 됐지만 워커에서 캐시를 지우는 코드가 생기면 조용히 깨진다.
CACHE_URL = os.environ.get(
    'CACHE_URL', f'redis://{_REDIS_AUTH}{REDIS_HOST}:{REDIS_PORT}/1',
)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': CACHE_URL,
    }
}

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', _DEFAULT_REDIS_URL)
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    'crawl-marathon-hourly': {
        'task': 'races.tasks.crawl_marathon_task',
        'schedule': crontab(minute=0),
        'kwargs': {'with_details': True},
    },
    'weekly-digest-monday': {
        'task': 'accounts.tasks.send_weekly_digest_task',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),  # Monday 9AM KST
    },
    'new-races-alert-hourly': {
        'task': 'accounts.tasks.send_new_races_alert_task',
        'schedule': crontab(minute=5),  # Every hour at :05 (after crawl at :00)
    },
    'fetch-weather-daily': {
        'task': 'races.tasks.fetch_weather_task',
        'schedule': crontab(hour=6, minute=30),  # Daily 6:30 AM KST
    },
    'update-registration-status-daily': {
        'task': 'races.tasks.update_registration_status_task',
        'schedule': crontab(hour=12, minute=0),  # Daily noon KST
    },
    # 화 4AM — 매시 크롤(:00), 6:30 날씨, 8:00 enrich, 9:00 월요일 다이제스트,
    # 12:00 접수판정과 겹치지 않는 시간대.
    'generate-ai-recap-weekly': {
        'task': 'races.tasks.generate_ai_recap_task',
        'schedule': crontab(hour=4, minute=0, day_of_week=2),
    },
    # 이름으로만 발행 — 태스크 구현은 crawler-worker 컨테이너(crawler/celery_app.py)에 있다
    'crawler-enrich-daily': {
        'task': 'crawler.enrich',
        'schedule': crontab(hour=8, minute=0),  # Daily 8AM KST
        'options': {'queue': 'crawler'},
    },
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
            'rename_fields': {
                'asctime': 'timestamp',
                'name': 'logger',
                'levelname': 'level',
            },
        },
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json' if not DEBUG else 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO' if DEBUG else 'WARNING',
            'propagate': False,
        },
    },
}
