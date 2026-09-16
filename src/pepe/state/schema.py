"""SQLite schema for per-deal pepe.db."""
from __future__ import annotations

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS deals (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        root_path TEXT NOT NULL,
        current_status TEXT NOT NULL DEFAULT 'new',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS state_transitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deal_id TEXT NOT NULL,
        from_state TEXT NOT NULL,
        to_state TEXT NOT NULL,
        reason TEXT NOT NULL DEFAULT '',
        timestamp TEXT NOT NULL,
        FOREIGN KEY (deal_id) REFERENCES deals(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deal_id TEXT NOT NULL,
        queue_message_id TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT NOT NULL,
        blocked_reason TEXT NOT NULL DEFAULT '',
        payload_json TEXT NOT NULL DEFAULT '{}',
        claim_id INTEGER,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (deal_id) REFERENCES deals(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deal_id TEXT NOT NULL,
        action TEXT NOT NULL,
        details_json TEXT NOT NULL DEFAULT '{}',
        timestamp TEXT NOT NULL,
        FOREIGN KEY (deal_id) REFERENCES deals(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS facts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deal_id TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        source TEXT NOT NULL DEFAULT '',
        timestamp TEXT NOT NULL,
        FOREIGN KEY (deal_id) REFERENCES deals(id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_state_deal ON state_transitions(deal_id, timestamp DESC)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_deal ON tasks(deal_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_audit_deal ON audit_log(deal_id, timestamp DESC)",
    "CREATE INDEX IF NOT EXISTS idx_facts_deal ON facts(deal_id)",
]


def init(conn) -> None:
    """Apply schema to an open pepe.db connection."""
    cur = conn.cursor()
    for stmt in SCHEMA:
        cur.execute(stmt)
    conn.commit()
