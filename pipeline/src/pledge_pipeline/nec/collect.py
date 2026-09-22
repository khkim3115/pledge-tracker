"""선관위 API로 당선인·공약을 전수 수집해 원본 JSONL로 저장하고, 선택적으로 DB에 적재한다.

# 수집 → data/raw/nec/20220601/{winners,pledges}.jsonl, summary.json
python -m pledge_pipeline.nec.collect --sg-id 20220601
# 수집 + DB 적재 / 기존 JSONL만 적재
python -m pledge_pipeline.nec.collect --sg-id 20220601 --load
python -m pledge_pipeline.nec.collect --sg-id 20220601 --load --skip-fetch
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from ..settings import DATA_DIR, require
from .client import NecApiError, NecClient
from .models import SG_TYPES, TERMS, pledge_rows, winner_row

log = logging.getLogger("nec.collect")

# 기대 당선인 수 (적재 건수 검증용). 민선9기는 광주·전남 통합(광역 16)과 기초 개편(227)이 반영됨.
EXPECTED_WINNERS = {
    "20220601": {3: 17, 4: 226, 11: 17},
    "20260603": {3: 16, 4: 227, 11: 16},
}


def no_pledge_reason(winner: dict) -> str:
    """공약 응답이 없는 당선인의 사유 추정. 득표수 0 = 무투표 당선(선거운동·공약서 없음)."""
    if str(winner.get("dugsu", "")).strip() in ("", "0"):
        return "무투표 당선"
    return "공약서 미제출 추정 (선거공약서는 임의 제출)"


def _read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def fetch(client: NecClient, sg_id: str, types: list[int], out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    winners_by_type: Counter[int] = Counter()
    pledge_items = 0
    no_pledges: list[dict] = []
    errors: list[dict] = []

    with (
        (out_dir / "winners.jsonl").open("w", encoding="utf-8") as wf,
        (out_dir / "pledges.jsonl").open("w", encoding="utf-8") as pf,
    ):
        for sg_type in types:
            winners = list(client.winners(sg_id, sg_type))
            log.info("%s 당선인 %d명", SG_TYPES[sg_type], len(winners))
            for item in winners:
                winners_by_type[sg_type] += 1
                wf.write(json.dumps({"sgTypecode": sg_type, **item}, ensure_ascii=False) + "\n")
                huboid = str(item.get("huboid", ""))
                label = f"{item.get('sdName', '')} {item.get('sggName', '')} {SG_TYPES[sg_type]}"
                try:
                    items = client.pledges(sg_id, sg_type, huboid)
                except NecApiError as e:
                    log.error("공약 조회 실패 %s (%s): %s", label, huboid, e)
                    errors.append({"huboid": huboid, "label": label, "error": str(e)})
                    continue
                if not items:
                    no_pledges.append(
                        {"huboid": huboid, "label": label, "reason": no_pledge_reason(item)}
                    )
                for p in items:
                    row = {"sgTypecode": sg_type, "huboid": huboid, **p}
                    pf.write(json.dumps(row, ensure_ascii=False) + "\n")
                    pledge_items += 1

    summary = {
        "sg_id": sg_id,
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "winners_by_type": {SG_TYPES[t]: winners_by_type[t] for t in types},
        "pledge_items": pledge_items,
        "winners_without_pledges": no_pledges,
        "errors": errors,
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def build_rows(sg_id: str, in_dir: Path) -> tuple[list[dict], list[dict]]:
    term = TERMS[sg_id]
    winners = [
        winner_row(w, sg_id, int(w["sgTypecode"])) for w in _read_jsonl(in_dir / "winners.jsonl")
    ]
    by_huboid = {w["huboid"]: w["winner_id"] for w in winners}
    pledges: list[dict] = []
    for item in _read_jsonl(in_dir / "pledges.jsonl"):
        winner_id = by_huboid.get(str(item["huboid"]))
        if winner_id is None:
            log.warning("당선인 목록에 없는 공약 응답: huboid=%s", item["huboid"])
            continue
        pledges.extend(pledge_rows(item, winner_id, term))

    dup = [k for k, n in Counter((p["winner_id"], p["ord"]) for p in pledges).items() if n > 1]
    if dup:
        raise ValueError(f"(winner_id, ord) 중복 {len(dup)}건 — 적재 중단: {dup[:5]}")

    # fetched_at = API 수집 시점 (재적재 시에도 갱신)
    summary = in_dir / "summary.json"
    fetched_at = (
        json.loads(summary.read_text(encoding="utf-8")).get("fetched_at")
        if summary.exists()
        else None
    ) or datetime.now(UTC).isoformat(timespec="seconds")
    for row in (*winners, *pledges):
        row["fetched_at"] = fetched_at
    return winners, pledges


def load(sg_id: str, in_dir: Path) -> dict:
    from ..db import connect, find_stale, upsert  # DB 적재 시에만 psycopg 연결

    winners, pledges = build_rows(sg_id, in_dir)
    with connect() as conn:
        n_w = upsert(conn, "winners", winners, conflict=["winner_id"])
        n_p = upsert(conn, "pledges", pledges, conflict=["pledge_id"])
        stale = find_stale(
            conn,
            "pledges",
            "pledge_id",
            "winner_id",
            [w["winner_id"] for w in winners],
            [p["pledge_id"] for p in pledges],
        )
        conn.commit()
    if stale:
        log.warning(
            "원천 응답에 없는 기존 공약 %d건 (삭제하지 않음, 확인 필요): %s", len(stale), stale
        )
    return {"winners": n_w, "pledges": n_p, "stale_pledges": len(stale)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="선관위 당선인·공약 수집")
    ap.add_argument("--sg-id", required=True, choices=sorted(TERMS), help="선거ID")
    ap.add_argument(
        "--types",
        default="3,4,11",
        help="sgTypecode 목록 (3 시도지사, 4 구시군장, 11 교육감)",
    )
    ap.add_argument("--out", type=Path, help="원본 JSONL 경로 (기본: data/raw/nec/<sg-id>)")
    ap.add_argument("--load", action="store_true", help="수집 후 DATABASE_URL로 적재")
    ap.add_argument("--skip-fetch", action="store_true", help="API 호출 없이 기존 JSONL만 사용")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sys.stdout.reconfigure(encoding="utf-8")
    types = [int(t) for t in args.types.split(",")]
    out_dir = args.out or DATA_DIR / "raw" / "nec" / args.sg_id

    if not args.skip_fetch:
        client = NecClient(require("DATA_GO_KR_SERVICE_KEY"))
        summary = fetch(client, args.sg_id, types, out_dir)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        expected = EXPECTED_WINNERS.get(args.sg_id, {})
        for t in types:
            got = summary["winners_by_type"][SG_TYPES[t]]
            if t in expected and got != expected[t]:
                log.warning("%s 당선인 수 %d ≠ 기대값 %d", SG_TYPES[t], got, expected[t])

    winners, pledges = build_rows(args.sg_id, out_dir)
    print(f"변환: 당선인 {len(winners)}명, 공약 {len(pledges)}건 → {out_dir}")

    if args.load:
        print("적재:", load(args.sg_id, out_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
