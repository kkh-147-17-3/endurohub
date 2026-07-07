"""마라톤 대회 크롤러 — LangChain 기반, Django 비의존 자립 패키지.

책임별 모듈:
  config    설정/.env 로드
  models    자체 pydantic 모델
  llm       LangChain LLM 레이어
  tools     탐색 도구(@tool)
  extract   hot path(정적/브라우저 추출)
  validate  결정론 검증 게이트
  store     파일 기반 스토어
  discovery cold path(레시피 생성/평가)
  race_crawler  오케스트레이션 진입점
"""
from .models import (
    SiteConfig, FieldSpec, DiscoveredRecipe, ExtractionRecipe, Verdict, RecipeBuildFailed,
)
from .discovery import build_recipe, discover_recipe, evaluate_recipe
from .extract import execute_recipe
from .validate import validate
from .llm import run_agent, structured_call, vision_extract
from .race_crawler import scrape_site, crawl_all

__all__ = [
    "SiteConfig", "FieldSpec", "DiscoveredRecipe", "ExtractionRecipe", "Verdict",
    "RecipeBuildFailed", "build_recipe", "discover_recipe", "evaluate_recipe",
    "execute_recipe", "validate", "run_agent", "structured_call", "vision_extract",
    "scrape_site", "crawl_all",
]
