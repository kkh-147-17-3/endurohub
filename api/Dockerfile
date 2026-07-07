FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# opentelemetry-instrument 가 wsgi/celery 임포트 전에 Django 계측을 초기화하므로
# DJANGO_SETTINGS_MODULE 이 환경변수로 미리 존재해야 한다. 없으면 settings 가
# 빈 UserSettingsHolder 로 굳어 ROOT_URLCONF 누락 → 모든 요청 500.
ENV DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# 설치된 라이브러리(Django/Celery/psycopg2/redis/httpx/requests 등)에 맞는
# OpenTelemetry instrumentation 패키지를 자동 탐지·설치한다.
RUN opentelemetry-bootstrap -a install

COPY . .

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
