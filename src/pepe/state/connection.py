"""Per-deal connection management.

`deals/{deal_id}/pepe.db` — state, transitions, tasks, audit, facts.
`deals/{deal_id}/queue.db` — owned by litequeue.
"""
from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path

from litequeue import LiteQueue

from .schema import init as init_pepe_schema

# In-process locks keyed by deal_id. SQLite + threads is safe with a per-conn lock.
_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


def _lock_for(deal_id: str) -> threading.Lock:
    with _LOCKS_GUARD:
        lock = _LOCKS.get(deal_id)
        if lock is None:
            lock = threading.Lock()
            _LOCKS[deal_id] = lock
        return lock


def _deal_root(deals_root: Path, deal_id: str) -> Path:
    return deals_root / deal_id


@dataclass
class DealPaths:
    root: Path
    pepe_db: Path
    queue_db: Path
    workspace: Path
    audit_jsonl: Path


def paths_for(deals_root: Path, deal_id: str) -> DealPaths:
    root = _deal_root(deals_root, deal_id)
    state_dir = root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return DealPaths(
        root=root,
        pepe_db=state_dir / "pepe.db",
        queue_db=state_dir / "queue.db",
        workspace=root,
        audit_jsonl=root / "logs" / "audit.jsonl",
    )


def get_pepe_db(deals_root: Path, deal_id: str) -> tuple[sqlite3.Connection, threading.Lock]:
    """Return (connection, lock) for pepe.db. Ensures schema is applied."""
    p = paths_for(deals_root, deal_id)
    lock = _lock_for(deal_id)
    conn = sqlite3.connect(
        str(p.pepe_db),
        check_same_thread=False,
        isolation_level=None,  # autocommit; we use explicit BEGIN
    )
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    init_pepe_schema(conn)
    return conn, lock


def get_queue(deals_root: Path, deal_id: str) -> LiteQueue:
    """Return a litequeue instance for queue.db. Creates file on first use."""
    p = paths_for(deals_root, deal_id)
    return LiteQueue(filename=str(p.queue_db))
