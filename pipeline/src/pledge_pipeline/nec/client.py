"""선관위 Open API 클라이언트.

- 당선인정보: WinnerInfoInqireService2/getWinnerInfoInqire
- 선거공약정보: ElecPrmsInfoInqireService/getCnddtElecPrmsInfoInqire (후보자 1명 단위 조회)

일일 트래픽 한도(개발계정 1만 건)는 선거 후 1회 적재 방식이라 문제되지 않는다.
민선8기 전체 = 당선인 목록 수 회 + 당선인 수(약 260)만큼의 공약 조회.
"""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from urllib.parse import unquote

import requests

log = logging.getLogger(__name__)

BASE_URL = "https://apis.data.go.kr/9760000"
WINNER_URL = f"{BASE_URL}/WinnerInfoInqireService2/getWinnerInfoInqire"
PLEDGE_URL = f"{BASE_URL}/ElecPrmsInfoInqireService/getCnddtElecPrmsInfoInqire"

RESULT_OK = "INFO-00"
RESULT_NO_DATA = "INFO-03"


class NecApiError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _items(body: dict) -> list[dict]:
    """body.items.item은 결과가 1건이면 dict, 여러 건이면 list, 없으면 ''로 온다."""
    items = body.get("items") or {}
    item = items.get("item") if isinstance(items, dict) else None
    if item is None:
        return []
    return [item] if isinstance(item, dict) else list(item)


def _xml_error(text: str) -> NecApiError | None:
    """인증 오류 등은 resultType=json이어도 XML(OpenAPI_ServiceResponse)로 온다."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return None
    code = root.findtext(".//returnReasonCode") or root.findtext(".//resultCode") or "XML"
    msg = (
        root.findtext(".//returnAuthMsg")
        or root.findtext(".//errMsg")
        or root.findtext(".//resultMsg")
        or text[:200]
    )
    return NecApiError(code, msg)


class NecClient:
    def __init__(
        self,
        service_key: str,
        *,
        session: requests.Session | None = None,
        delay: float = 0.1,
        max_retries: int = 3,
        timeout: float = 30.0,
    ):
        # Encoding 키가 들어와도 동작하도록 디코딩해 둔다 (requests가 다시 인코딩한다).
        self.service_key = unquote(service_key) if "%" in service_key else service_key
        self.session = session or requests.Session()
        self.delay = delay
        self.max_retries = max_retries
        self.timeout = timeout

    def _get(self, url: str, params: dict) -> dict:
        query = {"serviceKey": self.service_key, "resultType": "json", **params}
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, params=query, timeout=self.timeout)
            except (requests.ConnectionError, requests.Timeout) as e:
                if attempt == self.max_retries:
                    raise
                log.warning("요청 실패(%s), 재시도 %d/%d", e, attempt, self.max_retries)
                time.sleep(2**attempt)
                continue
            if resp.status_code >= 500 and attempt < self.max_retries:
                log.warning("HTTP %s, 재시도 %d/%d", resp.status_code, attempt, self.max_retries)
                time.sleep(2**attempt)
                continue
            break

        if self.delay:
            time.sleep(self.delay)

        try:
            data = resp.json()
        except ValueError:
            err = _xml_error(resp.text) or NecApiError(f"HTTP{resp.status_code}", resp.text[:200])
            raise err from None
        if resp.status_code >= 400:
            raise NecApiError(f"HTTP{resp.status_code}", str(data)[:200])

        response = data.get("response", data)
        header = response.get("header", {})
        code = header.get("resultCode", "")
        if code == RESULT_NO_DATA:
            return {"items": "", "totalCount": 0}
        if code != RESULT_OK:
            raise NecApiError(code, header.get("resultMsg", ""))
        return response.get("body", {})

    def _paginate(self, url: str, params: dict, page_size: int = 100) -> Iterator[dict]:
        page = 1
        while True:
            body = self._get(url, {**params, "pageNo": page, "numOfRows": page_size})
            yield from _items(body)
            total = int(body.get("totalCount") or 0)
            if page * page_size >= total:
                return
            page += 1

    def winners(self, sg_id: str, sg_typecode: int) -> Iterator[dict]:
        """당선인 목록. sg_typecode: 3 시도지사, 4 구시군장, 11 교육감."""
        return self._paginate(WINNER_URL, {"sgId": sg_id, "sgTypecode": sg_typecode})

    def pledges(self, sg_id: str, sg_typecode: int, cnddt_id: str) -> list[dict]:
        """후보자 1명의 공약. 응답 1건에 prmsOrd1..N/prmsTitle1..N 형태로 여러 공약이 들어 있다."""
        params = {"sgId": sg_id, "sgTypecode": sg_typecode, "cnddtId": cnddt_id}
        return list(self._paginate(PLEDGE_URL, params))
