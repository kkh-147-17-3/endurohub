"""탐색 도구 — LangChain @tool + 정제 헬퍼 (requests + BS4)."""
import json
import logging

import requests
from bs4 import BeautifulSoup, Tag
from langchain_core.tools import tool, BaseTool

from .models import DiscoveredRecipe

logger = logging.getLogger("marathon_crawler")


def _plain_text(url: str) -> str:
    soup = BeautifulSoup(requests.get(url, timeout=10).text, "html.parser")
    for t in soup(["script", "style", "noscript", "svg"]):
        t.decompose()
    return soup.get_text(" ", strip=True)[:6000]


def _img_src(img: Tag) -> str | None:
    for attr in ("src", "data-src", "data-original", "data-lazy-src"):  # lazy-load 대응
        v = img.get(attr)
        if v:
            return str(v)
    ss = img.get("srcset")
    if ss:
        return str(ss).split(",")[0].strip().split(" ")[0]
    return None


@tool
def fetch_page(url: str) -> str:
    """URL의 정제된 텍스트를 반환한다."""
    logger.info("  fetch_page: %s", url)
    return _plain_text(url)


@tool
def list_links(url: str) -> str:
    """페이지의 링크 목록(text, href)을 JSON으로 반환한다."""
    logger.info("  list_links: %s", url)
    soup = BeautifulSoup(requests.get(url, timeout=10).text, "html.parser")
    links = [{"text": a.get_text(strip=True)[:40], "href": a.get("href")}
             for a in soup.find_all("a", href=True)][:60]
    return json.dumps(links, ensure_ascii=False)


@tool
def list_images(url: str) -> str:
    """페이지의 이미지 인벤토리(src, alt, class, width, height)를 JSON으로 반환한다.

    LLM이 로고·아이콘이 아닌 '대회 안내/포스터' 이미지를 근거 있게 고르도록 돕는다.
    """
    logger.info("  list_images: %s", url)
    soup = BeautifulSoup(requests.get(url, timeout=10).text, "html.parser")
    imgs = [{"src": _img_src(img),
             "alt": (img.get("alt") or "")[:60],
             "class": " ".join(img.get("class") or [])[:60],
             "width": img.get("width"), "height": img.get("height")}
            for img in soup.find_all("img")][:60]
    return json.dumps(imgs, ensure_ascii=False)


@tool("submit_recipe", args_schema=DiscoveredRecipe)
def submit_recipe(**kwargs) -> str:
    """탐색 끝. 완성된 추출 레시피를 제출한다."""
    return "submitted"      # terminal tool — 실제로는 run_agent 가 호출을 가로챈다


# 모델에 바인딩할 도구들 + 실행 매핑(터미널 submit_recipe 제외)
EXPLORER_TOOLS: list[BaseTool] = [fetch_page, list_links, list_images, submit_recipe]
EXPLORER_IMPLS: dict[str, BaseTool] = {
    t.name: t for t in EXPLORER_TOOLS if t.name != "submit_recipe"
}
