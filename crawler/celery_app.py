"""크롤러 전용 Celery 워커 — api 의 beat 가 이름('crawler.enrich')으로 발행한 태스크를 받는다.

api 컨테이너와 브로커(redis)만 공유하고 코드는 공유하지 않는다:
  - beat 쪽: settings.CELERY_BEAT_SCHEDULE 에서 task='crawler.enrich', queue='crawler' 로 발행
  - 이 워커: celery -A crawler.celery_app worker -Q crawler
DB 접근은 admin API(HTTP)로만 한다 — Django 비의존 원칙 유지.
"""
import os

from celery import Celery

from . import config  # noqa: F401 — .env 로드 부수효과


def _broker_url() -> str:
    url = os.environ.get("CELERY_BROKER_URL")
    if url:
        return url
    host = os.environ.get("REDIS_HOST", "localhost")
    port = os.environ.get("REDIS_PORT", "6379")
    password = os.environ.get("REDIS_PASSWORD", "")
    auth = f":{password}@" if password else ""
    return f"redis://{auth}{host}:{port}/0"


app = Celery("crawler", broker=_broker_url())
app.conf.update(
    task_default_queue="crawler",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    task_ignore_result=True,
    worker_concurrency=1,          # Playwright 브라우저를 띄우므로 동시 실행 1개로 제한
)


@app.task(name="crawler.enrich")
def enrich_task(limit=None, dry_run=False):
    from .enrich import run

    return run(limit=limit, dry_run=dry_run)
