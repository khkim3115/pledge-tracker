"""Supabase(PostgreSQL) 적재. 파이프라인은 DATABASE_URL(service 권한)로 직접 쓴다."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from contextlib import contextmanager

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from .settings import require


@contextmanager
def connect():
    with psycopg.connect(require("DATABASE_URL"), autocommit=False) as conn:
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
