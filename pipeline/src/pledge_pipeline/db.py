"""Supabase(PostgreSQL) 적재. 파이프라인은 DATABASE_URL(service 권한)로 직접 쓴다."""

from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from contextlib import contextmanager

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.types.json import Jsonb

from .settings import require


def conninfo(url: str) -> str:
    """URL과 PGSSLMODE 어디에도 sslmode가 없을 때만 기본값을 채운다.

    libpq 기본값 prefer는 평문 강등을 허용하므로 require, sslrootcert가 있으면 verify-full.
    더 엄격한 설정(PGSSLMODE=verify-full 등)을 덮어쓰지 않는다.
    """
    params = conninfo_to_dict(url)
    if "sslmode" not in params and not os.environ.get("PGSSLMODE"):
        params["sslmode"] = "verify-full" if "sslrootcert" in params else "require"
    return make_conninfo("", **params)


@contextmanager
def connect():
    # prepare_threshold=None: 트랜잭션 풀러(6543)는 prepared statement를 지원하지 않는다
    url = conninfo(require("DATABASE_URL"))
    with psycopg.connect(url, autocommit=False, prepare_threshold=None) as conn:
        yield conn


def upsert(
    conn: psycopg.Connection,
    table: str,
    rows: Iterable[dict],
    conflict: Sequence[str],
) -> int:
    """rows를 table에 upsert한다. dict 값은 jsonb로 저장한다. 반환: 처리 행 수."""
    rows = list(rows)
    if not rows:
        return 0
    cols = list(rows[0].keys())
    updates = [c for c in cols if c not in conflict]
    query = sql.SQL(
        "insert into {table} ({cols}) values ({vals}) on conflict ({conflict}) do update set {set}"
    ).format(
        table=sql.Identifier(table),
        cols=sql.SQL(", ").join(map(sql.Identifier, cols)),
        vals=sql.SQL(", ").join(sql.Placeholder() * len(cols)),
        conflict=sql.SQL(", ").join(map(sql.Identifier, conflict)),
        set=sql.SQL(", ").join(
            sql.SQL("{c} = excluded.{c}").format(c=sql.Identifier(c)) for c in updates
        ),
    )
    params = [[Jsonb(r[c]) if isinstance(r[c], dict | list) else r[c] for c in cols] for r in rows]
    with conn.cursor() as cur:
        cur.executemany(query, params)
    return len(rows)


def find_stale(
    conn: psycopg.Connection,
    table: str,
    id_col: str,
    scope_col: str,
    scope_ids: Iterable[str],
    keep_ids: Iterable[str],
) -> list[str]:
    """scope 안에서 이번 적재에 없는 행의 id. 삭제하지 않는다.

    pledges를 지우면 matches·judgments가 cascade로 사라져 판정 이력 공개 원칙이 깨지므로,
    원천에서 사라진 행은 사람이 확인하도록 목록만 돌려준다.
    """
    query = sql.SQL("select {i} from {t} where {s} = any(%s) and not ({i} = any(%s))").format(
        i=sql.Identifier(id_col), t=sql.Identifier(table), s=sql.Identifier(scope_col)
    )
    with conn.cursor() as cur:
        cur.execute(query, [list(scope_ids), list(keep_ids)])
        return [r[0] for r in cur.fetchall()]
