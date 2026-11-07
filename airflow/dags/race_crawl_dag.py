"""Roadrun 마라톤 크롤링 DAG (Airflow PoC).

기존 celery beat 의 crawl-marathon-hourly 잡과 동일한 작업을
DockerOperator 로 실행한다: api 이미지 컨테이너를 띄워
`python manage.py crawl_marathon` 을 수행하고 종료한다.
"""

import os
from datetime import datetime

from airflow.providers.docker.operators.docker import DockerOperator
from airflow.sdk import DAG

API_IMAGE = os.environ.get('CRAWL_API_IMAGE', 'endurohub-api')
CRAWL_NETWORK = os.environ.get('CRAWL_NETWORK', 'endurohub_default')

# docker-compose.dev.yml 의 api 서비스 environment 와 동일한 기본값
CRAWL_ENV = {
    'DATABASE_HOST': os.environ.get('DATABASE_HOST', 'postgres'),
    'DATABASE_PORT': os.environ.get('DATABASE_PORT', '5432'),
    'DATABASE_NAME': os.environ.get('DATABASE_NAME', 'endurohub'),
    'DATABASE_USER': os.environ.get('DATABASE_USER', 'enduro'),
    'DATABASE_PASSWORD': os.environ.get('DATABASE_PASSWORD', 'changeme'),
    'DJANGO_SECRET_KEY': os.environ.get('DJANGO_SECRET_KEY', 'dev-secret-key-not-for-production'),
    'DJANGO_DEBUG': 'false',
    'DJANGO_ALLOWED_HOSTS': 'localhost,127.0.0.1,api',
}

with DAG(
    dag_id='race_crawl',
    description='Roadrun 마라톤 목록 크롤링 (Airflow PoC)',
    schedule='0 * * * *',  # 매시 정각 — 기존 beat 스케줄과 동일
    start_date=datetime(2026, 9, 1),
    catchup=False,  # 과거 밀린 실행분을 소급 실행하지 않음
    default_args={'retries': 1},  # 실패 시 5분 뒤 1회 재시도
    tags=['crawler', 'poc'],
) as dag:
    crawl_marathon = DockerOperator(
        task_id='crawl_marathon',
        image=API_IMAGE,
        command='python manage.py crawl_marathon',
        environment=CRAWL_ENV,
        network_mode=CRAWL_NETWORK,
        auto_remove='success',
        mount_tmp_dir=False,  # Windows Docker Desktop 에서 tmp 마운트 오류 방지
    )
