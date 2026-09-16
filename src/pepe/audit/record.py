"""Audit log. Append to pepe.db.audit_log AND a human-readable JSONL mirror
under deals/{deal_id}/logs/audit.jsonl."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..state.connection import get_pepe_db, paths_for


@dataclass
class AuditRecord:
    timestamp: str
    deal_id: str
    action: str
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def now(cls, deal_id: str, action: str, **details: Any) -> "AuditRecord":
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            deal_id=deal_id,
            action=action,
            details=details,
        )


def record(deals_root: Path, audit: AuditRecord) -> None:
    """Persist to pepe.db.audit_log and append the JSONL mirror."""
    p = paths_for(deals_root, audit.deal_id)
    p.audit_jsonl.parent.mkdir(parents=True, exist_ok=True)
    conn, lock = get_pepe_db(deals_root, audit.deal_id)
    payload = json.dumps(audit.details, sort_keys=True)
    with lock:
        conn.execute(
            "INSERT INTO audit_log (deal_id, action, details_json, timestamp) "
            "VALUES (?, ?, ?, ?)",
            (audit.deal_id, audit.action, payload, audit.timestamp),
        )
        conn.commit()
    with p.audit_jsonl.open("a") as f:
        f.write(json.dumps(asdict(audit)) + "\n")


def recent(deals_root: Path, deal_id: str, limit: int = 10) -> list[dict]:
    """Return the last N audit entries for a deal, newest first."""
    conn, lock = get_pepe_db(deals_root, deal_id)
    with lock:
        rows = conn.execute(
            "SELECT action, details_json, timestamp FROM audit_log "
            "WHERE deal_id=? ORDER BY timestamp DESC, id DESC LIMIT ?",
            (deal_id, limit),
        ).fetchall()
    return [
        {"action": r[0], "details": json.loads(r[1]), "timestamp": r[2]}
        for r in rows
    ]
