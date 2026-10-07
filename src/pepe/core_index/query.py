"""Cross-deal query helpers (read-aggregated from the firm index)."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .connection import get_firm_db


def list_deals(repo_root: Path) -> list[dict[str, Any]]:
    firm = get_firm_db(repo_root)
    firm.row_factory = sqlite3.Row
    rows = firm.execute(
        "SELECT id, name, current_state, current_status, last_activity, owner "
        "FROM deal_registry ORDER BY last_activity DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def list_active_deals(repo_root: Path) -> list[dict[str, Any]]:
    firm = get_firm_db(repo_root)
    firm.row_factory = sqlite3.Row
    rows = firm.execute(
        "SELECT id, name, current_state, current_status, last_activity "
        "FROM deal_registry WHERE current_state NOT IN ('COMPLETE','IDLE') "
        "ORDER BY last_activity DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def pipeline_summary(repo_root: Path) -> dict[str, Any]:
    firm = get_firm_db(repo_root)
    total = firm.execute("SELECT COUNT(*) FROM deal_registry").fetchone()[0]
    active = firm.execute(
        "SELECT COUNT(*) FROM deal_registry WHERE current_state NOT IN ('COMPLETE','IDLE')"
    ).fetchone()[0]
    blocked = firm.execute(
        "SELECT COUNT(*) FROM global_tasks WHERE status='blocked'"
    ).fetchone()[0]
    pending = firm.execute(
        "SELECT COUNT(*) FROM global_tasks WHERE status='pending'"
    ).fetchone()[0]
    return {
        "total_deals": int(total),
        "active": int(active),
        "blocked_tasks": int(blocked),
        "pending_tasks": int(pending),
    }


def global_search(repo_root: Path, query: str) -> dict[str, list[dict[str, Any]]]:
    firm = get_firm_db(repo_root)
    firm.row_factory = sqlite3.Row
    q = f"%{query}%"
    deals = firm.execute(
        "SELECT id, name, current_state FROM deal_registry WHERE name LIKE ? OR id LIKE ?",
        (q, q),
    ).fetchall()
    tasks = firm.execute(
        "SELECT description, related_deal_id, status FROM global_tasks WHERE description LIKE ?",
        (q,),
    ).fetchall()
    return {"deals": [dict(r) for r in deals], "tasks": [dict(r) for r in tasks]}
