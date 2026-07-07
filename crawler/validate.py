"""싼 결정론 검증 — 매 스크랩 1차 게이트 (LLM 평가의 '보완', '대체' 아님)."""
import logging

from .models import Row
from .extract import _parse_date

logger = logging.getLogger("marathon_crawler")


def validate(rows: list[Row]) -> list[str]:
    errors: list[str] = []
    if not rows:
        errors.append("대회가 0건 — 셀렉터가 깨졌을 가능성")
    for r in rows[:50]:
        for f in ("name", "date", "register_url"):
            if not r.get(f):
                errors.append(f"필수 필드 누락: {f}")
        close = r.get("reg_close")
        if close and not _parse_date(close):
            errors.append(f"마감일 파싱 불가: {close}")
    errors = list(dict.fromkeys(errors))                 # 중복 제거(순서 유지) — 행마다 같은 메시지 폭주 방지
    if errors:
        logger.warning("validate: %d개 문제 — %s", len(errors), errors[:3])
    else:
        logger.info("validate: 통과 (%d rows)", len(rows))
    return errors
