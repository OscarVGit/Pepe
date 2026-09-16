"""Explicit agent state machine. Persists to pepe.db.

The state machine survives process restarts via SQLite. LLM context is never
authoritative for state.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class AgentState(str, Enum):
    IDLE = "IDLE"
    UNDERSTANDING = "UNDERSTANDING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    WAITING_FOR_INFORMATION = "WAITING_FOR_INFORMATION"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    VALIDATING = "VALIDATING"
    BLOCKED = "BLOCKED"
    SCHEDULED = "SCHEDULED"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


TRANSITIONS: dict[AgentState, set[AgentState]] = {
    AgentState.IDLE: {AgentState.UNDERSTANDING, AgentState.SCHEDULED},
    AgentState.UNDERSTANDING: {AgentState.PLANNING, AgentState.WAITING_FOR_INFORMATION, AgentState.FAILED},
    AgentState.PLANNING: {AgentState.EXECUTING, AgentState.WAITING_FOR_APPROVAL, AgentState.BLOCKED, AgentState.FAILED},
    AgentState.EXECUTING: {
        AgentState.VALIDATING,
        AgentState.WAITING_FOR_INFORMATION,
        AgentState.WAITING_FOR_APPROVAL,
        AgentState.BLOCKED,
        AgentState.FAILED,
    },
    AgentState.WAITING_FOR_INFORMATION: {AgentState.EXECUTING, AgentState.BLOCKED},
    AgentState.WAITING_FOR_APPROVAL: {AgentState.EXECUTING, AgentState.BLOCKED},
    AgentState.VALIDATING: {AgentState.COMPLETE, AgentState.EXECUTING, AgentState.FAILED},
    AgentState.BLOCKED: {AgentState.EXECUTING, AgentState.FAILED},
    AgentState.SCHEDULED: {AgentState.UNDERSTANDING, AgentState.IDLE},
    AgentState.COMPLETE: {AgentState.IDLE},
    AgentState.FAILED: {AgentState.IDLE},
}


def can_transition(frm: AgentState, to: AgentState) -> bool:
    return to in TRANSITIONS.get(frm, set())


class InvalidTransitionError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_current(conn: sqlite3.Connection, deal_id: str) -> AgentState:
    row = conn.execute(
        "SELECT to_state FROM state_transitions "
        "WHERE deal_id = ? ORDER BY timestamp DESC, id DESC LIMIT 1",
        (deal_id,),
    ).fetchone()
    return AgentState(row[0]) if row else AgentState.IDLE


def load_state(
    conn: sqlite3.Connection,
    lock,
    deal_id: str,
    default: AgentState = AgentState.IDLE,
) -> AgentState:
    """Read the latest persisted state for a deal."""
    del default  # IDLE is the implicit default; signature preserved for tests.
    with lock:
        return _read_current(conn, deal_id)


def save_state(
    conn: sqlite3.Connection,
    lock,
    deal_id: str,
    to_state: AgentState,
    reason: str = "",
    expected_from: Optional[AgentState] = None,
) -> AgentState:
    """Persist a state transition atomically. Validates against the current state."""
    with lock:
        current = _read_current(conn, deal_id)
        if expected_from is not None and current is not expected_from:
            raise InvalidTransitionError(
                f"expected {expected_from}, found {current} for deal {deal_id}"
            )
        if not can_transition(current, to_state):
            raise InvalidTransitionError(
                f"cannot transition {current} -> {to_state} for deal {deal_id}"
            )
        try:
            conn.execute("BEGIN")
            conn.execute(
                "INSERT INTO state_transitions "
                "(deal_id, from_state, to_state, reason, timestamp) "
                "VALUES (?, ?, ?, ?, ?)",
                (deal_id, current.value, to_state.value, reason, _now()),
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    return to_state
