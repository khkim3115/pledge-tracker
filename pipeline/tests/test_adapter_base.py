from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from pledge_pipeline.adapters.base import Adapter, ParsedTask, RawDocument, validate_mapping

AS_OF = date(2026, 6, 30)


class DummyAdapter(Adapter):
    adapter_id = "dummy"
    region = "가상도"
    term = 8
    base_url = "https://example.invalid/"
    parser_type = "html"
    status_mapping = {"완료": "completed", "이행후계속추진": "continuing", "정상추진": "on_track"}

    def fetch(self):
        yield RawDocument(self.base_url, b"", "text/html", datetime.now(UTC))

    def parse(self, doc):
        for i, status in enumerate(["완료", "이행 후 계속추진", "정상추진", "검토중"]):
            yield ParsedTask(str(i), f"과제{i}", AS_OF, doc.url, raw_status=status)


def test_normalize_maps_known_and_leaves_unknown_none(caplog):
    results = list(DummyAdapter().run())
    assert [r.normalized_status for r in results] == ["completed", "continuing", "on_track", None]
    assert "검토중" in caplog.text


def test_content_hash_ignores_non_status_fields():
    a = ParsedTask("1", "이름A", AS_OF, "u", raw_status="완료", progress_text="실적")
    b = ParsedTask("1", "이름B", date(2026, 12, 31), "v", raw_status="완료", progress_text="실적")
    c = ParsedTask("1", "이름A", AS_OF, "u", raw_status="완료", progress_text="실적 추가")
    assert a.content_hash() == b.content_hash() != c.content_hash()


def test_validate_mapping_rejects_unknown_code():
    validate_mapping({"완료": "completed"})
    with pytest.raises(ValueError):
        validate_mapping({"완료": "done"})
