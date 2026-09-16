"""Generate a human-readable markdown status view from pepe.db.

This is a *view*, not the source of truth. Runtime never reads STATUS.md.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ..state.connection import get_pepe_db, paths_for
from ..state.tasks import list_active
from ..audit.record import recent
from ..workspace.models import DealWorkspace


def generate_status_md(workspace: DealWorkspace) -> Path:
    conn, lock = get_pepe_db(workspace.root.parent, workspace.deal_id)
    with lock:
        facts_rows = conn.execute(
            "SELECT key, value, source, timestamp FROM facts "
            "WHERE deal_id=? ORDER BY id ASC LIMIT 50",
            (workspace.deal_id,),
        ).fetchall()

    active = list_active(workspace.root.parent, workspace.deal_id)
    audit = recent(workspace.root.parent, workspace.deal_id, limit=10)

    lines: list[str] = []
    lines.append(f"# {workspace.name} — Status")
    lines.append("")
    lines.append(f"_Generated: {datetime.now(timezone.utc).isoformat()}_")
    lines.append("")
    lines.append(f"**State:** `{workspace.state.value}`")
    lines.append(f"**Current status:** {workspace.current_status}")
    lines.append(f"**Workspace:** `{workspace.root}`")
    lines.append("")

    if active:
        lines.append("## Active tasks")
        for t in active:
            marker = {"pending": "[ ]", "active": "[>]", "blocked": "[!]"}.get(t.status, "[?]")
            extra = f" — blocked: {t.blocked_reason}" if t.blocked_reason else ""
            lines.append(f"- {marker} **{t.description}** ({t.status}){extra}")
        lines.append("")
    else:
        lines.append("## Active tasks")
        lines.append("- (none)")
        lines.append("")

    if audit:
        lines.append("## Recent activity")
        for entry in audit:
            ts = entry["timestamp"]
            details = json.dumps(entry["details"], sort_keys=True)
            lines.append(f"- `{ts}` **{entry['action']}** — {details}")
        lines.append("")

    if facts_rows:
        lines.append("## Deal facts")
        for k, v, src, ts in facts_rows:
            src_part = f" (source: {src})" if src else ""
            lines.append(f"- **{k}**: {v}{src_part}")
        lines.append("")

    target = workspace.root / "STATUS.md"
    target.write_text("\n".join(lines) + "\n")
    return target
