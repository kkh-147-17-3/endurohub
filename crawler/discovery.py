"""cold path — 탐색(생성) → 실행 → 평가 → 재시도. 드물게만 돈다."""
import json
import logging

from . import config
from .models import DiscoveredRecipe, ExtractionRecipe, Verdict, RecipeBuildFailed, Row
from .llm import run_agent, structured_call
from .tools import EXPLORER_TOOLS, EXPLORER_IMPLS, _plain_text
from .extract import execute_recipe

logger = logging.getLogger("marathon_crawler")


def discover_recipe(base_url: str, feedback: str | None = None) -> ExtractionRecipe:
    logger.info("discover_recipe: %s (feedback=%s)", base_url, bool(feedback))
    system = (
        "너는 마라톤 대회 사이트의 구조를 탐색해 추출 레시피를 만든다. "
        f"목표 필드: {config.TARGET_FIELDS}. 도구로 페이지를 둘러보고 각 필드가 어느 페이지"
        "(리스트/상세)·어느 셀렉터에 있는지 찾아라. 상세 페이지 필드는 page='detail'과 "
        "detail_link, 모달/팝업 이미지 안이면 open·img를 지정해 submit_recipe로 제출하라. "
        "이미지 필드(img)는 반드시 list_images로 인벤토리를 먼저 확인하고, 로고·아이콘·배너·SNS "
        "버튼이 아니라 '대회 안내/포스터'를 가리키는 셀렉터를 골라라. class/alt/파일명에 poster·"
        "대회·요강·안내·코스 등이 든 큰 이미지를 우선한다(런타임도 큰 이미지를 우선 선택함)."
    )
    user = f"사이트: {base_url}"
    if feedback:                                        # 직전 평가의 지적을 반영해 재탐색
        user += f"\n\n직전 시도의 문제점(고쳐서 다시): {feedback}"
    out = run_agent(system, user, EXPLORER_TOOLS, EXPLORER_IMPLS,
                    terminal_tool="submit_recipe", effort=config.EFFORT_DISCOVERY, max_steps=15)
    if "result" not in out:                              # 모델이 submit_recipe 없이 종료 → 명확한 실패
        raise RecipeBuildFailed(f"{base_url}: 모델이 submit_recipe를 호출하지 않고 종료")
    discovered = DiscoveredRecipe.model_validate(out["result"])
    logger.info("discover_recipe: %d fields, needs_js=%s, detail_link=%s",
                len(discovered.fields), discovered.needs_js, bool(discovered.detail_link))
    return ExtractionRecipe(base_url=base_url, **discovered.model_dump())


def evaluate_recipe(recipe: ExtractionRecipe, sample: list[Row], page_text: str) -> Verdict:
    """LLM-as-judge. '실제 페이지 텍스트'에 근거해 판정 (감으로 판정 금지)."""
    system = ("추출 결과가 페이지 내용과 의미적으로 맞는지 검증한다. "
              "타입이 맞아도 '대회일을 접수마감일로 잘못 뽑은' 류의 의미 오류를 잡아라.")
    user = (f"추출 결과(샘플):\n{json.dumps(sample[:3], ensure_ascii=False)}\n\n"
            f"실제 페이지 텍스트(발췌):\n{page_text[:3000]}")
    verdict = structured_call(system, user, Verdict)
    logger.info("evaluate_recipe: ok=%s issues=%s", verdict.ok, verdict.issues[:80])
    return verdict


def build_recipe(base_url: str, sample_url: str, *, max_attempts: int = 3) -> ExtractionRecipe:
    feedback: str | None = None
    for attempt in range(max_attempts):                 # 생성 → 테스트 → 평가 → 보정
        logger.info("build_recipe: attempt %d/%d (%s)", attempt + 1, max_attempts, base_url)
        recipe = discover_recipe(base_url, feedback)    # 1. 탐색방법 정리
        sample = execute_recipe(recipe, sample_url)     # 2. 실제로 탐색 (코드)
        verdict = evaluate_recipe(recipe, sample, _plain_text(sample_url))  # 3. 평가
        if verdict.ok:
            logger.info("build_recipe: accepted (attempt %d)", attempt + 1)
            return recipe
        feedback = verdict.issues                       # 4. 안 맞으면 다시
    logger.warning("build_recipe: 실패 — %d회 시도 후 포기 (%s)", max_attempts, base_url)
    raise RecipeBuildFailed(base_url)                   # 포기 → 사람에게 플래그
