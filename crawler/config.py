"""설정 — .env 로드 + 상수. Django 비의존."""
import os
from pathlib import Path


def _load_env() -> None:
    """레포 루트의 .env / api/.env 를 best-effort 로드 (이미 설정된 값은 override 안 함)."""
    try:
        from dotenv import load_dotenv
        root = Path(__file__).resolve().parent.parent
        load_dotenv(root / ".env")
        load_dotenv(root / "api" / ".env")
    except Exception:
        pass


_load_env()

MODEL: str = os.environ.get("CRAWLER_MODEL", "gpt-5.4-nano")
EFFORT_DISCOVERY: str = "medium"       # 탐색은 약간의 추론 필요
EFFORT_FAST: str = "low"               # 추출/평가/vision — 빠르고 싸게
TARGET_FIELDS: list[str] = ["name", "date", "location", "reg_open", "reg_close", "register_url", "fee"]
STORE_DIR: Path = Path(os.environ.get("CRAWLER_STORE", Path(__file__).resolve().parent / "store"))
