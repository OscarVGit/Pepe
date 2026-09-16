"""Deal workspace operations: create the on-disk layout + DB; open existing."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ..state.connection import get_pepe_db, paths_for
from ..state.machine import AgentState, _read_current, save_state  # noqa: F401 (re-exported)
from .models import DealWorkspace, WORKSPACE_DIRS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create(deals_root: Path, deal_id: str, name: str | None = None) -> DealWorkspace:
    """Create the per-deal directory layout, init pepe.db, and insert the deal row."""
    root = deals_root / deal_id
    for d in WORKSPACE_DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(parents=True, exist_ok=True)
    (root / "state").mkdir(parents=True, exist_ok=True)

    conn, lock = get_pepe_db(deals_root, deal_id)
    with lock:
        now = _now()
        existing = conn.execute("SELECT id FROM deals WHERE id=?", (deal_id,)).fetchone()
        if existing is None:
            conn.execute(
                "INSERT INTO deals (id, name, root_path, current_status, created_at, updated_at) "
                "VALUES (?, ?, ?, 'new', ?, ?)",
                (deal_id, name or deal_id, str(root), now, now),
            )
            # Record the initial IDLE state transition for lineage.
            conn.execute(
                "INSERT INTO state_transitions (deal_id, from_state, to_state, reason, timestamp) "
                "VALUES (?, 'IDLE', 'IDLE', 'workspace created', ?)",
                (deal_id, now),
            )
            conn.commit()

    return open(deals_root, deal_id)


def open(deals_root: Path, deal_id: str) -> DealWorkspace:
    """Load a deal from pepe.db. Raises FileNotFoundError if missing."""
    p = paths_for(deals_root, deal_id)
    if not p.pepe_db.exists():
        raise FileNotFoundError(f"deal not found: {deal_id} (no pepe.db at {p.pepe_db})")
    conn, lock = get_pepe_db(deals_root, deal_id)
    with lock:
        row = conn.execute(
            "SELECT id, name, root_path, current_status FROM deals WHERE id=?",
            (deal_id,),
        ).fetchone()
        if row is None:
            raise FileNotFoundError(f"deal row missing for {deal_id}")
        state = _read_current(conn, deal_id)
    return DealWorkspace(
        deal_id=row[0],
        name=row[1],
        root=Path(row[2]),
        current_status=row[3],
        state=state,
    )


def snapshot(root: Path, label: str) -> Path:
    """Copy the models/ directory into outputs/snapshots/{label}_{ts}/.

    Phase 1: read-only models so this just records the snapshot manifest.
    """
    ts = _now().replace(":", "-")
    dest = root / "outputs" / "snapshots" / f"{label}_{ts}"
    dest.mkdir(parents=True, exist_ok=True)
    return dest
