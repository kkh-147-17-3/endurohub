"""파일 기반 스토어 — 레시피 저장/조회 + 스테이징. Django ORM 아님."""
import json
import logging

from .config import STORE_DIR
from .models import ExtractionRecipe, Row

logger = logging.getLogger("marathon_crawler")


def load_recipe(site_id: int) -> ExtractionRecipe | None:
    p = STORE_DIR / "recipes" / f"{site_id}.json"
    if not p.exists():
        return None
    return ExtractionRecipe.model_validate_json(p.read_text(encoding="utf-8"))


def save_recipe(site_id: int, recipe: ExtractionRecipe) -> None:
    p = STORE_DIR / "recipes" / f"{site_id}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(recipe.model_dump_json(indent=2), encoding="utf-8")
    logger.info("recipe 저장 -> %s", p)


def stage_for_review(site_id: int, rows: list[Row]) -> None:
    # 기존 vs 신규 diff → pending_review 적재 자리. 지금은 jsonl 로 스테이징(사람이 검토 후 반영).
    p = STORE_DIR / "staged" / f"{site_id}.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    logger.info("staged %d rows -> %s", len(rows), p)
