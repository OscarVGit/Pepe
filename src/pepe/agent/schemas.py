"""Structured shapes for the inner loop."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    tool: str
    params: dict[str, Any] = Field(default_factory=dict)


class Step(BaseModel):
    index: int
    router: dict[str, Any] | None = None     # served_by, top3, confidence
    action: str                              # classify | tool | ask | complete | blocked | reason
    tool: str | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    note: str = ""


class TaskOutcome(BaseModel):
    kind: str  # complete | blocked | needs_approval | failed | waiting
    reason: str = ""
    result: dict[str, Any] = Field(default_factory=dict)
    steps: list[Step] = Field(default_factory=list)
    run_id: str = ""


class Task(BaseModel):
    description: str
    payload: dict[str, Any] = Field(default_factory=dict)
    queue_message_id: str = ""
    claim_id: int = 0
