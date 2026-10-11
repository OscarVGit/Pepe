"""Concrete memory store backed by per-deal pepe.db.

Deterministic tool outputs only. Overwrites are audited with old→new. Facts
are listed in insertion order (id ASC) — the "what we know" order.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..state.connection import get_pepe_db
from ..state.machine import _now as _state_now
from .allowlist import allowed_key, fact_source_tool


def _ensure_deal_row(conn, deal_id: str) -> None:
    row = conn.execute("SELECT id FROM deals WHERE id=?", (deal_id,)).fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO deals (id, name, root_path, current_status, created_at, updated_at) "
            "VALUES (?, ?, ?, 'new', ?, ?)",
            (deal_id, deal_id, "", _state_now(), _state_now()),
        )


@dataclass
class Fact:
    key: str
    value: str
    source: str
    timestamp: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_facts(deals_root: Path, deal_id: str) -> list[Fact]:
    """Facts in insertion order (earliest-written first)."""
    conn, lock = get_pepe_db(deals_root, deal_id)
    with lock:
        rows = conn.execute(
            "SELECT key, value, source, timestamp FROM facts "
            "WHERE deal_id=? ORDER BY id ASC",
            (deal_id,),
        ).fetchall()
    return [Fact(key=r[0], value=r[1], source=r[2], timestamp=r[3]) for r in rows]


def get_fact(deals_root: Path, deal_id: str, key: str) -> Optional[Fact]:
    for f in list_facts(deals_root, deal_id):
        if f.key == key:
            return f
    return None


def save_fact(
    deals_root: Path,
    deal_id: str,
    key: str,
    value: str,
    source: str,
) -> tuple[bool, Optional[Fact]]:
    """Overwrite a fact if it exists, else insert. Audit the change.

    Returns (written, previous). written=False for disallowed keys or
    malformed input.
    """
    if not key or not allowed_key(key):
        return False, None

    conn, lock = get_pepe_db(deals_root, deal_id)
    with lock:
        _ensure_deal_row(conn, deal_id)
        existing = conn.execute(
            "SELECT value, source, timestamp FROM facts "
            "WHERE deal_id=? AND key=? ORDER BY id DESC LIMIT 1",
            (deal_id, key),
        ).fetchone()
        prev: Optional[Fact] = (
            Fact(key=key, value=existing[0], source=existing[1], timestamp=existing[2])
            if existing else None
        )
        ts = _now()
        if existing:
            conn.execute(
                "UPDATE facts SET value=?, source=?, timestamp=? WHERE id=("
                " SELECT id FROM facts WHERE deal_id=? AND key=? ORDER BY id DESC LIMIT 1)",
                (str(value), source, ts, deal_id, key),
            )
        else:
            conn.execute(
                "INSERT INTO facts (deal_id, key, value, source, timestamp) VALUES (?,?,?,?,?)",
                (deal_id, key, str(value), source, ts),
            )
        conn.commit()
    return True, prev
