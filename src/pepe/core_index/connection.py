"""Connection manager for the firm-level pepe.db at repo root."""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from .schema import init as init_schema

# One lock per firm DB. There is exactly one firm DB per repo, so a module-level
# lock is sufficient for Phase 1. If multi-process access is ever needed, a
# separate lock per repo_root would be required.
_LOCK = threading.Lock()


def get_firm_db(repo_root: Path) -> sqlite3.Connection:
    """Return a connection to repo_root/pepe.db. Schema is applied on first call."""
    db_path = repo_root / "pepe.db"
    conn = sqlite3.connect(
        str(db_path),
        check_same_thread=False,
        isolation_level=None,  # autocommit; we use explicit BEGIN
    )
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    init_schema(conn)
    return conn


def get_lock() -> threading.Lock:
    """The single firm-level write lock. Returned so callers can serialise."""
    return _LOCK
