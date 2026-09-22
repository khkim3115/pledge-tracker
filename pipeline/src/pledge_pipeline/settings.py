"""환경 변수 로딩. 로컬은 레포 루트 .env, Actions는 Repository Secrets."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"

load_dotenv(REPO_ROOT / ".env")


def require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(
            f"환경 변수 {name}가 비어 있습니다. .env.example을 참고해 .env에 설정하세요."
        )
    return value


def optional(name: str) -> str | None:
    return os.environ.get(name, "").strip() or None
