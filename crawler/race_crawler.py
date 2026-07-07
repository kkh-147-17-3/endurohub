"""오케스트레이션 — 분기(cold/hot) + 검증 + 복구 + 사람 게이트.

세부 로직은 책임별 모듈로 분리되어 있다:
  config / models / llm / tools / extract / validate / store / discovery
이 파일은 그것들을 엮는 슬림 진입점만 담는다.
"""
import logging

from .models import SiteConfig, ImageCache
from .discovery import build_recipe
from .extract import execute_recipe
from .validate import validate
from .store import load_recipe, save_recipe, stage_for_review

logger = logging.getLogger("marathon_crawler")


def scrape_site(site: SiteConfig) -> None:
    logger.info("=== scrape_site: %s ===", site.base_url)
    cache: ImageCache = {}                               # 이미지 해시 -> vision 결과 (이번 실행 동안)
    recipe = load_recipe(site.id)                        # ← '라우터' = 스토어 조회 (LLM 아님)
    if recipe is None:                                   # 새 사이트 → cold path (드물게)
        logger.info("레시피 없음 → cold path (build)")
        recipe = build_recipe(site.base_url, site.sample_url)
        save_recipe(site.id, recipe)
    else:
        logger.info("레시피 있음 (v%d) → hot path", recipe.version)

    rows = execute_recipe(recipe, site.list_url, cache)  # hot path (매번)
    errors = validate(rows)                              # 싼 게이트

    if errors:                                           # 깨짐 → cold path로 복구
        logger.warning("검증 실패 → 복구 (레시피 재생성)")
        recipe = build_recipe(site.base_url, site.sample_url)
        save_recipe(site.id, recipe)
        rows = execute_recipe(recipe, site.list_url, cache)
        errors = validate(rows)                          # 복구 후에도 검증 — 조용히 깨진 데이터 stage 방지
        if errors:
            logger.error("복구 후에도 검증 실패 — 사람 확인 필요: %s", errors[:3])

    stage_for_review(site.id, rows)                      # diff + 사람 게이트 (파일 스테이징)
    logger.info("=== scrape_site 완료: %d rows staged ===", len(rows))


def crawl_all(sites: list[SiteConfig]) -> None:
    """바깥 루프: 스케줄러(Celery beat 등)가 사이트별로 주기 실행."""
    for site in sites:
        scrape_site(site)
