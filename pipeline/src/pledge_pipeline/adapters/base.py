"""어댑터 공통 인터페이스: fetch → parse → normalize.

지자체마다 다른 것은 설정(URL, 셀렉터, 문서 형식, 상태값 매핑)과 파서뿐이다.
한 어댑터가 실패해도 다른 어댑터는 계속 돈다(어댑터 단위 격리).
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from dataclasses import field as dc_field
from datetime import date, datetime

log = logging.getLogger(__name__)

# 매니페스토 표준 5분류 (supabase normalized_statuses.code)
NORMALIZED_STATUSES = ("completed", "continuing", "on_track", "partial", "stalled")


@dataclass(frozen=True)
class RawDocument:
    url: str
    content: bytes
    content_type: str | None
    fetched_at: datetime


@dataclass
class ParsedTask:
    """지자체가 공개한 과제 1건의 한 시점 상태. 값은 원문 그대로 둔다."""

    external_id: str
    name: str
    as_of: date  # 기준일 (예: 2026-06-30). 공개 주기가 지자체마다 달라 날짜로 둔다
    source_url: str
    period_label: str | None = None  # 원문 표기 (예: '2026년 6월 말 기준')
    field: str | None = None
    dept: str | None = None
    budget_raw: str | None = None
    raw_status: str | None = None
    progress_rate: float | None = None
    progress_text: str | None = None
    extra: dict = dc_field(default_factory=dict)

    def content_hash(self) -> str:
        """스냅샷 diff 감지용. 상태·진척률·실적 텍스트가 같으면 재처리하지 않는다."""
        key = json.dumps(
            [self.raw_status, self.progress_rate, self.progress_text],
            ensure_ascii=False,
        )
        return hashlib.sha256(key.encode("utf-8")).hexdigest()


@dataclass
class NormalizedTask:
    task: ParsedTask
    normalized_status: str | None  # 매핑에 없는 원문 상태값은 추측하지 않고 None


def status_key(raw: str) -> str:
    """상태값 비교 키: 공백 제거 ('이행 후 계속추진' == '이행후계속추진')."""
    return re.sub(r"\s+", "", raw)


class Adapter(ABC):
    adapter_id: str
    region: str
    term: int
    base_url: str
    parser_type: str  # html | pdf | hwp | xlsx | api
    # 원문 상태값 → 표준 5분류 (공백 무시).
    # 새 상태값은 경고 후 None으로 적재하고 사람이 매핑을 추가한다.
    status_mapping: dict[str, str] = {}

    @abstractmethod
    def fetch(self) -> Iterable[RawDocument]:
        """원천 문서(HTML/PDF/HWP 등)를 가져온다."""

    @abstractmethod
    def parse(self, doc: RawDocument) -> Iterable[ParsedTask]:
        """문서에서 과제 목록을 추출한다."""

    def normalize(self, task: ParsedTask) -> NormalizedTask:
        raw = (task.raw_status or "").strip()
        mapping = {status_key(k): v for k, v in self.status_mapping.items()}
        status = mapping.get(status_key(raw))
        if raw and status is None:
            log.warning(
                "[%s] 매핑되지 않은 상태값: %r (%s)", self.adapter_id, raw, task.external_id
            )
        return NormalizedTask(task=task, normalized_status=status)

    def run(self) -> Iterator[NormalizedTask]:
        for doc in self.fetch():
            for task in self.parse(doc):
                yield self.normalize(task)

    def describe(self) -> dict:
        return {
            "adapter_id": self.adapter_id,
            "region": self.region,
            "term": self.term,
            "base_url": self.base_url,
            "parser_type": self.parser_type,
        }


def validate_mapping(mapping: dict[str, str]) -> None:
    bad = {k: v for k, v in mapping.items() if v not in NORMALIZED_STATUSES}
    if bad:
        raise ValueError(f"알 수 없는 표준 상태값: {bad}")


__all__ = [
    "Adapter",
    "NORMALIZED_STATUSES",
    "NormalizedTask",
    "ParsedTask",
    "RawDocument",
    "status_key",
    "validate_mapping",
]
