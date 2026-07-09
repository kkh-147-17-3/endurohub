FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    # Playwright chromium + OS 의존 라이브러리 (이미지가 커지는 주범이지만 필수)
    && playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

# 패키지 형태(crawler.*)로 임포트되도록 /app/crawler 아래에 복사
COPY . ./crawler

CMD ["celery", "-A", "crawler.celery_app", "worker", "-Q", "crawler", "-l", "info"]
