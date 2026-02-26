# Django REST API Specification (Finalized)

> Finalized from api-spec.md after cross-referencing all Laravel source files.
> Changes from draft are marked with `[CHANGED]`, additions with `[ADDED]`.

## 1. Overview

### Base URL
- Internal (SvelteKit SSR -> Django): `http://api:8000/api/v1/`
- External (client -> nginx -> Django): `https://{domain}/api/v1/`

### Authentication
- **Internal API**: No authentication (SvelteKit SSR server-side calls)
- **Public API**: No authentication (race list/detail, device tokens)
- **Crawler API**: Bearer Token (`Authorization: Bearer {CRAWLER_API_KEY}`)
- **Admin**: Django Admin session auth (unrelated to API)

### Common Rules
- Content-Type: `application/json` (except file uploads)
- File uploads: `multipart/form-data`
- Date format: `YYYY-MM-DD` (date), ISO 8601 (datetime)
- Field names: **camelCase** (existing Svelte component compatibility)
- Empty lists: `[]` (never null)
- Null fields: explicitly `null` (not omitted from response)
- IP hash: extract from `X-Forwarded-For` header -> `sha256(ip + SECRET_KEY)`
- Timezone: `Asia/Seoul` for all date-based calculations (status, upcoming, closing_soon)

### Custom Pagination Format
Maintains Laravel pagination structure for minimal frontend changes:
```json
{
  "data": [],
  "meta": {
    "currentPage": 1,
    "lastPage": 5,
    "perPage": 20,
    "total": 98,
    "from": 1,
    "to": 20
  },
  "links": {
    "first": "/api/v1/races/?page=1",
    "last": "/api/v1/races/?page=5",
    "prev": null,
    "next": "/api/v1/races/?page=2"
  }
}
```

**[ADDED] Empty page behavior**: When `total` is 0, `from` and `to` are both `null`, `data` is `[]`.

---

## 2. Common Schemas

### 2.1 Race Object

Source: `RaceResource.php` (35 fields including computed)

```jsonc
{
  // === Basic Info ===
  "id": 1,                              // integer
  "slug": "2026-서울마라톤",              // string, URL routing key
  "title": "2026 서울마라톤",             // string
  "sport": "running",                    // enum: running|swimming|cycling|triathlon|trail_running
  "sportLabel": "마라톤",                // string (computed) - Korean label for sport

  // === Schedule ===
  "raceDate": "2026-03-15",             // string|null (YYYY-MM-DD)
  "raceEndDate": "2026-03-15",          // string|null (YYYY-MM-DD) - multi-day races
  "startTime": "08:00",                 // string|null

  // === Location ===
  "location": "서울 여의도공원",          // string|null
  "address": "서울시 영등포구 여의도동",   // string|null
  "latitude": 37.5283,                  // number|null (decimal)
  "longitude": 126.9322,                // number|null (decimal)
  "region": "서울",                      // string|null

  // === Distances ===
  "distances": ["42.195", "21.0975", "10"], // string[]|null (JSON array)

  // === Registration ===
  "registrationStart": "2026-01-01",    // string|null (YYYY-MM-DD)
  "registrationEnd": "2026-03-01",      // string|null (YYYY-MM-DD)
  "entryFee": [                          // object[]|null (JSON array)
    {"distance": "풀코스", "fee": "50,000원"},
    {"distance": "하프", "fee": "40,000원"}
  ],

  // === Links ===
  "officialUrl": "https://...",          // string|null
  "source": "marathon.pe.kr",           // string|null - data source
  "sourceUrl": "https://...",           // string|null

  // === Status (computed) ===
  "status": "registration_open",        // enum: upcoming|registration_open|registration_closed|finished
  "statusLabel": "접수중",               // string (computed) - Korean label for status

  // === Details ===
  "description": "...",                  // string|null (may contain HTML)
  "organizer": "서울마라톤조직위원회",     // string|null
  "organizerContact": "02-1234-5678",   // string|null
  "organizerEmail": "info@example.com", // string|null

  // === Images (computed) ===
  "imageSrc": "https://...",             // string|null (computed) - image_url first, then image_path URL
  "giveaways": ["완주 메달", "기념 티셔츠"], // string[]|null
  "courseImageSrcs": ["https://..."],    // string[] (computed, never null) - course image URLs
  "giveawayImageSrcs": ["https://..."], // string[] (computed, never null) - giveaway image URLs

  // === Stats/Computed ===
  "viewCount": 1234,                    // integer
  "daysUntilRace": 18,                  // integer (computed) - negative if already finished
  "daysUntilRegistrationEnd": 4,        // integer|null (computed) - null if no registration_end
  "isRegistrationOpen": true,           // boolean (computed) - status === 'registration_open'

  // === Other ===
  "recapUrl": "https://...",            // string|null - post-race recap/video URL
  "url": "/races/2026-서울마라톤",        // string (computed) - frontend detail page URL

  // === Timestamps ===
  "createdAt": "2026-01-15T09:00:00.000Z", // string (ISO 8601)
  "updatedAt": "2026-02-20T14:30:00.000Z"  // string (ISO 8601)
}
```

**Status computation logic** (when DB value is null, date-based auto-calculation):
1. `COALESCE(race_end_date, race_date) < today` -> `"finished"`
2. `registration_start IS NOT NULL AND registration_end IS NOT NULL AND registration_start <= today AND registration_end >= today` -> `"registration_open"`
3. `registration_end IS NOT NULL AND registration_end < today` -> `"registration_closed"`
4. Otherwise -> `"upcoming"`

**[ADDED] Important**: `today` uses `Asia/Seoul` timezone.

**Sport label mapping**:
| sport | sportLabel |
|---|---|
| running | 마라톤 |
| swimming | 수영 |
| cycling | 자전거 |
| triathlon | 철인3종 |
| trail_running | 트레일러닝 |

**Status label mapping**:
| status | statusLabel |
|---|---|
| upcoming | 예정 |
| registration_open | 접수중 |
| registration_closed | 접수마감 |
| finished | 종료 |

**Image resolution logic**:
- `imageSrc`: `image_url` (external URL) takes priority; fallback to `asset('storage/' + image_path)` if `image_path` exists; otherwise `null`
- `courseImageSrcs`: merge `course_images` (resolve each: external URLs pass through, local paths get `asset('storage/' + path)` prefix) + `course_image_uploads` (always `asset('storage/' + path)`)
- `giveawayImageSrcs`: same pattern as courseImageSrcs but for giveaway fields

### 2.2 Post Object

Source: `PostResource.php` (12 fields + conditional 2)

```jsonc
{
  "id": 1,                              // integer
  "nickname": "익명",                    // string (computed) - '익명' when nickname is null/empty
  "title": "첫 마라톤 후기",             // string
  "content": "...",                      // string (max 10000 chars)
  "images": ["posts/1/abc.jpg"],         // string[]|null - storage relative paths
  "imageSrcs": ["https://.../posts/1/abc.jpg"], // string[] (computed, never null) - full URLs
  "viewCount": 56,                       // integer
  "commentCount": 3,                     // integer (computed) - total comments (including replies)
  "likeCount": 12,                       // integer (computed) - total likes
  "createdAt": "2026-02-10T09:00:00.000Z", // string (ISO 8601)
  "createdAtFormatted": "2026.02.10 09:00", // string (computed, format: Y.m.d H:i)
  "updatedAt": "2026-02-10T09:00:00.000Z", // string (ISO 8601)

  // === Conditional (detail page only) ===
  "taggedRaces": [                       // TaggedRace[] - included when races relation is loaded
    {
      "id": 1,
      "slug": "2026-서울마라톤",
      "title": "2026 서울마라톤",
      "sport": "running",
      "sportLabel": "마라톤"
    }
  ],
  "comments": [...]                      // PostComment[] - root comments only (parent_id is null), ordered by created_at DESC
}
```

**[ADDED] Notes**:
- `taggedRaces` is included in both list and detail endpoints (list loads `races` relation)
- `comments` is only included in detail endpoint (loads `rootComments.replies`)
- `images` field contains storage-relative paths; `imageSrcs` contains full absolute URLs

### 2.3 PostComment Object

Source: `PostCommentResource.php` (8 fields + conditional 1)

```jsonc
{
  "id": 1,                              // integer
  "postId": 1,                           // integer
  "parentId": null,                      // integer|null - parent comment ID if this is a reply
  "nickname": "익명",                    // string (computed) - '익명' when nickname is null/empty
  "content": "좋은 글이네요!",            // string (max 1000 chars)
  "isReply": false,                      // boolean (computed) - parentId !== null
  "createdAt": "2026-02-10T10:00:00.000Z", // string (ISO 8601)
  "createdAtFormatted": "2026.02.10 10:00", // string (computed, format: Y.m.d H:i)

  // === Conditional ===
  "replies": [                           // PostComment[] - loaded when replies relation is present
    {
      "id": 2,
      "postId": 1,
      "parentId": 1,
      "nickname": "마라토너",
      "content": "감사합니다!",
      "isReply": true,
      "createdAt": "2026-02-10T11:00:00.000Z",
      "createdAtFormatted": "2026.02.10 11:00",
      "replies": []                      // always empty for nested replies (1-level only)
    }
  ]
}
```

**[ADDED] Notes**: Replies are ordered by `created_at ASC` (oldest first). Root comments are ordered by `created_at DESC` (newest first).

### 2.4 Review Object

Source: `ReviewResource.php` (6 fields)

```jsonc
{
  "id": 1,                              // integer
  "nickname": "러너",                    // string (computed) - '익명' when nickname is null/empty
  "rating": 4,                           // integer (1-5)
  "comment": "코스가 좋았습니다",         // string (5-200 chars)
  "createdAt": "2026-02-15T09:00:00.000Z", // string (ISO 8601)
  "createdAtFormatted": "2026.02.15"     // string (computed, format: Y.m.d - NOTE: date only, no time)
}
```

---

## 3. Internal API - Home

### GET /api/v1/home/

Home page data. Source: `HomeController@index`

**Query Parameters**: None

**Response** `200 OK`:
```jsonc
{
  "closingSoon": Race[],        // Registration closing soon (within 7 days, excluding cancelled, max 6)
  "upcomingRaces": Race[],      // Upcoming races (excluding cancelled, max 12)
  "recentlyAdded": Race[],      // Recently added races (created_at DESC, max 8)
  "recentPosts": Post[],        // Recent posts (max 5, taggedRaces included)
  "sportCounts": {              // Upcoming race count per sport
    "running": 45,
    "swimming": 12,
    "cycling": 8,
    "triathlon": 5,
    "trail_running": 15
  },
  "totalUpcoming": 85           // Total races with registration_open status
}
```

**Source mapping**:
| Response field | Laravel source |
|---|---|
| closingSoon | `Race::closingSoon(7)->where('title', 'not like', '%(취소)%')->limit(6)->get()` |
| upcomingRaces | `Race::upcoming()->where('title', 'not like', '%(취소)%')->limit(12)->get()` |
| recentlyAdded | `Race::orderBy('created_at', 'desc')->limit(8)->get()` |
| recentPosts | `Post::with('races')->latest()->limit(5)->get()` |
| sportCounts | Per sport: `Race::bySport(x)->upcoming()->count()` |
| totalUpcoming | `Race::registrationOpen()->count()` |

**[ADDED] Cancelled race exclusion**: `closingSoon` and `upcomingRaces` exclude races with `(취소)` in the title. `recentlyAdded` does NOT exclude cancelled races.

**[ADDED] closingSoon scope details**:
- `registration_end` is not null
- `registration_end >= today`
- `registration_end <= today + 7 days`
- `COALESCE(race_end_date, race_date) >= today`
- `status IS NULL OR status != 'registration_closed'`
- Ordered by `registration_end ASC`

**[ADDED] upcoming scope details**:
- `race_date >= today`
- Ordered by `race_date ASC`

**[ADDED] sportCounts uses the `upcoming` scope** (race_date >= today), while `totalUpcoming` uses the `registrationOpen` scope (actively accepting registrations).

---

## 4. Internal API - Races

### 4.1 GET /api/v1/races/

Race list with filtering + pagination. Source: `RaceController@index`

**Query Parameters**:
| Parameter | Type | Default | Description |
|---|---|---|---|
| sport | string\|string[] | - | Sport filter (multiple allowed) |
| region | string\|string[] | - | Region filter (multiple allowed) |
| status | string\|string[] | - | Status filter (`upcoming`, `registration_open`, `registration_closed`, `finished`, `closing_soon`) |
| name | string | - | Race name search (LIKE '%name%') |
| distance_category | string\|string[] | - | Distance category filter (only effective when exactly 1 sport is selected) |
| month_from | string | current year-month | Start month (YYYY-MM format) |
| month_to | string | - | End month (YYYY-MM format) |
| page | integer | 1 | Page number |

**[ADDED] Mobile-specific parameters** (also handled on this endpoint):
| Parameter | Type | Default | Description |
|---|---|---|---|
| upcoming | boolean | false | If true, only upcoming races |
| closing_soon | boolean | false | If true, only closing-soon races |
| days | integer | 7 | Used with closing_soon, days until deadline |
| per_page | integer | 20 | Items per page |

**Response** `200 OK`:
```jsonc
{
  "data": Race[],               // Paginated race list
  "meta": { "currentPage": 1, "lastPage": 5, "perPage": 20, "total": 98, "from": 1, "to": 20 },
  "links": { "first": "...", "last": "...", "prev": null, "next": "..." },
  "filters": {
    "regions": ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"],
    "sports": [
      {"value": "running", "label": "마라톤"},
      {"value": "swimming", "label": "수영"},
      {"value": "cycling", "label": "자전거"},
      {"value": "triathlon", "label": "철인3종"},
      {"value": "trail_running", "label": "트레일러닝"}
    ],
    "distanceCategories": {
      "running": [
        {"value": "short", "label": "10km 이하", "type": "range", "min": 0, "max": 10},
        {"value": "half", "label": "하프", "type": "range", "min": 20, "max": 22},
        {"value": "full", "label": "풀코스", "type": "range", "min": 40, "max": 43},
        {"value": "ultra", "label": "울트라", "type": "range", "min": 50, "max": 999},
        {"value": "special", "label": "특별종목", "type": "non_numeric"}
      ],
      "trail_running": [
        {"value": "short", "label": "20km 이하", "type": "range", "min": 0, "max": 20},
        {"value": "middle", "label": "21~50km", "type": "range", "min": 21, "max": 50},
        {"value": "ultra", "label": "울트라", "type": "range", "min": 51, "max": 999}
      ],
      "cycling": [
        {"value": "mtb", "label": "MTB", "type": "keyword", "keyword": "MTB"},
        {"value": "road", "label": "로드", "type": "keyword", "keyword": "로드"},
        {"value": "granfondo", "label": "그란폰도", "type": "keyword", "keyword": "그란폰도"},
        {"value": "mediofondo", "label": "메디오폰도", "type": "keyword", "keyword": "메디오폰도"}
      ],
      "triathlon": [
        {"value": "half", "label": "70.3 (하프)", "type": "keyword", "keyword": "70.3"},
        {"value": "full", "label": "풀코스", "type": "keyword", "keyword": "풀코스"}
      ],
      "swimming": [
        {"value": "short", "label": "1.5km 이하", "type": "range_m", "min": 0, "max": 1500},
        {"value": "long", "label": "1.5km 초과", "type": "range_m", "min": 1501, "max": 99999}
      ]
    }
  },
  "applied": {
    "sport": ["running"],
    "region": [],
    "status": [],
    "name": null,
    "distanceCategory": [],
    "monthFrom": "2026-02",
    "monthTo": null
  }
}
```

**[ADDED] Filtering logic details**:
- `status` containing `closing_soon` is handled separately: applies `closingSoon(7)` scope. Other status values in the array are filtered independently.
- `distance_category` is ONLY applied when exactly 1 sport is selected (`len(sport) === 1`)
- `month_from` defaults to current year-month (`now('Asia/Seoul').strftime('%Y-%m')`)
- `month_from` filtering: `race_date >= first day of month_from`
- `month_to` filtering: `race_date <= last day of month_to`
- Default ordering: `race_date ASC`
- `filters` and `applied` are always included in response, even for mobile API calls

**[ADDED] Distance category filtering logic** (PostgreSQL version):
- `range` type: check if any value in `distances` JSON array, cast to float, falls between `min` and `max`
- `range_m` type: same as range but values may contain commas (remove before casting)
- `keyword` type: check if any value in `distances` JSON array contains the keyword string
- `non_numeric` type: check if any value in `distances` JSON array, cast to float, equals 0 and is not empty string

### 4.2 GET /api/v1/races/{slug}/

Race detail. Source: `RaceController@show`

**Path Parameters**:
| Parameter | Type | Description |
|---|---|---|
| slug | string | Race slug |

**Headers** (optional):
| Header | Description |
|---|---|
| X-Forwarded-For | Client IP (for checking review status) |

**Response** `200 OK`:
```jsonc
{
  "race": Race,                  // Full race detail
  "relatedRaces": Race[],       // Related races (max 4)
  "relatedPosts": Post[],       // Related posts (max 5, taggedRaces included)
  "reviews": Review[],          // Reviews (newest first)
  "reviewStats": {
    "count": 12,                 // Review count
    "average": 4.2               // Average rating (1 decimal place), 0 if no reviews
  },
  "hasReviewed": false           // Whether current IP has already reviewed
}
```

**Side Effect**: `view_count` +1 increment

**Related races selection logic** (max 4, excluding current race):
1. Same sport + same region + upcoming (priority)
2. Same sport + upcoming (fill remaining)
3. Same region + upcoming (fill remaining)
Each step excludes IDs already selected by previous steps.

**Response** `404 Not Found`:
```json
{"detail": "Not found."}
```

### 4.3 GET /api/v1/races/year/{year}/

Annual race list (grouped by month). Source: `RaceController@yearly`

**Path Parameters**:
| Parameter | Type | Description |
|---|---|---|
| year | integer | Year (e.g., 2026) |

**Response** `200 OK`:
```jsonc
{
  "races": {
    "1": Race[],                 // January races
    "2": Race[],                 // February races
    // ... keys only exist for months with races
  },
  "year": 2026,                  // echo-back
  "totalCount": 245              // Total race count for the year
}
```

**[ADDED] Notes**:
- Month keys are integers (1-12), not zero-padded strings
- Races within each month are ordered by `race_date ASC`
- Grouping uses `race_date` month (format: `n` = month without leading zero)

### 4.4 GET /api/v1/races/calendar/

Calendar data. Source: `CalendarController@index`

**Query Parameters**:
| Parameter | Type | Default | Description |
|---|---|---|---|
| year | integer | current year | Year |
| month | integer | current month | Month (1-12) |
| sport | string | - | Sport filter (single value only) |

**Response** `200 OK`:
```jsonc
{
  "year": 2026,
  "month": 3,
  "startOfMonth": "2026-03-01",
  "racesGrouped": {              // Races grouped by date
    "2026-03-01": Race[],
    "2026-03-08": Race[],
    "2026-03-15": Race[]
    // ... only dates with races have keys
  },
  "previousMonth": {
    "year": 2026,
    "month": 2
  },
  "nextMonth": {
    "year": 2026,
    "month": 4
  },
  "sport": null,                 // echo-back (null if not filtered)
  "sports": [
    {"value": "running", "label": "마라톤"},
    {"value": "swimming", "label": "수영"},
    {"value": "cycling", "label": "자전거"},
    {"value": "triathlon", "label": "철인3종"},
    {"value": "trail_running", "label": "트레일러닝"}
  ]
}
```

**[ADDED] Notes**:
- Date keys in `racesGrouped` are in `YYYY-MM-DD` format
- Races within each date are ordered by `race_date ASC`
- Query filters by `race_date BETWEEN start_of_month AND end_of_month`

### 4.5 GET /api/v1/races/sports/

Sports list. Source: `Api\RaceController@sports`

**Response** `200 OK`:
```json
[
  {"value": "running", "label": "마라톤"},
  {"value": "swimming", "label": "수영"},
  {"value": "cycling", "label": "자전거"},
  {"value": "triathlon", "label": "철인3종"},
  {"value": "trail_running", "label": "트레일러닝"}
]
```

**[CHANGED]**: The Laravel source `Api\RaceController@sports` only returns 4 sports (missing `trail_running`). The Django implementation MUST include all 5 sports to match the web controllers and ensure consistency.

### 4.6 GET /api/v1/races/regions/

Regions list. Source: `Api\RaceController@regions`

**Response** `200 OK`:
```json
["서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
```

---

## 5. Internal API - Reviews

### POST /api/v1/races/{slug}/reviews/

Create review. Source: `ReviewController@store`

**Path Parameters**:
| Parameter | Type | Description |
|---|---|---|
| slug | string | Race slug |

**Headers**:
| Header | Description |
|---|---|
| X-Forwarded-For | Client IP (required - duplicate review prevention and rate limiting) |

**Request Body** `application/json`:
```jsonc
{
  "nickname": "러너",            // string|null (max 50 chars, shows as '익명' when empty)
  "rating": 4,                   // integer (required, 1-5)
  "comment": "코스가 좋았습니다"  // string (required, 5-200 chars)
}
```

**Validation Rules**:
| Field | Rules | Error Messages |
|---|---|---|
| rating | required, integer, min:1, max:5 | "별점을 선택해주세요." / "별점은 1점 이상이어야 합니다." / "별점은 5점 이하이어야 합니다." |
| comment | required, string, min:5, max:200 | "한줄평을 입력해주세요." / "한줄평은 최소 5자 이상 입력해주세요." / "한줄평은 최대 200자까지 입력 가능합니다." |
| nickname | nullable, string, max:50 | - |

**Response** `201 Created`:
```json
{
  "success": true,
  "message": "리뷰가 등록되었습니다.",
  "review": Review
}
```

**Response** `400 Bad Request` (duplicate review):
```json
{
  "errors": {"review": ["이미 이 대회에 리뷰를 작성하셨습니다."]}
}
```

**Response** `422 Unprocessable Entity` (validation failure):
```json
{
  "errors": {
    "rating": ["별점을 선택해주세요."],
    "comment": ["한줄평은 최소 5자 이상 입력해주세요."]
  }
}
```

**Response** `429 Too Many Requests`:
```json
{
  "errors": {"review": ["리뷰 작성 제한에 도달했습니다. 잠시 후 다시 시도해주세요."]}
}
```

**Rate Limit**: 3 per hour per IP

**[ADDED] Processing order**: validation -> duplicate check -> rate limit check -> create

**Side Effect**: Stores `ip_hash` (SHA256 of client IP + SECRET_KEY) with the review

---

## 6. Internal API - Posts

### 6.1 GET /api/v1/posts/

Post list. Source: `PostController@index`

**Query Parameters**:
| Parameter | Type | Default | Description |
|---|---|---|---|
| search | string | - | Search title + content (LIKE '%search%') |
| page | integer | 1 | Page number |

**Response** `200 OK`:
```jsonc
{
  "data": Post[],               // taggedRaces included, comments NOT included
  "meta": { "currentPage": 1, "lastPage": 3, "perPage": 20, "total": 42, "from": 1, "to": 20 },
  "links": { "first": "...", "last": "...", "prev": null, "next": "..." },
  "search": null                 // echo-back
}
```

**[ADDED] Notes**:
- Posts are ordered by `created_at DESC` (latest first)
- Search matches both `title` and `content` fields with OR logic

### 6.2 GET /api/v1/posts/races/

Taggable races list for post creation. Source: `PostController@create`

**Response** `200 OK`:
```jsonc
{
  "races": [                     // Upcoming races (max 100)
    {
      "id": 1,
      "title": "2026 서울마라톤",
      "sport": "running",
      "sportLabel": "마라톤",
      "raceDate": "2026.03.15"   // format: Y.m.d (note: dots, not dashes)
    }
  ]
}
```

**[ADDED]**: The `raceDate` format here is `Y.m.d` (with dots), different from the Race object's `YYYY-MM-DD` format. This matches the Laravel source which uses `$race->race_date?->format('Y.m.d')`.

### 6.3 POST /api/v1/posts/

Create post. Source: `PostController@store`

**Headers**:
| Header | Description |
|---|---|
| X-Forwarded-For | Client IP (rate limiting) |

**Request Body** `multipart/form-data`:
| Field | Type | Required | Description |
|---|---|---|---|
| nickname | string | - | Nickname (max 50 chars) |
| title | string | Y | Title (max 100 chars) |
| content | string | Y | Content (max 10000 chars) |
| password | string | Y | Password (4-50 chars) |
| race_ids | integer[] | - | Race IDs to tag (max 5) |
| images | File[] | - | Image files (max 5, each max 5MB, jpeg/png/gif/webp) |

**Validation Rules**:
| Field | Rules | Error Messages |
|---|---|---|
| title | required, string, max:100 | "제목을 입력해주세요." / "제목은 최대 100자까지 입력 가능합니다." |
| content | required, string, max:10000 | "내용을 입력해주세요." / "내용은 최대 10000자까지 입력 가능합니다." |
| password | required, string, min:4, max:50 | "비밀번호를 입력해주세요." / "비밀번호는 최소 4자 이상이어야 합니다." |
| race_ids | nullable, array, max:5, each: exists:races,id | "대회 태그는 최대 5개까지 선택 가능합니다." |
| images | nullable, array, max:5, each: image, mimes:jpeg,png,gif,webp, max:5120KB | "이미지는 최대 5개까지 첨부 가능합니다." / "이미지 파일만 업로드 가능합니다." / "지원되는 이미지 형식: jpeg, png, gif, webp" / "이미지 크기는 최대 5MB까지 가능합니다." |

**Response** `201 Created`:
```json
{
  "success": true,
  "message": "글이 등록되었습니다.",
  "post": Post,
  "redirect": "/posts/{id}"
}
```

**Response** `429 Too Many Requests`:
```json
{
  "errors": {"post": ["글 작성 제한에 도달했습니다. 잠시 후 다시 시도해주세요."]}
}
```

**Rate Limit**: 10 per hour per IP
**Side Effect**:
- Images saved to `posts/{post_id}/` directory with unique filenames
- `password` stored as bcrypt hash
- `ip_hash` stored (SHA256 of IP + SECRET_KEY)
- `nickname` stored as null when empty string provided

### 6.4 GET /api/v1/posts/{id}/

Post detail. Source: `PostController@show`

**Path Parameters**:
| Parameter | Type | Description |
|---|---|---|
| id | integer | Post ID |

**Headers** (optional):
| Header | Description |
|---|---|
| X-Forwarded-For | Client IP (like status check) |

**Response** `200 OK`:
```jsonc
{
  "post": Post,                  // taggedRaces + comments (with replies) included
  "hasLiked": false              // Whether current IP has liked this post
}
```

**Side Effect**: `view_count` +1 increment

**[ADDED]**: Comments are loaded as root comments (parent_id IS NULL) ordered by `created_at DESC`, each with nested replies ordered by `created_at ASC`.

### 6.5 POST /api/v1/posts/{id}/verify-password/

Verify password before editing. Source: `PostController@edit`

**Request Body** `application/json`:
```json
{
  "password": "1234"
}
```

**Response** `200 OK` (password matches):
```jsonc
{
  "success": true,
  "post": Post,                  // taggedRaces included
  "races": [                     // Taggable races (upcoming + already tagged races not in upcoming)
    {
      "id": 1,
      "title": "2026 서울마라톤",
      "sport": "running",
      "sportLabel": "마라톤",
      "raceDate": "2026.03.15"
    }
  ],
  "editToken": "a1b2c3d4..."    // Edit token (valid for 5 minutes)
}
```

**Response** `403 Forbidden` (password mismatch):
```json
{
  "errors": {"password": ["비밀번호가 일치하지 않습니다."]}
}
```

**[ADDED] Edit token implementation notes**:
- In Laravel, the token is stored in the session. Since the Django API is stateless, the implementation should use one of:
  - Django cache backend (recommended): store `{post_id}:{token}` -> `{expires_at}` in cache with 5-minute TTL
  - Or signed token containing post_id and expiry timestamp
- The token is 32 hex characters (16 random bytes)
- Token must be validated on the PUT /api/v1/posts/{id}/ endpoint
- `races` list includes upcoming races (max 100) PLUS any already-tagged races that are not in the upcoming list (to allow keeping existing tags)

### 6.6 PUT /api/v1/posts/{id}/

Update post. Source: `PostController@update`

**Request Body** `multipart/form-data`:
| Field | Type | Required | Description |
|---|---|---|---|
| edit_token | string | Y | Token from verify-password endpoint |
| nickname | string | - | Nickname (max 50 chars) |
| title | string | Y | Title (max 100 chars) |
| content | string | Y | Content (max 10000 chars) |
| race_ids | integer[] | - | Race IDs to tag (max 5) |
| images | File[] | - | New image files (max 5 each) |
| existing_images | string[] | - | Existing image paths to keep |

**Validation Rules**: Same as 6.3 (excluding password) + edit_token required

**Response** `200 OK`:
```json
{
  "success": true,
  "message": "글이 수정되었습니다.",
  "post": Post,
  "redirect": "/posts/{id}"
}
```

**Response** `403 Forbidden` (invalid or expired token):
```json
{
  "errors": {"password": ["수정 권한이 없습니다."]}
}
```

**[ADDED] Response for expired token specifically**:
```json
{
  "errors": {"password": ["세션이 만료되었습니다. 비밀번호를 다시 입력해주세요."]}
}
```

**Side Effects**:
- Old images NOT in `existing_images` are deleted from storage
- New images are added to `posts/{post_id}/` directory
- Total images (existing + new) limited to 5 (excess truncated)
- Race tags are fully synced (old tags removed, new tags set)
- Edit token is consumed (deleted from cache) after successful update
- `nickname` stored as null when empty string provided

### 6.7 DELETE /api/v1/posts/{id}/

Delete post. Source: `PostController@destroy`

**Request Body** `application/json`:
```json
{
  "password": "1234"
}
```

**Response** `200 OK`:
```json
{
  "success": true,
  "message": "글이 삭제되었습니다.",
  "redirect": "/posts"
}
```

**Response** `403 Forbidden`:
```json
{
  "errors": {"password": ["비밀번호가 일치하지 않습니다."]}
}
```

**Side Effects**:
- All image files deleted from storage
- Image directory `posts/{post_id}/` deleted
- Post record deleted (cascades to comments, likes, race tags)

---

## 7. Internal API - Comments

### 7.1 POST /api/v1/posts/{id}/comments/

Create comment. Source: `PostCommentController@store`

**Path Parameters**:
| Parameter | Type | Description |
|---|---|---|
| id | integer | Post ID |

**Headers**:
| Header | Description |
|---|---|
| X-Forwarded-For | Client IP (rate limiting) |

**Request Body** `application/json`:
```jsonc
{
  "parent_id": null,             // integer|null (parent comment ID for replies)
  "nickname": "마라토너",         // string|null (max 50 chars)
  "content": "좋은 글이네요!",    // string (required, max 1000 chars)
  "password": "1234"             // string (required, 4-50 chars)
}
```

**Validation Rules**:
| Field | Rules | Error Messages |
|---|---|---|
| content | required, string, max:1000 | "댓글 내용을 입력해주세요." / "댓글은 최대 1000자까지 입력 가능합니다." |
| password | required, string, min:4, max:50 | "비밀번호를 입력해주세요." / "비밀번호는 최소 4자 이상이어야 합니다." |
| parent_id | nullable, integer, exists:post_comments,id | - |
| nickname | nullable, string, max:50 | - |

**Business Rules**:
- If `parent_id` is specified, parent comment must belong to the same post
- Reply-to-reply not allowed (1 level only) -> parent comment's `parent_id` must be null

**Response** `201 Created`:
```json
{
  "success": true,
  "message": "댓글이 등록되었습니다.",
  "comment": PostComment
}
```

**Response** `400 Bad Request`:
```json
{
  "errors": {"comment": ["잘못된 요청입니다."]}
}
```
Or:
```json
{
  "errors": {"comment": ["대댓글에는 답글을 달 수 없습니다."]}
}
```

**[ADDED] Response** `429 Too Many Requests`:
```json
{
  "errors": {"comment": ["댓글 작성 제한에 도달했습니다. 잠시 후 다시 시도해주세요."]}
}
```

**Rate Limit**: 10 per 10 minutes per IP

**Side Effect**: `password` stored as bcrypt hash, `ip_hash` stored

### 7.2 PUT /api/v1/posts/{id}/comments/{commentId}/

Update comment. Source: `PostCommentController@update`

**Request Body** `application/json`:
```json
{
  "content": "수정된 댓글입니다.",
  "password": "1234"
}
```

**Validation Rules**:
| Field | Rules | Error Messages |
|---|---|---|
| content | required, string, max:1000 | "댓글 내용을 입력해주세요." / "댓글은 최대 1000자까지 입력 가능합니다." |
| password | required, string (password verification) | - |

**Business Rules**: Comment must belong to the specified post (`comment.post_id === id`)

**Response** `200 OK`:
```json
{
  "success": true,
  "message": "댓글이 수정되었습니다.",
  "comment": PostComment
}
```

**[ADDED] Response** `400 Bad Request` (comment doesn't belong to post):
```json
{
  "errors": {"comment": ["잘못된 요청입니다."]}
}
```

**Response** `403 Forbidden`:
```json
{
  "errors": {"password": ["비밀번호가 일치하지 않습니다."]}
}
```

### 7.3 DELETE /api/v1/posts/{id}/comments/{commentId}/

Delete comment. Source: `PostCommentController@destroy`

**Request Body** `application/json`:
```json
{
  "password": "1234"
}
```

**Business Rules**: Comment must belong to the specified post

**Response** `200 OK`:
```json
{
  "success": true,
  "message": "댓글이 삭제되었습니다."
}
```

**[ADDED] Response** `400 Bad Request` (comment doesn't belong to post):
```json
{
  "errors": {"comment": ["잘못된 요청입니다."]}
}
```

**Response** `403 Forbidden`:
```json
{
  "errors": {"password": ["비밀번호가 일치하지 않습니다."]}
}
```

---

## 8. Internal API - Likes

### POST /api/v1/posts/{id}/like/

Toggle like. Source: `PostLikeController@toggle`

**Path Parameters**:
| Parameter | Type | Description |
|---|---|---|
| id | integer | Post ID |

**Headers**:
| Header | Description |
|---|---|
| X-Forwarded-For | Client IP (required - like tracking) |

**Request Body**: None (empty body)

**Response** `200 OK`:
```json
{
  "success": true,
  "liked": true,
  "likeCount": 13
}
```

**[ADDED] Notes**:
- `liked: true` = like was added, `liked: false` = like was removed
- `likeCount` is the fresh count after the toggle

**Response** `429 Too Many Requests`:
```json
{
  "success": false,
  "message": "추천 횟수 제한에 도달했습니다. 잠시 후 다시 시도해주세요."
}
```

**Rate Limit**: 20 per hour per IP (only counts when adding a like, not when removing)

---

## 9. Internal API - Sitemap

### GET /api/v1/sitemap/

Sitemap data. Source: `SitemapController@index`

**Response** `200 OK`:
```jsonc
{
  "races": [                     // All races (updated_at DESC)
    {
      "slug": "2026-서울마라톤",
      "updatedAt": "2026-02-20T14:30:00.000Z"
    }
  ],
  "posts": [                     // All posts (updated_at DESC)
    {
      "id": 1,
      "updatedAt": "2026-02-10T09:00:00.000Z"
    }
  ],
  "calendarMonths": [            // Current month +/- 12 months (25 entries)
    {"year": 2025, "month": 2},
    {"year": 2025, "month": 3},
    // ...
    {"year": 2027, "month": 2}
  ]
}
```

**[ADDED] Notes**:
- `calendarMonths` includes both endpoints (current - 12 months TO current + 12 months), totaling 25 entries
- This endpoint returns ALL races and ALL posts (no pagination), so it should be cached if data volume grows

---

## 10. Public API - Races (Mobile)

The public API shares the same endpoints as the internal API. No separate endpoints needed.

### 10.1 GET /api/v1/races/ (Public)

Same as 4.1. Internal and external share the same endpoint and response format.

The mobile-specific query parameters (`upcoming`, `closing_soon`, `days`, `per_page`) are handled on the same endpoint.

### 10.2 GET /api/v1/races/{slug}/ (Public)

Same as 4.2. Internal and external share the same endpoint and response format.

**[ADDED] Note**: The public API (mobile) endpoint returns the full Race object through the serializer, identical to the internal API. The original Laravel public API returned raw model data (without RaceResource), but for the Django migration we unify both to use the same serializer for consistency.

---

## 11. Public API - Device Tokens

Push notification device token management. Source: `Api\DeviceTokenController`

### 11.1 POST /api/v1/devices/

Register/update device token. Source: `DeviceTokenController@store`

**Request Body** `application/json`:
```jsonc
{
  "token": "fcm-token-string",          // string (required, max 255)
  "platform": "android",                // enum: android|ios (required)
  "subscribed_sports": ["running", "cycling"], // string[]|null
  "subscribed_regions": ["서울", "경기"]       // string[]|null
}
```

**Validation Rules**:
| Field | Rules |
|---|---|
| token | required, string, max:255 |
| platform | required, in:android,ios |
| subscribed_sports.* | in:running,swimming,cycling,triathlon,trail_running |
| subscribed_regions.* | string, max:50 |

**Behavior**: If `token` already exists, performs updateOrCreate (overwrites platform and subscriptions)

**Response** `201 Created`:
```json
{
  "message": "푸시 토큰이 등록되었습니다.",
  "device_token": {
    "id": 1,
    "token": "fcm-token-string",
    "platform": "android",
    "subscribed_sports": ["running", "cycling"],
    "subscribed_regions": ["서울", "경기"],
    "created_at": "...",
    "updated_at": "..."
  }
}
```

**[ADDED] Notes**: The `device_token` response uses **snake_case** field names (not camelCase), matching the original Laravel API response which returns the raw model. This is intentional for backwards compatibility with existing mobile clients.

### 11.2 PUT /api/v1/devices/

Update subscription settings. Source: `DeviceTokenController@update`

**[CHANGED]**: URL path has no `{token}` parameter. Token is passed in the request body.

**Request Body** `application/json`:
```json
{
  "token": "fcm-token-string",
  "subscribed_sports": ["running"],
  "subscribed_regions": ["서울"]
}
```

**Response** `200 OK`:
```json
{
  "message": "구독 설정이 업데이트되었습니다.",
  "device_token": { ... }
}
```

**Response** `404 Not Found`:
```json
{
  "message": "등록된 토큰을 찾을 수 없습니다."
}
```

### 11.3 DELETE /api/v1/devices/

Delete device token. Source: `DeviceTokenController@destroy`

**[CHANGED]**: URL path has no `{token}` parameter. Token is passed in the request body.

**Request Body** `application/json`:
```json
{
  "token": "fcm-token-string"
}
```

**Response** `200 OK`:
```json
{
  "message": "푸시 토큰이 삭제되었습니다."
}
```

**Response** `404 Not Found`:
```json
{
  "message": "등록된 토큰을 찾을 수 없습니다."
}
```

---

## 12. Public API - Image Upload (Crawler Only)

### POST /api/v1/races/{slug}/images/

Crawler uploads race images. Source: `Api\RaceImageController@upload`

**Authentication**: Bearer Token (required)
```
Authorization: Bearer {CRAWLER_API_KEY}
```

**Request Body** `multipart/form-data`:
| Field | Type | Required | Description |
|---|---|---|---|
| type | string | Y | Image type: `main`, `course`, `giveaway` |
| images | File[] | Y | Image files (1-10, each max 4MB, jpg/jpeg/png/gif/webp) |

**Validation Rules**:
| Field | Rules |
|---|---|
| type | required, in:main,course,giveaway |
| images | required, array, min:1, max:10 |
| images.* | required, image, mimes:jpg,jpeg,png,gif,webp, max:4096KB |

**Behavior**:
- Images stored in directories based on type:
  - `main` -> `races/` (filename: `{race_id}_{datetime}_{index}.{ext}`)
  - `course` -> `races/courses/`
  - `giveaway` -> `races/giveaways/`
- Creates `RacePendingChange` record (admin approval required)
- Does NOT directly modify the Race model
- `field_name` in pending change:
  - `main` -> `image_path`
  - `course` -> `course_image_uploads`
  - `giveaway` -> `giveaway_image_uploads`

**[ADDED] For course/giveaway types**: New paths are merged with existing values (appended to array)

**Response** `201 Created`:
```json
{
  "message": "Images uploaded and pending review.",
  "race_id": 1,
  "race_title": "2026 서울마라톤",
  "type": "course",
  "stored_paths": ["races/courses/1_20260225_120000_0.jpg"],
  "urls": ["https://.../storage/races/courses/1_20260225_120000_0.jpg"]
}
```

**Response** `401 Unauthorized`:
```json
{
  "message": "Invalid API key."
}
```

**[ADDED] Response** `500 Internal Server Error` (API key not configured):
```json
{
  "message": "API key not configured on server."
}
```

---

## 13. Appendix

### 13.1 Error Response Format

All error responses follow consistent formats:

**Validation errors** (422):
```json
{
  "errors": {
    "fieldName": ["Error message 1", "Error message 2"],
    "anotherField": ["Error message"]
  }
}
```

**Business logic errors** (400/403):
```json
{
  "errors": {
    "contextKey": ["Error message"]
  }
}
```
- `contextKey` examples: `review` (duplicate review), `password` (password mismatch), `comment` (invalid request), `post` (rate limit)

**Not Found** (404):
```json
{"detail": "Not found."}
```

**Rate Limit** (429):
- Like endpoint: `{"success": false, "message": "..."}`
- All others: `{"errors": {"contextKey": ["..."]}}`

**Server Error** (500):
```json
{"detail": "Internal server error."}
```

**[ADDED] Note on DRF default 404**: Django REST Framework's default 404 response uses `{"detail": "Not found."}`. Custom 404 responses (like device token's `{"message": "..."}`) override this for specific endpoints.

### 13.2 Rate Limiting

| Endpoint | Limit | Period | Identifier |
|---|---|---|---|
| POST /api/v1/posts/ | 10 | 1 hour | IP hash |
| POST /api/v1/races/{slug}/reviews/ | 3 | 1 hour | IP hash |
| POST /api/v1/posts/{id}/comments/ | 10 | 10 minutes | IP hash |
| POST /api/v1/posts/{id}/like/ | 20 | 1 hour | IP hash (only counted on like add, not remove) |

Django implementation: `django.core.cache` based (same pattern as Laravel's `Cache::put`)
- Cache key: `{action}_rate_limit:{ip_hash}`
- Counter approach (window auto-resets on expiry)
- **[ADDED]**: Use `cache.get_or_set()` with TTL for initial counter, `cache.incr()` for subsequent increments, or simply `cache.get()` + `cache.set()` with absolute TTL matching Laravel behavior.

### 13.3 Pagination

DRF custom Pagination class maintaining Laravel-compatible structure:

```python
# api/core/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class LaravelStylePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'per_page'  # [CHANGED] Allow mobile to override

    def get_paginated_response(self, data):
        return Response({
            'data': data,
            'meta': {
                'currentPage': self.page.number,
                'lastPage': self.page.paginator.num_pages,
                'perPage': self.get_page_size(self.request),
                'total': self.page.paginator.count,
                'from': self.page.start_index() if self.page.paginator.count > 0 else None,
                'to': self.page.end_index() if self.page.paginator.count > 0 else None,
            },
            'links': {
                'first': self.get_first_link(),
                'last': self.get_last_link(),
                'prev': self.get_previous_link(),
                'next': self.get_next_link(),
            }
        })

    def get_first_link(self):
        if not self.page.has_previous():
            return self.request.build_absolute_uri()
        url = self.request.build_absolute_uri()
        return self.replace_query_param(url, self.page_query_param, 1)

    def get_last_link(self):
        url = self.request.build_absolute_uri()
        return self.replace_query_param(url, self.page_query_param, self.page.paginator.num_pages)

    @staticmethod
    def replace_query_param(url, key, val):
        from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        query[key] = [str(val)]
        return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))
```

**[CHANGED]**: Added `page_size_query_param = 'per_page'` to allow mobile clients to customize page size. Added null handling for `from`/`to` when result is empty.

### 13.4 IP Hash Processing

```python
# api/core/utils.py
import hashlib
from django.conf import settings

def get_client_ip(request):
    """Extract client IP from X-Forwarded-For header"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')

def hash_ip(request):
    """Convert IP address to SHA256 hash"""
    ip = get_client_ip(request)
    return hashlib.sha256(f"{ip}{settings.SECRET_KEY}".encode()).hexdigest()
```

### 13.5 Endpoint Summary

| # | HTTP | URL | Purpose | Source |
|---|---|---|---|---|
| 1 | GET | /api/v1/home/ | Home page data | HomeController@index |
| 2 | GET | /api/v1/races/ | Race list (filtering) | RaceController@index + Api\RaceController@index |
| 3 | GET | /api/v1/races/calendar/ | Calendar data | CalendarController@index + Api\RaceController@calendar |
| 4 | GET | /api/v1/races/sports/ | Sports list | Api\RaceController@sports |
| 5 | GET | /api/v1/races/regions/ | Regions list | Api\RaceController@regions |
| 6 | GET | /api/v1/races/year/{year}/ | Annual race list | RaceController@yearly |
| 7 | GET | /api/v1/races/{slug}/ | Race detail | RaceController@show + Api\RaceController@show |
| 8 | POST | /api/v1/races/{slug}/reviews/ | Create review | ReviewController@store |
| 9 | POST | /api/v1/races/{slug}/images/ | Image upload (crawler) | Api\RaceImageController@upload |
| 10 | GET | /api/v1/posts/ | Post list | PostController@index |
| 11 | GET | /api/v1/posts/races/ | Taggable races list | PostController@create |
| 12 | POST | /api/v1/posts/ | Create post | PostController@store |
| 13 | GET | /api/v1/posts/{id}/ | Post detail | PostController@show |
| 14 | POST | /api/v1/posts/{id}/verify-password/ | Verify password | PostController@edit |
| 15 | PUT | /api/v1/posts/{id}/ | Update post | PostController@update |
| 16 | DELETE | /api/v1/posts/{id}/ | Delete post | PostController@destroy |
| 17 | POST | /api/v1/posts/{id}/comments/ | Create comment | PostCommentController@store |
| 18 | PUT | /api/v1/posts/{id}/comments/{commentId}/ | Update comment | PostCommentController@update |
| 19 | DELETE | /api/v1/posts/{id}/comments/{commentId}/ | Delete comment | PostCommentController@destroy |
| 20 | POST | /api/v1/posts/{id}/like/ | Toggle like | PostLikeController@toggle |
| 21 | GET | /api/v1/sitemap/ | Sitemap data | SitemapController@index |
| 22 | POST | /api/v1/devices/ | Register device token | Api\DeviceTokenController@store |
| 23 | PUT | /api/v1/devices/ | Update subscriptions | Api\DeviceTokenController@update |
| 24 | DELETE | /api/v1/devices/ | Delete device token | Api\DeviceTokenController@destroy |

Total: 24 endpoints (8 static pages excluded: about, privacy, tools x5, running-terms)

### 13.6 DRF Serializer Field Mapping

Recommended: Use `djangorestframework-camel-case` package for automatic snake_case to camelCase conversion.

| API Field (camelCase) | DB Column (snake_case) | Notes |
|---|---|---|
| sportLabel | - | SerializerMethodField (computed) |
| raceDate | race_date | DateField |
| raceEndDate | race_end_date | DateField |
| startTime | start_time | CharField |
| registrationStart | registration_start | DateField |
| registrationEnd | registration_end | DateField |
| entryFee | entry_fee | JSONField |
| officialUrl | official_url | URLField |
| sourceUrl | source_url | URLField |
| statusLabel | - | SerializerMethodField (computed) |
| organizerContact | organizer_contact | CharField |
| organizerEmail | organizer_email | EmailField |
| imageSrc | - | SerializerMethodField (computed) |
| courseImageSrcs | - | SerializerMethodField (computed) |
| giveawayImageSrcs | - | SerializerMethodField (computed) |
| viewCount | view_count | IntegerField |
| daysUntilRace | - | SerializerMethodField (computed) |
| daysUntilRegistrationEnd | - | SerializerMethodField (computed) |
| isRegistrationOpen | - | SerializerMethodField (computed) |
| recapUrl | recap_url | URLField |
| createdAt | created_at | DateTimeField |
| updatedAt | updated_at | DateTimeField |
| commentCount | - | SerializerMethodField (computed) |
| likeCount | - | SerializerMethodField (computed) |
| imageSrcs | - | SerializerMethodField (computed) |
| createdAtFormatted | - | SerializerMethodField (computed) |
| postId | post_id | IntegerField |
| parentId | parent_id | IntegerField |
| isReply | - | SerializerMethodField (computed) |

**[ADDED] Exception**: Device token endpoints (11.x) use **snake_case** in responses for backwards compatibility with existing mobile clients.

### 13.7 DISTANCE_CATEGORIES Constant

Define in Django model or separate constants file. Source: `Race::DISTANCE_CATEGORIES`

```python
# api/races/constants.py
DISTANCE_CATEGORIES = {
    "running": [
        {"value": "short", "label": "10km 이하", "type": "range", "min": 0, "max": 10},
        {"value": "half", "label": "하프", "type": "range", "min": 20, "max": 22},
        {"value": "full", "label": "풀코스", "type": "range", "min": 40, "max": 43},
        {"value": "ultra", "label": "울트라", "type": "range", "min": 50, "max": 999},
        {"value": "special", "label": "특별종목", "type": "non_numeric"},
    ],
    "trail_running": [
        {"value": "short", "label": "20km 이하", "type": "range", "min": 0, "max": 20},
        {"value": "middle", "label": "21~50km", "type": "range", "min": 21, "max": 50},
        {"value": "ultra", "label": "울트라", "type": "range", "min": 51, "max": 999},
    ],
    "cycling": [
        {"value": "mtb", "label": "MTB", "type": "keyword", "keyword": "MTB"},
        {"value": "road", "label": "로드", "type": "keyword", "keyword": "로드"},
        {"value": "granfondo", "label": "그란폰도", "type": "keyword", "keyword": "그란폰도"},
        {"value": "mediofondo", "label": "메디오폰도", "type": "keyword", "keyword": "메디오폰도"},
    ],
    "triathlon": [
        {"value": "half", "label": "70.3 (하프)", "type": "keyword", "keyword": "70.3"},
        {"value": "full", "label": "풀코스", "type": "keyword", "keyword": "풀코스"},
    ],
    "swimming": [
        {"value": "short", "label": "1.5km 이하", "type": "range_m", "min": 0, "max": 1500},
        {"value": "long", "label": "1.5km 초과", "type": "range_m", "min": 1501, "max": 99999},
    ],
}
```

**[ADDED] PostgreSQL distance filtering implementation**:

The Laravel source uses SQLite's `json_each()` function. For PostgreSQL, use `jsonb_array_elements_text()`:

```python
# Range type (e.g., running distances in km)
Race.objects.extra(
    where=["""
        EXISTS (
            SELECT 1 FROM jsonb_array_elements_text(distances) AS d
            WHERE d::float > 0 AND d::float BETWEEN %s AND %s
        )
    """],
    params=[min_val, max_val]
)

# Range_m type (may contain commas)
# REPLACE(d, ',', '') before casting

# Keyword type
Race.objects.extra(
    where=["""
        EXISTS (
            SELECT 1 FROM jsonb_array_elements_text(distances) AS d
            WHERE d ILIKE %s
        )
    """],
    params=[f'%{keyword}%']
)

# Non-numeric type
Race.objects.extra(
    where=["""
        EXISTS (
            SELECT 1 FROM jsonb_array_elements_text(distances) AS d
            WHERE d != '' AND (d::float = 0 OR d ~ '[^0-9.]')
        )
    """]
)
```

**[ADDED] Note**: Use `RawSQL` or `extra()` for these queries since Django ORM doesn't natively support JSON array element filtering. Alternatively, consider using `django.contrib.postgres.fields` ArrayField operations if the column were ArrayField, but since we're using `managed=False` and the column is JSON, raw SQL is the safest approach.

### 13.8 SEO Redirects

**[ADDED]** The Laravel app has a redirect from numeric IDs to slugs for race URLs:
```
GET /races/{numeric_id} -> 301 redirect to /races/{slug}
```
This should be handled in the SvelteKit frontend, not in the Django API.

### 13.9 URL Pattern for `url` Field in Race Object

**[ADDED]** The `url` field in the Race object is computed as `/races/{slug}`. This is a frontend URL path, not an API URL. The Django serializer should compute this as:
```python
def get_url(self, obj):
    return f"/races/{obj.slug}"
```
