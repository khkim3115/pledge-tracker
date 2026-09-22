"""선관위 API 원본 응답 → DB 행(winners, pledges) 변환."""

from __future__ import annotations

import re

# 선거ID → 민선 기수
TERMS = {"20220601": 8, "20260603": 9}

# 공약 API 제공 대상 중 이 서비스 범위 (대통령 제외)
SG_TYPES = {3: "시도지사", 4: "구시군장", 11: "교육감"}

# 공개 DB(raw jsonb)에 싣지 않는 개인 정보. 로컬 원본 JSONL에는 그대로 남는다.
PRIVATE_FIELDS = frozenset({"addr", "birthday"})

MAX_PLEDGES = 10


def _clean(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def winner_row(item: dict, sg_id: str, sg_typecode: int) -> dict:
    huboid = _clean(item.get("huboid"))
    if not huboid:
        raise ValueError(f"huboid 없음: {item}")
    sido = _clean(item.get("sdName")) or ""
    sgg = _clean(item.get("sggName")) or sido
    wiw = _clean(item.get("wiwName"))
    region = sido if sg_typecode in (3, 11) else f"{sido} {wiw or sgg}".strip()
    return {
        "winner_id": f"{sg_id}-{huboid}",
        "sg_id": sg_id,
        "sg_type": sg_typecode,
        "huboid": huboid,
        "term": TERMS[sg_id],
        "sido_name": sido,
        "sgg_name": sgg,
        "wiw_name": wiw,
        "region": region,
        "party": _clean(item.get("jdName")),
        "name": _clean(item.get("name")) or "",
        "raw": {k: v for k, v in item.items() if k not in PRIVATE_FIELDS},
    }


def pledge_rows(item: dict, winner_id: str, term: int) -> list[dict]:
    """공약 응답 1건을 공약별 행으로 편다.

    응답 1건 = 후보자 1명: prmsOrd{i}, prmsRealmName{i}, prmsTitle{i}, prmmCont{i} (i = 1..N)
    공약 본문은 문서상 prmsCont{i}이지만 실제 응답은 prmmCont{i}다 → 둘 다 읽는다.
    prmsRealmName{i}은 대부분 비어 있다.
    """
    indexes = sorted(
        {int(m.group(1)) for k in item if (m := re.fullmatch(r"prmsTitle(\d+)", k))}
    ) or range(1, MAX_PLEDGES + 1)
    rows = []
    for i in indexes:
        title = _clean(item.get(f"prmsTitle{i}"))
        if not title:
            continue
        ord_ = _clean(item.get(f"prmsOrd{i}"))
        rows.append(
            {
                "pledge_id": f"{winner_id}-{ord_ or i}",
                "winner_id": winner_id,
                "ord": int(ord_) if ord_ and ord_.isdigit() else i,
                "field": _clean(item.get(f"prmsRealmName{i}")),
                "title": title,
                "content": _clean(item.get(f"prmmCont{i}") or item.get(f"prmsCont{i}")),
                "source": "nec_api",
                "term": term,
                "raw": {
                    k: item[k]
                    for k in (
                        f"prmsOrd{i}",
                        f"prmsRealmName{i}",
                        f"prmsTitle{i}",
                        f"prmmCont{i}",
                        f"prmsCont{i}",
                    )
                    if k in item
                },
            }
        )
    return rows
