"""보강(enrich) 잡 — 대회 공식 페이지에서 누락 필드만 채운다 (fill-only).

대상 필드 4종 (서버가 대회별 누락 목록을 계산해 준다 — admin API enrich-targets):
  - distances      : 대회 종목/거리 (비어 있을 때만)
  - fee            : 참가비 — distances 항목 안의 fee (전부 없을 때만)
  - giveaways      : 기념품 목록 (비어 있을 때만)
  - course_images  : 코스 지도 이미지 URL (비어 있을 때만)

흐름 (대회당, Playwright 브라우저 1개 재사용):
  1. 공식 페이지 로드 → 렌더링된 본문 텍스트
  2. 텍스트 LLM 추출 (structured_call) → 원문 실존 검증 통과분만 인정
  3. 텍스트로 못 채운 필드는 포스터/요강 이미지 vision 폴백 (_pick_image_el 재사용)
  4. 코스 지도: alt/src/class에 코스 키워드가 있는 이미지를 찾아 실제로 다운로드한 뒤
     admin 이미지 업로드 API(kind=course)로 올린다 — 외부 URL을 저장하지 않고
     로컬 경로(course_image_uploads)로 관리 (webp 변환 파이프라인 재사용)
  5. 텍스트 필드는 admin API PATCH (기존 locked_fields 동봉 → auto-lock 우회)

fill-only 원칙: 이미 값 있는 필드는 절대 덮어쓰지 않는다. LLM 출력은 신뢰하지
않는다 — 텍스트 추출은 페이지 원문에 실존하는 문자열만, 참가비는 파싱 가능한
정수 + 상식 범위만 인정한다. vision 결과는 형식 검증만 가능하므로 보수적으로 파싱한다.
"""
import hashlib
import json
import logging
import re
from urllib.parse import urljoin, urlparse

import requests
from playwright.sync_api import (
    sync_playwright, Page, Error as PlaywrightError, TimeoutError as PlaywrightTimeout,
)

from . import config
from .models import EnrichExtraction
from .llm import structured_call, vision_extract
from .extract import _pick_image_el

logger = logging.getLogger("marathon_crawler")

PAGE_TEXT_LIMIT = 6000
MIN_PAGE_TEXT = 200
MAX_GIVEAWAYS = 10
FEE_MIN, FEE_MAX = 1_000, 2_000_000        # 참가비 상식 범위 (원)
COURSE_IMG_KEYWORDS = ("코스", "course", "map", "지도")
ICON_MIN_SIDE = 80                          # 렌더 크기가 이보다 작으면 아이콘으로 보고 배제

_SYSTEM = (
    "너는 대회 공식 페이지에서 누락된 정보를 찾아 채우는 추출기다.\n"
    "규칙:\n"
    "- 요청받은 필드만 채운다. 페이지에서 확인할 수 없는 필드는 null.\n"
    "- distances의 name은 페이지 원문 표기 그대로(수정 없이) 인용한다 (예: '10km', '하프', '풀코스').\n"
    "  대회 참가 종목만 넣는다 — 사전행사·자원봉사·응원단 등은 제외.\n"
    "- fee는 해당 종목의 참가비를 원 단위 정수로. 페이지에 없으면 null.\n"
    "- giveaways는 참가자 전원에게 기념으로 지급되는 물품만 (예: 완주메달, 기념티셔츠, 기념품). "
    "페이지 원문 표기 그대로. 배번·기록칩, 생수·간식·보급품, 셔틀 등 편의 제공, "
    "추첨 경품(경품권·여행권 등)은 제외.\n"
    "- 추측하지 마라. 확신이 없으면 null."
)


def _api(path: str) -> str:
    return f"{config.API_BASE.rstrip('/')}{path}"


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {config.ADMIN_SECRET}"}


def fetch_targets(limit: int | None = None) -> list[dict]:
    params = {"limit": limit} if limit else {}
    resp = requests.get(_api("/api/v1/admin/races/enrich-targets/"),
                        headers=_headers(), params=params, timeout=30)
    resp.raise_for_status()
    targets = resp.json()["targets"]
    logger.info("보강 대상 %d건 조회", len(targets))
    return targets


# ── 검증 헬퍼 — LLM 출력 불신 원칙 ──
_WS = re.compile(r"\s+")


def _in_page(value: str, page_text: str) -> bool:
    """추출 문자열이 페이지 원문에 실존하는지 — 환각 기각 안전망."""
    v = _WS.sub(" ", value).strip()
    return len(v) >= 2 and v in _WS.sub(" ", page_text)


def _parse_fee(value) -> int | None:
    """'30,000', '30000원', '3만원', 30000 → 원 단위 정수. 실패 시 None."""
    if isinstance(value, (int, float)):
        return int(value) if value > 0 else None
    if not isinstance(value, str) or not value.strip():
        return None
    s = value.strip().replace(",", "")
    man = re.search(r"(\d+(?:\.\d+)?)\s*만", s)
    if man:
        total = float(man.group(1)) * 10000
        cheon = re.search(r"만\s*(\d+)\s*천", s)
        if cheon:
            total += float(cheon.group(1)) * 1000
        return int(total) if total > 0 else None
    num = re.search(r"(\d+)", s)
    return int(num.group(1)) if num else None


def _fee_ok(fee: int | None) -> bool:
    return fee is not None and FEE_MIN <= fee <= FEE_MAX


_DIST_KEYWORDS = ("하프", "풀", "울트라", "릴레이", "올림픽", "스프린트", "듀애슬론", "아쿠아슬론")


def _looks_like_distance(name: str) -> bool:
    """'10km', '5K', '1,800m', '하프', '올림픽코스' 같은 종목 표기인지 형식 검증."""
    if re.search(r"\d+(?:[.,]\d+)?\s*(?:km|k|m)\b", name, re.IGNORECASE):
        return True
    return any(k in name for k in _DIST_KEYWORDS)


def _validate_distances(items: list | None, page_text: str | None) -> list[dict]:
    """이름 형식 + (텍스트 추출이면) 원문 실존 + 참가비 범위 검증 통과분만.

    items: DistanceFee(pydantic) 또는 {'name', 'fee'} dict 의 리스트.
    page_text=None 이면 원문 실존 검증 생략 (vision 결과 — 이미지 텍스트는 본문에 없다).
    """
    if not items:
        return []
    out, seen = [], set()
    for it in items[:20]:
        if isinstance(it, dict):
            name, fee = str(it.get("name") or ""), it.get("fee")
        else:
            name, fee = it.name, it.fee
        name = name.strip()
        if not (2 <= len(name) <= 30) or name in seen:
            continue
        if not _looks_like_distance(name):
            continue
        if page_text is not None and not _in_page(name, page_text):
            continue
        seen.add(name)
        entry: dict = {"name": name}
        fee = _parse_fee(fee)
        if _fee_ok(fee):
            entry["fee"] = fee
        out.append(entry)
    return out


def _validate_giveaways(items: list[str] | None, page_text: str | None) -> list[str]:
    if not items:
        return []
    out, seen = [], set()
    for it in items[:MAX_GIVEAWAYS]:
        v = str(it).strip()
        if not (2 <= len(v) <= 30) or v in seen:
            continue
        if page_text is not None and not _in_page(v, page_text):
            continue
        seen.add(v)
        out.append(v)
    return out


# ── 페이지 읽기 (Playwright) ──
def _page_text(page: Page) -> str:
    try:
        return _WS.sub(" ", page.inner_text("body")).strip()[:PAGE_TEXT_LIMIT]
    except Exception:
        return ""


_COLLECT_IMGS_JS = """els => els.map(e => {
    const r = e.getBoundingClientRect();
    return {
        meta: [e.getAttribute('alt'), e.getAttribute('src'), e.getAttribute('class')]
            .filter(Boolean).join(' ').toLowerCase(),
        src: e.getAttribute('src') || e.getAttribute('data-src') || '',
        w: r.width, h: r.height,
    };
})"""


def _course_image_urls(page: Page) -> list[str]:
    """alt/src/class에 코스 키워드가 있는 이미지의 절대 URL (아이콘 크기 배제).

    이미지마다 왕복하면(query_selector_all + get_attribute + bounding_box) meta
    refresh/JS 리다이렉트가 걸린 페이지에서 순회 도중 페이지가 넘어가
    'Execution context was destroyed' 로 터진다. _candidate_links 와 같이 JS
    한 번으로 모아서 그 창을 없앤다 (왕복이 3N→1 로 줄어 속도도 붙는다).
    """
    try:
        found = page.eval_on_selector_all("img", _COLLECT_IMGS_JS)
    except Exception as exc:
        logger.info("  코스 이미지 스캔 실패 — 건너뜀 (%s)", exc)
        return []
    urls: list[str] = []
    for img in found:
        if not any(k in img["meta"] for k in COURSE_IMG_KEYWORDS):
            continue
        # 렌더 크기 0 은 비표시(display:none 등) — 기존 bounding_box() None 과 같이 통과시킨다
        if img["w"] and img["h"] and min(img["w"], img["h"]) < ICON_MIN_SIDE:
            continue
        src = img["src"]
        if not src or src.startswith("data:"):
            continue
        absolute = urljoin(page.url, src)
        if absolute.startswith(("http://", "https://")) and absolute not in urls:
            urls.append(absolute)
    return urls[:5]


# ── 코스 지도: 다운로드 → admin 업로드 API (외부 URL 저장 금지, 로컬 경로 관리) ──
IMG_MIN_BYTES = 5_000            # 이보다 작으면 아이콘/트래킹 픽셀로 보고 버림
IMG_MAX_BYTES = 15_000_000       # nginx/adapter body limit(20MB) 이내
_EXT_BY_MIME = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp"}


def _download_image(url: str, referer: str) -> tuple[str, bytes, str] | None:
    """이미지 다운로드 → (파일명, 바이트, MIME). 이미지가 아니거나 크기 부적합이면 None."""
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (compatible; EnduroHubBot/1.0)",
            "Referer": referer,                       # 핫링크 차단 사이트 대응
        })
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.info("  이미지 다운로드 실패: %s (%s)", url, exc)
        return None
    mime = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    ext = _EXT_BY_MIME.get(mime)
    if not ext or not (IMG_MIN_BYTES <= len(resp.content) <= IMG_MAX_BYTES):
        return None
    return f"course{ext}", resp.content, mime


def _upload_course_images(slug: str, downloads: list[tuple[str, bytes, str]]) -> None:
    files = [("images", (f"course_{i}{name[name.rfind('.'):]}", data, mime))
             for i, (name, data, mime) in enumerate(downloads)]
    resp = requests.post(_api(f"/api/v1/admin/races/{slug}/images/"),
                         headers=_headers(), data={"kind": "course"},
                         files=files, timeout=120)
    resp.raise_for_status()


# ── vision 폴백 — 포스터/요강 이미지에서 읽기 ──
_VISION_FIELDS = {
    "distances": "참가 종목(거리) 목록 — 쉼표로 구분 (예: 5km, 10km, 하프)",
    "fee": "참가비 — '종목 금액' 형태로 쉼표 구분 (예: 10km 30000원, 하프 40000원)",
    "giveaways": "참가자 전원에게 지급되는 기념품 목록 — 쉼표로 구분 (예: 완주메달, 기념티셔츠). "
                 "배번·생수·간식·추첨 경품은 제외",
}


def _vision_fallback(page: Page, field: str, cache: dict) -> str | None:
    """페이지에서 가장 '대회 안내/포스터'다운 이미지를 골라 vision으로 필드를 읽는다."""
    try:
        el = _pick_image_el(page, "img")          # 이미지별 DOM 왕복 — 네비게이션 중이면 터진다
        if el is None:
            return None
        img = el.screenshot()
    except Exception:
        return None
    h = f"{hashlib.sha256(img).hexdigest()}:{field}"
    if h not in cache:
        cache[h] = vision_extract(img, _VISION_FIELDS[field])
    return cache[h]


def _parse_vision_distances(raw: str) -> list[dict]:
    items = [{"name": p.strip()} for p in re.split(r"[,/·]", raw) if p.strip()]
    return _validate_distances(items, None)


def _parse_vision_fees(raw: str, existing: list[dict]) -> bool:
    """'10km 30000원, 하프 40000원' → 기존 distances 항목에 fee 병합. 채웠으면 True."""
    fee_by_name: dict[str, int] = {}
    for part in re.split(r"[,/·]", raw):
        m = re.match(r"(.+?)\s*([\d,]+)\s*원?\s*$", part.strip())
        if not m:
            continue
        fee = _parse_fee(m.group(2))
        if _fee_ok(fee):
            fee_by_name[m.group(1).strip()] = fee
    if not fee_by_name:
        return False
    changed = False
    for d in existing:
        if d.get("fee") is not None:
            continue
        for name, fee in fee_by_name.items():
            if name and (name in d["name"] or d["name"] in name):
                d["fee"] = fee
                changed = True
                break
    return changed


# ── 하위 페이지 탐색 — 요강/코스 안내는 대부분 랜딩이 아닌 하위 페이지에 있다 ──
MAX_SUBPAGES = 4
LINK_KEYWORDS_ANY = ("요강", "대회안내", "대회정보", "모집", "개요", "참가안내")   # 필드 무관 요강류
LINK_KEYWORDS_BY_FIELD = {
    "distances": ("종목", "참가", "코스"),
    "fee": ("참가비", "접수", "신청", "엔트리", "요금"),
    "giveaways": ("기념품", "사은품", "시상"),
    "course_images": ("코스", "course", "지도", "맵", "map"),
}


def _same_site(href: str, base_url: str) -> bool:
    """등록 도메인이 같을 때만 따라간다 (SNS/포털/외부 접수대행으로 새는 것 방지)."""
    a, b = urlparse(href).netloc.lower(), urlparse(base_url).netloc.lower()
    if not a or not b:
        return False
    return ".".join(a.split(".")[-2:]) == ".".join(b.split(".")[-2:])


def _candidate_links(page: Page, remaining: set[str], base_url: str) -> list[str]:
    """링크 텍스트/href를 키워드 스코어링해 방문할 하위 페이지 URL을 고른다."""
    try:
        links = page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => ({text: (e.innerText || '').trim().slice(0, 60), href: e.href}))",
        )
    except Exception:
        return []
    field_keywords = {k for f in remaining for k in LINK_KEYWORDS_BY_FIELD.get(f, ())}
    scored: dict[str, int] = {}
    for link in links:
        href = link.get("href") or ""
        if (not href.startswith(("http://", "https://"))
                or href.rstrip("/") == page.url.rstrip("/")
                or not _same_site(href, base_url)):
            continue
        meta = f"{link.get('text', '')} {href}".lower()
        score = (3 * sum(1 for k in LINK_KEYWORDS_ANY if k in meta)
                 + 2 * sum(1 for k in field_keywords if k in meta))
        if score > 0:
            scored[href] = max(scored.get(href, 0), score)
    ranked = sorted(scored.items(), key=lambda t: t[1], reverse=True)
    return [href for href, _ in ranked[:MAX_SUBPAGES]]


def _goto(page: Page, url: str, slug: str) -> None:
    """robust 페이지 로드 — networkidle 은 분석 스크립트/롱폴링 사이트에서 무한 대기하므로
    domcontentloaded 후 짧게 정착 대기, 타임아웃돼도 로드된 만큼으로 진행.

    meta refresh/JS 리다이렉트가 걸린 사이트는 goto 자체가 'interrupted by
    another navigation' 으로 터진다 — 이것도 로드된 만큼으로 진행한다
    (정말 아무것도 못 읽으면 자연히 unfilled 로 집계된다).
    """
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20_000)
        page.wait_for_load_state("load", timeout=10_000)
    except PlaywrightTimeout:
        logger.info("  [%s] 페이지 로드 타임아웃 — 부분 로드로 진행 (%s)", slug, url)
    except PlaywrightError as exc:
        logger.info("  [%s] 페이지 로드 중단 — 부분 로드로 진행 (%s: %s)", slug, url, exc)
    try:
        page.wait_for_timeout(1_500)                      # lazy-load 이미지 정착 대기
    except PlaywrightError:
        pass


def _harvest(page: Page, race: dict, remaining: set[str], state: dict, cache: dict) -> None:
    """현재 페이지에서 아직 못 채운 필드만 추출해 state 에 누적한다.

    state: {'payload': dict, 'downloads': list, 'existing': list}  (existing = fee 병합용 distances 사본)
    """
    text = _page_text(page)
    extraction: EnrichExtraction | None = None
    if text and len(text) >= MIN_PAGE_TEXT and ({"distances", "fee", "giveaways"} & remaining):
        user = (
            f"대회명: {race['title']}\n종목(스포츠): {race['sportLabel']}\n"
            f"대회일: {race['raceDate']}\n채워야 할 누락 필드: {', '.join(sorted(remaining))}\n\n"
            f"--- 페이지 원문 ---\n{text}"
        )
        try:
            extraction = structured_call(_SYSTEM, user, EnrichExtraction)
        except Exception as exc:
            logger.warning("  [%s] 텍스트 추출 실패: %s", race["slug"], exc)

    # distances (종목 자체가 없음)
    if "distances" in remaining:
        distances = _validate_distances(extraction.distances if extraction else None, text)
        if not distances:                                   # vision 폴백
            raw = _vision_fallback(page, "distances", cache)
            if raw:
                distances = _parse_vision_distances(raw)
        if distances:
            state["payload"]["distances"] = distances
            remaining.discard("distances")

    # fee (종목은 있는데 참가비가 전부 없음) — 기존 배열에 병합해서 통째로 보낸다
    if "fee" in remaining:
        existing = state["existing"]
        extracted = _validate_distances(extraction.distances if extraction else None, text)
        fee_by_name = {e["name"]: e["fee"] for e in extracted if e.get("fee")}
        changed = False
        for d in existing:
            if d.get("fee") is not None:
                continue
            for name, fee in fee_by_name.items():
                if name in d.get("name", "") or d.get("name", "") in name:
                    d["fee"] = fee
                    changed = True
                    break
        if not changed:                                     # vision 폴백
            raw = _vision_fallback(page, "fee", cache)
            if raw:
                changed = _parse_vision_fees(raw, existing)
        if changed:
            state["payload"]["distances"] = existing
            remaining.discard("fee")

    # giveaways
    if "giveaways" in remaining:
        giveaways = _validate_giveaways(extraction.giveaways if extraction else None, text)
        if not giveaways:                                   # vision 폴백
            raw = _vision_fallback(page, "giveaways", cache)
            if raw:
                giveaways = _validate_giveaways([p.strip() for p in re.split(r"[,/·]", raw)], None)
        if giveaways:
            state["payload"]["giveaways"] = giveaways
            remaining.discard("giveaways")

    # course_images — 키워드 매칭 이미지를 실제 다운로드 (업로드는 호출자가)
    if "course_images" in remaining:
        for u in _course_image_urls(page):
            dl = _download_image(u, page.url)
            if dl:
                state["downloads"].append(dl)
        if state["downloads"]:
            remaining.discard("course_images")


# ── 대회 1건 처리 ──
def enrich_race(page: Page, race: dict, cache: dict) -> tuple[dict, list]:
    """누락 필드를 추출해 (PATCH payload, 코스지도 다운로드 목록)을 반환한다.

    랜딩 페이지에서 먼저 추출하고, 못 채운 필드가 남으면 요강/코스 안내류
    하위 페이지(키워드 스코어 상위, 같은 도메인, 최대 MAX_SUBPAGES개)를
    순회하며 남은 필드만 재추출한다. 다 채워지면 조기 종료.

    어느 페이지에서 터지든 그때까지 모은 결과는 그대로 반환한다 — 한 페이지
    실패로 이미 뽑아둔 다른 필드까지 버리지 않는다.
    """
    url = race.get("officialUrl") or race.get("sourceUrl")
    remaining = set(race["missing"])
    state: dict = {
        "payload": {},
        "downloads": [],
        "existing": [dict(d) for d in (race.get("distances") or []) if isinstance(d, dict)],
    }

    _goto(page, url, race["slug"])
    try:
        _harvest(page, race, remaining, state, cache)
    except Exception as exc:
        logger.warning("  [%s] 랜딩 페이지 추출 실패 — 하위 페이지로 계속 (%s)", race["slug"], exc)

    if remaining:
        # 리다이렉트 후 실제 도메인(page.url) 기준으로 같은 사이트 여부를 판정한다
        for sub_url in _candidate_links(page, remaining, page.url):
            if not remaining:
                break
            logger.info("  [%s] 하위 페이지 탐색: %s", race["slug"], sub_url)
            try:
                _goto(page, sub_url, race["slug"])
                _harvest(page, race, remaining, state, cache)
            except Exception as exc:
                logger.info("  [%s] 하위 페이지 실패 (%s): %s", race["slug"], sub_url, exc)

    return state["payload"], state["downloads"]


def _patch(race: dict, payload: dict) -> None:
    # 기존 locked_fields 를 동봉해 admin API 의 auto-lock 을 우회한다
    # (자동 갱신이 스스로 필드를 잠그면 이후 크롤러 갱신이 막힌다).
    payload = {**payload, "lockedFields": race.get("lockedFields") or []}
    resp = requests.patch(_api(f"/api/v1/admin/races/{race['slug']}/"),
                          json=payload, headers=_headers(), timeout=30)
    resp.raise_for_status()


def run(limit: int | None = None, dry_run: bool = False) -> dict:
    """잡 1회 실행. 요약 카운트를 반환한다."""
    if not config.ADMIN_SECRET:
        raise RuntimeError("ADMIN_SECRET 미설정 — 환경변수로 지정 필요")

    summary = {"total": 0, "filled": 0, "unfilled": 0, "errors": 0}
    targets = fetch_targets(limit)
    cache: dict = {}                     # 이미지 해시 -> vision 결과 (이번 실행 동안)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for race in targets:
            summary["total"] += 1
            # 대회마다 새 컨텍스트를 쓴다. page 하나를 재사용하면 앞 대회의 지연
            # 리다이렉트(meta refresh 등)가 뒤늦게 발동해 다음 대회의 goto 를
            # "interrupted by another navigation" 으로 가로챈다 — 한 사이트가
            # 다음 대회를 연쇄로 망가뜨리던 실패의 주원인이었다.
            context = browser.new_context()
            page = context.new_page()
            try:
                payload, course_downloads = enrich_race(page, race, cache)
                if not payload and not course_downloads:
                    summary["unfilled"] += 1
                    continue
                filled = [k for k in payload if k != "lockedFields"]
                if course_downloads:
                    filled.append(f"course_images({len(course_downloads)})")
                if dry_run:
                    logger.info("  [%s] [dry-run] 채울 필드: %s → %s", race["slug"], filled,
                                json.dumps(payload, ensure_ascii=False)[:200])
                else:
                    if payload:
                        _patch(race, payload)
                    if course_downloads:
                        _upload_course_images(race["slug"], course_downloads)
                    logger.info("  [%s] 보강 완료: %s", race["slug"], filled)
                summary["filled"] += 1
            except Exception:
                logger.exception("  [%s] 보강 실패", race.get("slug"))
                summary["errors"] += 1
            finally:
                try:
                    context.close()
                except Exception:
                    pass
        browser.close()

    logger.info("=== enrich 완료: %s ===", summary)
    return summary
