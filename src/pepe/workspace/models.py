"""Pydantic models for the deal workspace. These cross the Python/SQL boundary
as the structured shape of a deal."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from ..state.machine import AgentState


WORKSPACE_DIRS = (
    "documents", "models", "research", "presentations", "outputs",
    "assumptions", "memory", "tasks", "sources", "approvals", "logs", "state",
)


class DealWorkspace(BaseModel):
    """The fundamental unit of Pepe. One workspace per deal."""

    deal_id: str
    name: str
    root: Path
    current_status: str = "new"
    state: AgentState = AgentState.IDLE
    completed: list[str] = Field(default_factory=list)
    waiting_for: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    pending_approval: list[str] = Field(default_factory=list)

    @property
    def state_db(self) -> Path:
        return self.root / "state" / "pepe.db"

    @property
    def queue_db(self) -> Path:
        return self.root / "state" / "queue.db"

    @property
    def audit_jsonl(self) -> Path:
        return self.root / "logs" / "audit.jsonl"
