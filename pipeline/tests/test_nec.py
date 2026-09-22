"""선관위 API 변환·페이지네이션 테스트 (네트워크 없음). 응답은 가상의 값이다."""

from __future__ import annotations

import pytest

from pledge_pipeline.nec.client import NecApiError, NecClient, _items
from pledge_pipeline.nec.models import pledge_rows, winner_row

WINNER = {
    "huboid": "100000001",
    "sgId": "20220601",
    "sgTypecode": "4",
    "sdName": "가상도",
    "sggName": "가상시",
    "wiwName": "가상시",
    "jdName": "가상정당",
    "name": "홍길동",
    "addr": "가상도 가상시 어딘가 1",
    "birthday": "19700101",
    "age": "56",
}

PLEDGE_ITEM = {
    "cnddtId": "100000001",
    "prmsCnt": "2",
    "prmsOrd1": "1",
    "prmsRealmName1": "교통",
    "prmsTitle1": "순환버스 신설",
    "prmmCont1": "○ 목표\n- 순환버스 3개 노선",
    "prmsOrd2": "2",
    "prmsRealmName2": "복지",
    "prmsTitle2": " 공공 돌봄센터 확충 ",
    "prmmCont2": "",
    "prmsOrd3": "",
    "prmsTitle3": "",
}


def test_winner_row_basic_and_private_fields_dropped():
    row = winner_row(WINNER, "20220601", 4)
    assert row["winner_id"] == "20220601-100000001"
    assert row["term"] == 8
    assert row["region"] == "가상도 가상시"
    assert row["party"] == "가상정당"
    assert "addr" not in row["raw"] and "birthday" not in row["raw"]
    assert row["raw"]["age"] == "56"


def test_winner_row_metro_region_is_sido():
    row = winner_row({**WINNER, "sggName": "가상도", "wiwName": ""}, "20220601", 3)
    assert row["region"] == "가상도"


def test_pledge_rows_flattens_and_skips_empty():
    rows = pledge_rows(PLEDGE_ITEM, "20220601-100000001", 8)
    assert [r["pledge_id"] for r in rows] == ["20220601-100000001-1", "20220601-100000001-2"]
    assert rows[1]["title"] == "공공 돌봄센터 확충"
    assert rows[1]["content"] is None
    assert rows[0]["raw"] == {
        k: PLEDGE_ITEM[k] for k in ("prmsOrd1", "prmsRealmName1", "prmsTitle1", "prmmCont1")
    }


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ({"items": {"item": [{"a": 1}, {"a": 2}]}}, 2),
        ({"items": {"item": {"a": 1}}}, 1),
        ({"items": ""}, 0),
        ({}, 0),
    ],
)
def test_items_shapes(body, expected):
    assert len(_items(body)) == expected


class FakeResponse:
    def __init__(self, payload=None, text="", status=200):
        self._payload, self.text, self.status_code = payload, text, status

    def json(self):
        if self._payload is None:
            raise ValueError("not json")
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append(params)
        return self.responses.pop(0)


def page(items, total, code="INFO-00"):
    return FakeResponse(
        {
            "response": {
                "header": {"resultCode": code, "resultMsg": "NORMAL SERVICE"},
                "body": {"items": {"item": items}, "totalCount": total},
            }
        }
    )


def test_paginates_until_total():
    session = FakeSession([page([{"huboid": "1"}, {"huboid": "2"}], 3), page([{"huboid": "3"}], 3)])
    client = NecClient("key", session=session, delay=0)
    got = list(client._paginate("u", {}, page_size=2))
    assert [g["huboid"] for g in got] == ["1", "2", "3"]
    assert [c["pageNo"] for c in session.calls] == [1, 2]


def test_encoded_key_is_decoded():
    assert NecClient("ab%2Bcd%3D%3D", delay=0).service_key == "ab+cd=="


def test_no_data_code_returns_empty():
    session = FakeSession([page(None, 0, code="INFO-03")])
    assert NecClient("k", session=session, delay=0).pledges("20220601", 3, "1") == []


def test_xml_auth_error_raises():
    xml = (
        "<OpenAPI_ServiceResponse><cmmMsgHeader><errMsg>SERVICE ERROR</errMsg>"
        "<returnAuthMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</returnAuthMsg>"
        "<returnReasonCode>30</returnReasonCode></cmmMsgHeader></OpenAPI_ServiceResponse>"
    )
    session = FakeSession([FakeResponse(text=xml)])
    with pytest.raises(NecApiError, match="SERVICE_KEY_IS_NOT_REGISTERED_ERROR"):
        NecClient("k", session=session, delay=0).pledges("20220601", 3, "1")
