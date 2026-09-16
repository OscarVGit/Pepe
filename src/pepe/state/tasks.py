"""litequeue wrapper. Provides claim-based persistent task semantics.

The queue (queue.db) is per-deal. Tasks are stored as JSON strings. litequeue
gives us atomic pop-with-claim, idempotent submit, and expired-claim retry.

Note: litequeue's public `peek()` does not bump the claim_id, so we use the
package's private `_pop_returning()` which is the canonical claim primitive.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import sqlite3
import threading

from .connection import get_queue, get_pepe_db, paths_for


@dataclass
class TaskRecord:
    id: int
    queue_message_id: str
    description: str
    status: str
    blocked_reason: str
    payload: dict
    claim_id: int
    created_at: str
    updated_at: str

    @property
    def is_active(self) -> bool:
        return self.status in {"pending", "active"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_deal_row(conn, deal_id: str) -> None:
    row = conn.execute("SELECT id FROM deals WHERE id=?", (deal_id,)).fetchone()
    if row is None:
        from .machine import _now as _n
        conn.execute(
            "INSERT INTO deals (id, name, root_path, current_status, created_at, updated_at) "
            "VALUES (?, ?, ?, 'new', ?, ?)",
            (deal_id, deal_id, "", _n(), _n()),
        )


def enqueue(deals_root: Path, deal_id: str, description: str, payload: dict | None = None,
            idempotency_key: str | None = None) -> tuple[str, int]:
    """Submit a task. Returns (queue_message_id, task_row_id)."""
    payload = payload or {}
    q = get_queue(deals_root, deal_id)
    data = json.dumps({"description": description, "payload": payload})
    msg = q.put(data, idempotency_key=idempotency_key)
    conn, lock = get_pepe_db(deals_root, deal_id)
    with lock:
        _ensure_deal_row(conn, deal_id)
        cur = conn.execute(
            "INSERT INTO tasks (deal_id, queue_message_id, description, status, "
            "blocked_reason, payload_json, created_at, updated_at) "
            "VALUES (?, ?, ?, 'pending', '', ?, ?, ?)",
            (deal_id, str(msg.message_id), description,
             json.dumps(payload), _now(), _now()),
        )
        row_id = int(cur.lastrowid)
        conn.commit()
    return str(msg.message_id), row_id


def claim_next(deals_root: Path, deal_id: str) -> Optional[TaskRecord]:
    """Atomically claim the next ready task. Bumps claim_id via litequeue."""
    q = get_queue(deals_root, deal_id)
    msg = q._pop_returning()
    if msg is None:
        return None
    # litequeue payload is our JSON string
    body = json.loads(msg.data) if isinstance(msg.data, str) else msg.data
    conn, lock = get_pepe_db(deals_root, deal_id)
    with lock:
        conn.execute(
            "UPDATE tasks SET status='active', claim_id=?, updated_at=? "
            "WHERE queue_message_id=? AND deal_id=?",
            (int(msg.claim_id), _now(), str(msg.message_id), deal_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, queue_message_id, description, status, blocked_reason, "
            "payload_json, claim_id, created_at, updated_at "
            "FROM tasks WHERE queue_message_id=? AND deal_id=?",
            (str(msg.message_id), deal_id),
        ).fetchone()
    if row is None:
        return None
    return TaskRecord(
        id=row[0], queue_message_id=row[1], description=row[2], status=row[3],
        blocked_reason=row[4], payload=json.loads(row[5] or "{}"),
        claim_id=row[6], created_at=row[7], updated_at=row[8],
    )


def complete(deals_root: Path, deal_id: str, queue_message_id: str, claim_id: int) -> bool:
    q = get_queue(deals_root, deal_id)
    ok = q.done(queue_message_id, claim_id=claim_id)
    conn, lock = get_pepe_db(deals_root, deal_id)
    with lock:
        conn.execute(
            "UPDATE tasks SET status='done', claim_id=NULL, updated_at=? "
            "WHERE queue_message_id=? AND deal_id=?",
            (_now(), queue_message_id, deal_id),
        )
        conn.commit()
    return ok


def block(deals_root: Path, deal_id: str, queue_message_id: str, claim_id: int, reason: str) -> bool:
    """Mark a claimed task as blocked. Litequeue message goes to FAILED state
    so retry_expired does not re-dispatch it automatically."""
    q = get_queue(deals_root, deal_id)
    failed = q.mark_failed(queue_message_id, claim_id=claim_id)
    conn, lock = get_pepe_db(deals_root, deal_id)
    with lock:
        conn.execute(
            "UPDATE tasks SET status='blocked', blocked_reason=?, claim_id=NULL, updated_at=? "
            "WHERE queue_message_id=? AND deal_id=?",
            (reason, _now(), queue_message_id, deal_id),
        )
        conn.commit()
    return failed


def unblock(deals_root: Path, deal_id: str, queue_message_id: str) -> bool:
    """Re-enqueue a blocked task. litequeue has no unblock primitive; we put
    a new message and update the row to point at it."""
    conn, lock = get_pepe_db(deals_root, deal_id)
    with lock:
        row = conn.execute(
            "SELECT description, payload_json FROM tasks "
            "WHERE queue_message_id=? AND deal_id=?",
            (queue_message_id, deal_id),
        ).fetchone()
        if row is None:
            return False
        description, payload_json = row
    # Re-enqueue using the original idempotency_key (the message_id) so retries are safe.
    new_msg_id, _ = enqueue(deals_root, deal_id, description, json.loads(payload_json or "{}"),
                            idempotency_key=queue_message_id)
    with lock:
        conn.execute(
            "UPDATE tasks SET status='pending', blocked_reason='', queue_message_id=?, "
            "claim_id=NULL, updated_at=? WHERE id=(SELECT id FROM tasks "
            "WHERE queue_message_id=? AND deal_id=? LIMIT 1)",
            (new_msg_id, _now(), queue_message_id, deal_id),
        )
        # Remove the old row (same description, just a new queue handle)
        conn.execute(
            "DELETE FROM tasks WHERE queue_message_id=? AND deal_id=? AND status='blocked'",
            (queue_message_id, deal_id),
        )
        conn.commit()
    return True


def retry_expired(deals_root: Path, deal_id: str, threshold_seconds: int = 300) -> int:
    """Recover tasks whose claim has expired (e.g. crashed worker)."""
    q = get_queue(deals_root, deal_id)
    return q.retry_expired(threshold_seconds=threshold_seconds)


def list_active(deals_root: Path, deal_id: str) -> list[TaskRecord]:
    conn, lock = get_pepe_db(deals_root, deal_id)
    with lock:
        rows = conn.execute(
            "SELECT id, queue_message_id, description, status, blocked_reason, "
            "payload_json, claim_id, created_at, updated_at "
            "FROM tasks WHERE deal_id=? AND status IN ('pending','active','blocked') "
            "ORDER BY id ASC",
            (deal_id,),
        ).fetchall()
    return [
        TaskRecord(
            id=r[0], queue_message_id=r[1], description=r[2], status=r[3],
            blocked_reason=r[4], payload=json.loads(r[5] or "{}"),
            claim_id=r[6] or 0, created_at=r[7], updated_at=r[8],
        )
        for r in rows
    ]
