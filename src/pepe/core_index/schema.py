"""DDL for the firm-level Pepe Core Index.

`pepe.db` lives at the repo root. It is a read-aggregated mirror of per-deal
state, never authoritative. Per-deal pepe.db remains sovereign.
"""
from __future__ import annotations

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS deal_registry (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        current_state TEXT NOT NULL,
        current_status TEXT NOT NULL,
        last_activity TEXT NOT NULL,
        root_path TEXT NOT NULL,
        owner TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS global_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        related_deal_id TEXT NOT NULL,
        status TEXT NOT NULL,
        blocked_reason TEXT NOT NULL DEFAULT '',
        due_at TEXT,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_prefs (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS institutional_knowledge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        source TEXT,
        updated_at TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_registry_state ON deal_registry(current_state)",
    "CREATE INDEX IF NOT EXISTS idx_global_tasks_deal ON global_tasks(related_deal_id, status)",
]


def init(conn) -> None:
    """Apply schema to an open firm-level pepe.db connection."""
    cur = conn.cursor()
    for stmt in SCHEMA:
        cur.execute(stmt)
    conn.commit()
