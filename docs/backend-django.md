# 엔듀로허브 백엔드 (Django) 구현 설명

엔듀로허브의 API 서버는 **Django 5.1 + Django REST Framework**로 구현되어 있다.
이 문서는 백엔드(`api/`)가 어떻게 짜여 있는지 — 앱 구조, 데이터 모델, API, 인증, 비동기 작업,
데이터 크롤링, 운영 장치 — 를 코드 기준으로 정리한 것이다.

> 관련 문서: 서비스 전체 소개는 [PORTFOLIO.md](../PORTFOLIO.md) 참고.

---

## 1. 프로젝트 구조

`config` 프로젝트 아래에 도메인별 앱 4개(`core`·`races`·`posts`·`accounts`)로 나뉜다.

```
api/
├── config/            # 프로젝트 설정
│   ├── settings.py    # DRF·Celery·로깅·외부서비스 설정 일괄
│   ├── celery.py      # Celery 앱 (autodiscover_tasks)
│   ├── urls.py        # 루트 URLConf (/dj-admin, /api/v1)
│   └── wsgi.py
├── core/              # 공통: 분석·미들웨어·유틸·예외·알림
├── races/             # 대회 도메인 (핵심): 모델·API·크롤러·어드민·커맨드
├── posts/             # 커뮤니티: 게시글·댓글·좋아요
└── accounts/          # 인증: OAuth·프로필·이메일 인증·내 기록
```

**`INSTALLED_APPS` 핵심** (`config/settings.py`)
- `unfold` (django-admin 확장, 맨 앞에 위치해야 함) + `unfold.contrib.filters`
- `rest_framework`, `corsheaders`, `django_celery_beat`
- 자체 앱: `core`, `races`, `posts`, `accounts`

**기본 설정**
- `LANGUAGE_CODE = 'ko-kr'`, `TIME_ZONE = 'Asia/Seoul'`, `USE_TZ = True`
- DB: PostgreSQL (`django.db.backends.postgresql`), 환경변수로 접속 정보 주입
- 미디어: `MEDIA_URL = '/storage/'`, 정적: `STATIC_URL = '/static/'`
- 업로드 한도 20MB (nginx `client_max_body_size`와 일치)

---

## 2. 데이터 모델

모든 모델은 `Meta.db_table`로 테이블명을 명시한다. 타임스탬프는 `created_at`(auto_now_add) /
`updated_at`(auto_now) 컨벤션을 따른다.

### races 앱

| 모델 | 테이블 | 설명 |
|---|---|---|
| `Race` | `races` | 대회 본체. ~46개 필드 + 커스텀 QuerySet 매니저 |
| `Review` | `race_reviews` | 대회 후기 (별점·완주기록·난이도·추천태그, IP 해시) |
| `RacePendingChange` | `race_pending_changes` | 크롤러 변경 제안. `approve()`/`reject()` 메서드 |
| `DeviceToken` | `device_tokens` | 푸시 알림 토큰 (구독 종목·지역) |
| `RaceFavorite` | `race_favorites` | 즐겨찾기 (user+race 유니크) |

**`Race` 모델의 특징**
- **JSON 필드**로 유연한 구조 저장: `distances`, `registration_phases`, `giveaways`,
  `course_images`, `giveaway_images`, `course_image_uploads`, `giveaway_image_uploads`,
  `weather_forecast`, `locked_fields`
- **이미지 이중 구조**: `image_url`(외부 URL) + `image_path`(로컬 업로드) →
  `image_src`/`image_src_thumb` 프로퍼티가 WebP·썸네일 경로를 계산해 반환
- **상태 자동 계산**: `status` 컬럼이 비어 있으면 `computed_status` 프로퍼티가
  접수·대회 날짜로 `예정/접수중/접수마감/종료`를 산출
- **거리 파싱/분류** (정적 메서드):
  - `parse_distance_km()` — `"42.195km"`, `"1,800m"`, `"10"` 등 문자열에서 km 추출
  - `detect_distance_category()` / `get_next_distance_category()` — 종목별 분류 규칙 매칭
  - `distance_names()` — 구(문자열) / 신(딕셔너리) 두 가지 distances 포맷 모두 지원
- **slug 생성**: `generate_unique_slug()`가 한글 포함 제목을 slug화하고 충돌 시 `-2`, `-3` 부여
- **저장 훅(`save`)**: 제목에 트레일러닝 키워드가 있으면 종목 자동 보정,
  distances의 `distance_meter`를 이름에서 자동 계산

**크롤러 보호 로직** (자동 수집 ↔ 수작업 충돌 방지)
- `CRAWLER_TRACKED_FIELDS` — 크롤러가 갱신 대상으로 삼는 필드 목록
- `lock_fields_for_edit()` — 어드민이 추적 필드를 직접 수정하면 해당 필드를 `locked_fields`에 추가
- `is_field_locked()` — 크롤러가 잠긴 필드는 건드리지 않도록 검사

### posts 앱

| 모델 | 테이블 | 설명 |
|---|---|---|
| `Post` | `posts` | 게시글. 6개 카테고리, `races`와 M2M(`through='PostRace'`) |
| `PostRace` | `post_race` | 게시글↔대회 피벗 (post+race 유니크) |
| `PostComment` | `post_comments` | 댓글. `parent` 자기참조로 대댓글 |
| `PostLike` | `post_likes` | 좋아요 (post+ip_hash 유니크) |

- 로그인 사용자(`user` FK, `SET_NULL`)와 익명 작성 모두 지원
- 익명 글/댓글은 `password`(bcrypt 해시)로 수정·삭제 검증 → `check_password()`
- `display_nickname` 프로퍼티가 로그인 닉네임 → 입력 닉네임 → `'익명'` 순으로 표시

### accounts 앱

| 모델 | 테이블 | 설명 |
|---|---|---|
| `UserProfile` | `user_profiles` | `User`와 OneToOne. 닉네임·이메일 인증·선호 종목/지역·온보딩 상태 |
| `SocialAccount` | `social_accounts` | OAuth 연동 (provider+uid 유니크) |
| `PendingSocialLogin` | `pending_social_logins` | OAuth 진행 중 임시 상태 (이메일 인증 코드 포함) |
| `EmailVerification` | `email_verifications` | 6자리 이메일 인증 코드 |
| `RaceRecord` | `race_records` | 사용자의 과거 대회 기록 (온보딩 시 수집, 기본 비공개) |

> `User`는 Django 기본 모델을 사용하며, 어드민 접근용 staff 계정으로만 쓰인다.
> 일반 사용자 식별은 `UserProfile`이 담당한다.

### core 앱

| 모델 | 설명 |
|---|---|
| `AnalyticsEvent` | 비즈니스 이벤트 로그 (event_type, properties JSON, item, session, 인덱스 다수) |

---

## 3. API 설계

### 라우팅 구조
- `config/urls.py` → `/api/v1/`를 `core.urls`로 위임, `/dj-admin/`은 Django 어드민
- `core/urls.py`가 `races`·`posts`·`accounts`의 URL을 한곳에 묶음 (+ `events/` 분석 수집)

### 주요 엔드포인트

**대회 (`races/urls.py`)**
```
GET  /api/v1/home/                     홈 데이터 (인기/마감임박/커뮤니티)
GET  /api/v1/races/                     목록 (종목·지역·상태·거리·기간·검색)
GET  /api/v1/races/calendar/            캘린더
GET  /api/v1/races/sports/  · regions/  필터 옵션
GET  /api/v1/races/recommendations/     개인화 추천
GET  /api/v1/races/year/<year>/         연도별
GET  /api/v1/races/<slug>/              상세 (+관련 대회·후기·게시글)
POST /api/v1/races/<slug>/reviews/      후기 작성
*    /api/v1/races/<slug>/favorite/     즐겨찾기 토글 (인증 필요)
POST /api/v1/races/<slug>/images/       이미지 업로드 (크롤러 API 키)
GET  /api/v1/sitemap/                   사이트맵 데이터
*    /api/v1/devices/ ...               푸시 토큰 등록/수정/삭제
```

**커뮤니티 (`posts/urls.py`)** — 게시글 CRUD, 비밀번호 검증, 댓글 CRUD, 좋아요 토글, 인라인 이미지 업로드

**인증·내정보 (`accounts/urls.py`)** — OAuth login/callback, 닉네임·이메일 인증, `me/`, 선호도, 온보딩, 로그아웃, 즐겨찾기·내 기록

**어드민 전용 API (`races/admin_api.py`)** — `/api/v1/admin/races/...` Bearer 토큰 기반 (SvelteKit 어드민 화면용, Django 어드민과 별개)

### DRF 전역 설정 (`REST_FRAMEWORK`)
- **렌더러/파서**: `djangorestframework_camel_case` → API는 camelCase, 내부는 snake_case 자동 변환
- **인증**: 기본 `accounts.authentication.JWTAuthentication`
- **권한**: 기본 `AllowAny` (대부분 공개 API, 필요한 뷰에서만 인증 요구)
- **페이지네이션**: 전역 비활성 → 필요 시 `core/pagination.py`의 커스텀 페이지네이터 사용
- **예외 처리**: `core.exceptions.custom_exception_handler` — 400 검증 오류를 `{'errors': {...}}` 형태로 감싸 프론트가 일관되게 파싱

### 뷰 스타일
함수형 대신 **클래스 기반 APIView**를 도메인별로 둔다 (`HomeView`, `RaceListView`,
`RaceDetailView`, `PostListCreateView` 등). 복잡한 필터는 모델의 `RaceQuerySet` 메서드로 위임한다.

---

## 4. 대회 조회 로직 (RaceQuerySet)

필터링·상태 계산의 핵심은 `races/models.py`의 커스텀 QuerySet에 모여 있다.

| 메서드 | 역할 |
|---|---|
| `upcoming()` | 오늘 이후 대회 |
| `closing_soon(days=7)` | 접수 마감 임박 (대회 종료일 고려) |
| `by_month_range(from, to)` | 월 범위 필터 |
| `by_sport` / `by_region` | 종목·지역 (단일/리스트 모두 허용) |
| `by_status(statuses)` | 상태 필터 — **수동 status 값 + 날짜 기반 자동 계산을 Q 객체로 OR 결합** |
| `by_distance_category(sport, cats)` | 종목별 거리 분류 — JSON distances를 파이썬에서 파싱해 매칭 |
| `registration_open()` | 현재 접수중 (수동/자동 상태 모두 반영) |

`by_status`는 `status` 컬럼이 채워진 대회는 그 값을, 비어 있는 대회는 접수·대회 날짜로
실시간 계산한 상태를 사용한다. 덕분에 운영자가 상태를 강제 지정할 수도, 자동에 맡길 수도 있다.

---

## 5. 인증

별도의 세션 로그인 없이 **경량 JWT + OAuth** 구조를 쓴다.

- **`JWTAuthentication`** (`accounts/authentication.py`): `Authorization: Bearer <token>` 헤더
  또는 `auth_token` 쿠키에서 토큰을 읽어 `user_id`로 사용자를 조회 (`select_related('profile')`)
- **토큰 발급/검증**: `accounts/tokens.py` (PyJWT), 페이로드는 `user_id`만 담는 최소 구조
- **OAuth** (`accounts/providers.py`): 카카오·네이버·구글. authorize URL 생성 → 콜백에서
  코드 교환 → `provider`, `provider_uid`, `email`, 프로필 이미지 획득
- **신규 가입 흐름**: OAuth 인증 → 닉네임 설정 → 이메일 6자리 코드 인증 → 온보딩(선호 종목·지역)
- **익명 사용자**: 게시글/댓글은 로그인 없이 작성하고, 비밀번호(bcrypt)로 본인 확인.
  좋아요·후기는 **IP 해시**(SHA256 + SECRET_KEY)로 중복을 막는다.

---

## 6. 미들웨어 & 운영 장치 (core)

`config/settings.py`의 `MIDDLEWARE`에 커스텀 3종을 등록한다.

| 미들웨어 | 역할 |
|---|---|
| `RequestLoggingMiddleware` | 모든 요청을 JSON 구조화 로그로 기록 (method·path·status·duration_ms·user·ip) |
| `ErrorNotificationMiddleware` | 500 발생 시 Telegram 알림. 동일 에러(타입+경로)는 60초간 중복 억제 |
| `AdminTokenCookieMiddleware` | Django 어드민에 로그인한 staff에게 `admin_token` 쿠키 발급 → SvelteKit이 `isAdmin` 판별 (30일 슬라이딩 만료) |

**그 외 core 유틸**
- `core/utils.py`: `hash_ip()`(SHA256), `is_bot_request()`(봇 UA 정규식 차단),
  `get_client_ip()`(X-Forwarded-For), `check_rate_limit()`(캐시 기반 레이트리밋),
  `post_count_subqueries()`(JSON 컬럼 GROUP BY 문제를 피하는 Subquery 카운트)
- `core/analytics.py`: `track()` — **별도 스레드로 비동기 기록**해 응답 속도에 영향 없음, 봇 요청은 제외
- `core/notifications.py`: Telegram 에러 알림
- `core/sanitize.py`: nh3로 사용자 HTML 새니타이즈
- **로깅**: 프로덕션은 `pythonjsonlogger` JSON 포맷, 개발은 사람이 읽기 좋은 포맷
- **Sentry**: `settings.py` 상단에서 초기화 (trace/profile 10% 샘플링)
- **캐시**: 파일 기반(`.cache`) — Redis 없이도 워커 간 공유 가능 (홈/관련 대회 캐시에 사용)

---

## 7. 비동기 작업 (Celery)

- `config/celery.py`가 Celery 앱을 만들고 `autodiscover_tasks()`로 각 앱의 `tasks.py`를 수집
- 브로커/백엔드는 Redis (환경변수로 주입), 직렬화는 JSON

**`CELERY_BEAT_SCHEDULE` (스케줄 작업)**

| 작업 | 주기 | 내용 |
|---|---|---|
| `crawl_marathon_task` | 매시 정각 (`with_details=True`) | 대회 크롤링 + 결과 이메일 리포트 |
| `send_weekly_digest_task` | 매주 월 09:00 KST | 옵트인 사용자에게 주간 다이제스트 |
| `send_new_races_alert_task` | 매시 05분 (크롤 직후) | 신규 추가 대회 알림 |
| `fetch_weather_task` | 매일 06:30 KST | 다가오는 대회 날씨 예보 수집 |

`races/tasks.py`·`accounts/tasks.py`에 실제 태스크가 정의되어 있다.

---

## 8. 데이터 크롤링 파이프라인

`races/services/marathon_crawler.py`의 `MarathonCrawlerService`가 핵심이다.

1. **수집**: `roadrun.co.kr` 일정/상세 페이지를 `httpx`로 가져와 파싱
   (`crawl()` 기본 / `crawl_with_details()` 상세 — 이미지·접수 단계 포함)
2. **지역 정규화**: 도시명을 시·도로 매핑 (`region_map` + `extra_patterns`로 청주→충북 등)
3. **변경 감지**: 기존 대회와 필드를 비교해 차이를 `RacePendingChange`로 적재
   (`CRITICAL_FIELDS`는 중요 필드)
4. **승인 워크플로우**: 관리자가 어드민에서 변경을 검토 → `approve()`(대회에 반영) / `reject()`
5. **보호**: `locked_fields`에 잠긴 필드, 수동 검증된(`verified_at`) 데이터는 덮어쓰지 않음

→ 자동 수집의 효율과 수작업 데이터의 신뢰성을 함께 확보하는 **human-in-the-loop** 구조.

**이미지 처리** (`races/image_utils.py`): 업로드 파일을 WebP로 변환하고 600px 썸네일 생성,
모델 프로퍼티가 원본/WebP/썸네일 경로를 자동 계산.

---

## 9. 관리자 (django-unfold)

`races/admin.py`가 가장 큰 커스터마이징 대상이다.

- 대회 폼을 `fieldsets`로 구획, JSON 필드(distances·entry_fee·이미지 갤러리)에 커스텀 위젯
- **코스/기념품 이미지 갤러리**: 드래그 정렬, 외부 URL + 업로드 이미지 분리, 클립보드 붙여넣기
- 추적 필드를 어드민에서 수정하면 **자동으로 `locked_fields`에 추가**(크롤러 덮어쓰기 방지)
- 대회 검증/접수 마감 등 **일괄 액션**, pending change 개수 뱃지
- `RacePendingChangeAdmin`: 기본 필터를 '대기중'으로, old/new 값 비교 표시, 일괄 승인/반려
- `posts`·`accounts`도 각 앱의 `admin.py`에서 unfold ModelAdmin으로 구성

---

## 10. 관리 커맨드 (`manage.py`)

`races/management/commands/`에 운영용 커맨드가 모여 있다.

| 커맨드 | 용도 |
|---|---|
| `crawl_marathon` | 대회 크롤링 (Celery 태스크의 CLI 진입점) |
| `scrape_races` / `apply_images` / `auto_review_images` | 공식 사이트 이미지 스크래핑·검토·적용 |
| `generate_og_images` | 동적 OG 이미지 생성 (Gemini) |
| `generate_blog` / `generate_open_registration` | 콘텐츠 생성 |
| `convert_images_webp` | 이미지 일괄 WebP 변환 |
| `backfill_edition` | 데이터 백필 |
| `fetch_weather` | 날씨 예보 수집 |

---

## 11. 기술 스택 요약 (`requirements.txt`)

| 분류 | 패키지 |
|---|---|
| 코어 | Django 5.1, djangorestframework 3.15 |
| 어드민 | django-unfold |
| API 보조 | djangorestframework-camel-case, django-cors-headers |
| 비동기 | celery[redis] 5.4, django-celery-beat |
| 인증 | PyJWT |
| 데이터 | psycopg2-binary (PostgreSQL) |
| 이미지/보안 | Pillow, nh3 |
| 외부 호출 | httpx |
| 운영 | gunicorn, sentry-sdk, python-json-logger, python-dotenv |
