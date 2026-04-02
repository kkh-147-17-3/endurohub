# EnduroHub

대한민국 endurance sports 커뮤니티 플랫폼. 마라톤, 수영, 사이클, 트라이애슬론, 트레일러닝 대회 정보를 제공하고 커뮤니티 기능을 지원합니다.

## Tech Stack

- **Backend**: Django REST Framework, PostgreSQL, Gunicorn
- **Frontend**: SvelteKit (SSR), Svelte 5, Tailwind CSS, DaisyUI
- **Infra**: Docker Compose, Nginx
- **외부 서비스**: Kakao/Naver/Google OAuth, Sentry, Google Analytics, Gemini AI

## 주요 기능

- **대회 검색 및 필터링** — 종목, 지역, 상태, 거리, 기간별 필터
- **대회 캘린더** — 월별/연도별 대회 일정 조회
- **커뮤니티 게시판** — 리뷰, 훈련 팁, 장비 추천, 질문 등
- **대회 리뷰** — 평점, 코스 난이도, 운영 만족도 평가
- **훈련 도구** — 페이스 계산기, 레이스 예측기, VO2max 계산기, 훈련 계획
- **소셜 로그인** — 카카오, 네이버, 구글 OAuth

## 프로젝트 구조

```
api/          # Django REST API (accounts, races, posts, core)
web/          # SvelteKit 프론트엔드
nginx/        # Nginx 리버스 프록시 설정
```

## 시작하기

```bash
# 환경변수 설정
cp .env.example .env
# .env 파일에 DB, OAuth 키 등 입력

# 개발 환경 실행
docker-compose -f docker-compose.dev.yml up

# 프로덕션 실행
docker-compose up -d
```

| 서비스 | 포트 |
|--------|------|
| Web    | 3000 |
| API    | 8000 |
| Nginx  | 80   |
