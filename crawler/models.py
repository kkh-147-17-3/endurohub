"""자체 pydantic 모델 — Django 비의존 계약서 (타입 + tool 스키마 + 검증)."""
from __future__ import annotations
from typing import Literal

from pydantic import BaseModel

Row = dict[str, "str | None"]          # 한 행: 필드명 -> 값 or None
ImageCache = dict[str, "str | None"]   # 이미지 해시 -> vision 결과


class RecipeBuildFailed(Exception):
    """평가자-최적화자 루프가 max_attempts 안에 맞는 레시피를 못 만든 경우 -> 사람에게 플래그."""


class SiteConfig(BaseModel):
    """scrape_site 가 기대하는 사이트 레코드 (Django 모델 아님, 자립형)."""
    id: int
    base_url: str
    sample_url: str
    list_url: str


class FieldSpec(BaseModel):
    page: Literal["list", "detail"] = "list"
    sel: str | None = None        # 텍스트/속성 필드의 셀렉터
    attr: str | None = None       # 뽑을 속성(href 등); None이면 텍스트
    open: str | None = None       # 이미지: 모달 여는 클릭 셀렉터
    img: str | None = None        # 이미지: img 셀렉터 (있으면 vision으로 읽음)


class DiscoveredRecipe(BaseModel):
    """LLM이 탐색 후 emit하는 부분 (base_url/version은 코드가 채운다)."""
    needs_js: bool
    list_selector: str
    fields: dict[str, FieldSpec]
    detail_link: str | None = None
    pagination: str | None = None


class ExtractionRecipe(DiscoveredRecipe):
    base_url: str
    version: int = 1


class Verdict(BaseModel):
    ok: bool
    issues: str = ""


class DistanceFee(BaseModel):
    """대회 종목 하나 — 페이지 원문 표기 그대로의 이름 + 참가비(원)."""
    name: str
    fee: int | None = None


class EnrichExtraction(BaseModel):
    """보강(enrich) 추출 결과 — 페이지에서 확인 못 한 필드는 None."""
    distances: list[DistanceFee] | None = None
    giveaways: list[str] | None = None


# future annotations 하에서 중첩 포워드레퍼런스(FieldSpec 등)를 미리 확정해 둔다.
DiscoveredRecipe.model_rebuild()
ExtractionRecipe.model_rebuild()
EnrichExtraction.model_rebuild()
