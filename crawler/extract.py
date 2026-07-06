"""hot path — 레시피 기반 결정론 실행 (LLM 무관). 정적(requests/BS4) or 브라우저(Playwright)."""
import re
import hashlib
import logging
import datetime as dt
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from playwright.sync_api import sync_playwright, Page, ElementHandle

from .models import ExtractionRecipe, FieldSpec, Row, ImageCache
from .llm import vision_extract

logger = logging.getLogger("marathon_crawler")


def _specs_for(recipe: ExtractionRecipe, page_name: str) -> dict[str, FieldSpec]:
    return {f: s for f, s in recipe.fields.items() if s.page == page_name}


def _has_images(recipe: ExtractionRecipe) -> bool:
    return any(s.img for s in recipe.fields.values())


def execute_recipe(recipe: ExtractionRecipe, start_url: str,
                   cache: ImageCache | None = None) -> list[Row]:
    browser = recipe.needs_js or _has_images(recipe)
    logger.info("execute_recipe: %s path, start=%s", "browser" if browser else "static", start_url)
    if browser:
        return _extract_browser(recipe, start_url, cache if cache is not None else {})
    return _extract_static(recipe, start_url)


# ── 정적 경로 (requests + BS4) — 가장 싼 hot path ──
def _extract_static(recipe: ExtractionRecipe, start_url: str) -> list[Row]:
    rows: list[Row] = []
    list_specs, detail_specs = _specs_for(recipe, "list"), _specs_for(recipe, "detail")
    url: str | None = start_url
    pages = 0
    while url and pages < 20:                            # 페이지네이션 (상한)
        soup = BeautifulSoup(requests.get(url, timeout=10).text, "html.parser")
        cards = soup.select(recipe.list_selector)
        logger.info("  static page %d: %d cards (%s)", pages + 1, len(cards), url)
        for card in cards:
            row: Row = {f: _bs_text(card, s) for f, s in list_specs.items()}
            if detail_specs and recipe.detail_link:      # 상세 페이지로 2-hop
                a = card.select_one(recipe.detail_link)
                if a and a.get("href"):
                    durl = urljoin(recipe.base_url, str(a["href"]))
                    dsoup = BeautifulSoup(requests.get(durl, timeout=10).text, "html.parser")
                    row.update({f: _bs_text(dsoup, s) for f, s in detail_specs.items()})
            rows.append(_normalize(row, recipe))
        nxt = soup.select_one(recipe.pagination) if recipe.pagination else None
        url = urljoin(url, str(nxt["href"])) if nxt and nxt.get("href") else None
        pages += 1
    logger.info("  static: %d rows total", len(rows))
    return rows


def _bs_text(scope: Tag | BeautifulSoup, spec: FieldSpec) -> str | None:
    if spec.sel is None:
        return None
    el = scope.select_one(spec.sel)
    if el is None:
        return None
    return el.get(spec.attr) if spec.attr else el.get_text(strip=True)


# ── 브라우저 경로 (Playwright) — JS 렌더링 + 모달/팝업 이미지 ──
def _extract_browser(recipe: ExtractionRecipe, start_url: str, cache: ImageCache) -> list[Row]:
    list_specs, detail_specs = _specs_for(recipe, "list"), _specs_for(recipe, "detail")
    pending: list[tuple[Row, str | None]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        url: str | None = start_url
        pages = 0
        while url and pages < 20:                        # 1) 리스트 페이지들 순회
            page.goto(url, wait_until="networkidle")
            cards = page.query_selector_all(recipe.list_selector)
            logger.info("  browser page %d: %d cards (%s)", pages + 1, len(cards), url)
            for card in cards:
                row = _extract_on(card, page, list_specs, cache)
                durl: str | None = None
                if recipe.detail_link:
                    a = card.query_selector(recipe.detail_link)
                    if a:
                        durl = urljoin(recipe.base_url, a.get_attribute("href") or "")
                pending.append((row, durl))
            nxt = page.query_selector(recipe.pagination) if recipe.pagination else None
            href = nxt.get_attribute("href") if nxt else None  # href 없으면(버튼/비활성) 종료 — 같은 URL 재로드 방지
            url = urljoin(url, href) if href else None
            pages += 1

        if detail_specs:                                 # 2) 상세 페이지에서 나머지 필드
            n = sum(1 for _, d in pending if d)
            logger.info("  browser: 상세 페이지 %d건 방문", n)
            for row, durl in pending:
                if not durl:
                    continue
                page.goto(durl, wait_until="networkidle")
                row.update(_extract_on(page, page, detail_specs, cache))

        browser.close()
    logger.info("  browser: %d rows total", len(pending))
    return [_normalize(row, recipe) for row, _ in pending]


def _extract_on(scope: Page | ElementHandle, page: Page,
                specs: dict[str, FieldSpec], cache: ImageCache) -> Row:
    """scope: 카드 핸들(list) 또는 page(detail). page: 모달 클릭용 Playwright page."""
    row: Row = {}
    for field, spec in specs.items():
        if spec.img:                                     # 이미지 -> vision
            row[field] = read_image_field(scope, page, spec, cache, field)
        elif spec.sel is not None:
            el = scope.query_selector(spec.sel)
            if el is None:
                row[field] = None
            elif spec.attr:
                row[field] = el.get_attribute(spec.attr)
            else:
                row[field] = el.inner_text().strip()
        else:
            row[field] = None
    return row


# ── 이미지 후보 선별: 아이콘/로고 배제 + 대회 키워드 가산으로 '포스터'를 고른다 ──
RACE_IMG_KEYWORDS: tuple[str, ...] = (
    "poster", "포스터", "대회", "안내", "요강", "기수", "회차", "코스",
    "course", "notice", "guide", "map", "지도",
)
ICON_MIN_SIDE: int = 80          # 한 변이 이 값(px) 미만이면 아이콘/로고/썸네일로 보고 강하게 감점


def _pick_image_el(root: Page | ElementHandle, selector: str) -> ElementHandle | None:
    """selector에 매치되는 이미지들 중 '대회 정보 이미지'일 가능성이 가장 높은 하나를 고른다."""
    els = root.query_selector_all(selector)
    scored: list[tuple[float, ElementHandle]] = []
    for el in els:
        box = el.bounding_box()                          # 렌더된 실제 크기 (안 보이면 None)
        if box is None:
            continue
        area = box["width"] * box["height"]
        meta = " ".join(filter(None, [                   # alt/src/class에서 키워드 탐색
            el.get_attribute("alt"), el.get_attribute("src"), el.get_attribute("class"),
        ])).lower()
        kw = any(k in meta for k in RACE_IMG_KEYWORDS)
        big = min(box["width"], box["height"]) >= ICON_MIN_SIDE
        # 점수: 면적 × (키워드 3배) × (아이콘 크기면 0.05배로 사실상 배제)
        scored.append((area * (3.0 if kw else 1.0) * (1.0 if big else 0.05), el))
    if not scored:                                       # bounding_box가 전무하면(비표시 등) 최후의 수단
        return els[0] if els else None
    scored.sort(key=lambda t: t[0], reverse=True)
    logger.info("  image select: %d candidates → best score=%.0f", len(scored), scored[0][0])
    return scored[0][1]


# ── 이미지 필드: 모달 열기 -> 스크린샷 -> 해시캐시 -> vision(단발 호출) ──
def read_image_field(scope: Page | ElementHandle, page: Page, spec: FieldSpec,
                     cache: ImageCache, field: str) -> str | None:
    assert spec.img is not None
    if spec.open:                                        # 모달/팝업: page 레벨에서 열고 찾는다
        page.click(spec.open)
        page.wait_for_selector(spec.img, state="visible")
        el = _pick_image_el(page, spec.img)
    else:                                                # 인라인 이미지: 카드/페이지 scope 안에서 찾는다
        el = _pick_image_el(scope, spec.img)
    if el is None:
        return None
    img: bytes = el.screenshot()

    # 캐시 키에 field 포함: 같은 포스터에서 date/fee 등 여러 필드를 뽑을 때 값이 섞이지 않게
    h = f"{hashlib.sha256(img).hexdigest()}:{field}"
    if h in cache:
        logger.info("  image[%s]: 캐시 hit", field)
    else:
        logger.info("  image[%s]: 캐시 miss → vision 호출", field)
        cache[h] = vision_extract(img, field)
    value = cache[h]

    if spec.open:
        page.keyboard.press("Escape")
    return value


# ── 후처리: 상대 URL -> 절대, 날짜 정규화 ──
def _normalize(row: Row, recipe: ExtractionRecipe) -> Row:
    for f, v in list(row.items()):
        if not v:
            continue
        spec = recipe.fields.get(f)
        if spec and spec.attr == "href":
            row[f] = urljoin(recipe.base_url, v)
        if f in ("date", "reg_open", "reg_close"):
            d = _parse_date(v)
            if d:
                row[f] = d.date().isoformat()
    return row


def _parse_date(s: str) -> dt.datetime | None:
    # "2025-03-05", "2025.03.05", "2025/3/5", "2025년 3월 5일", "2025. 3. 5" 등 허용
    m = re.search(r"(\d{4})\D{1,3}(\d{1,2})\D{1,3}(\d{1,2})", s.strip())
    if not m:
        return None
    try:
        return dt.datetime(int(m[1]), int(m[2]), int(m[3]))
    except ValueError:
        return None
