"""Auto-sync: scan deals/*/state/pepe.db and upsert to firm-level pepe.db.

Phase 1 behaviour:
  - sync_deal(repo_root, deal_id): reads one per-deal DB and upserts to the index.
  - sync_all(repo_root): scans all deals and syncs each.
  - Called after every CLI mutation (ask, resume, create) to keep the index fresh.
"""
from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from .connection import get_firm_db, get_lock


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sync_deal(repo_root: Path, deal_id: str) -> bool:
    """Sync one deal into the firm index. Returns True if a row was written."""
    deal_db = repo_root / "deals" / deal_id / "state" / "pepe.db"
    if not deal_db.exists():
        return False

    src = sqlite3.connect(str(deal_db), check_same_thread=False)
    src.row_factory = sqlite3.Row
    try:
        row = src.execute(
            "SELECT id, name, root_path, current_status, created_at FROM deals WHERE id=?",
            (deal_id,),
        ).fetchone()
        if row is None:
            return False
        state_row = src.execute(
            "SELECT to_state FROM state_transitions "
            "WHERE deal_id=? ORDER BY timestamp DESC, id DESC LIMIT 1",
            (deal_id,),
        ).fetchone()
        current_state = state_row["to_state"] if state_row else "IDLE"
        tasks = src.execute(
            "SELECT description, status, blocked_reason FROM tasks "
            "WHERE deal_id=? AND status IN ('pending','active','blocked')",
            (deal_id,),
        ).fetchall()
        last_activity = src.execute(
            "SELECT timestamp FROM audit_log WHERE deal_id=? "
            "ORDER BY timestamp DESC, id DESC LIMIT 1",
            (deal_id,),
        ).fetchone()
        last_activity_ts = last_activity["timestamp"] if last_activity else row["created_at"]
    finally:
        src.close()

    firm = get_firm_db(repo_root)
    lock = get_lock()
    now = _now()
    with lock:
        firm.execute("BEGIN")
        try:
            firm.execute(
                "INSERT INTO deal_registry "
                "(id, name, current_state, current_status, last_activity, root_path, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "name=excluded.name, current_state=excluded.current_state, "
                "current_status=excluded.current_status, last_activity=excluded.last_activity, "
                "root_path=excluded.root_path, updated_at=excluded.updated_at",
                (deal_id, row["name"], current_state, row["current_status"],
                 last_activity_ts, row["root_path"], row["created_at"], now),
            )
            firm.execute("DELETE FROM global_tasks WHERE related_deal_id=?", (deal_id,))
            for t in tasks:
                firm.execute(
                    "INSERT INTO global_tasks "
                    "(description, related_deal_id, status, blocked_reason, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (t["description"], deal_id, t["status"], t["blocked_reason"], now),
                )
            firm.execute("COMMIT")
        except Exception:
            firm.execute("ROLLBACK")
            raise
    return True


def sync_all(repo_root: Path) -> int:
    """Scan all deals under deals/ and sync each. Returns count synced."""
    deals_dir = repo_root / "deals"
    if not deals_dir.exists():
        return 0
    n = 0
    for d in sorted(deals_dir.iterdir()):
        if d.is_dir() and (d / "state" / "pepe.db").exists():
            if sync_deal(repo_root, d.name):
                n += 1
    return n
