"""Memory architecture: five separate concepts. See docs/MEMORY.md."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ConversationMemory:
    recent_turns: list[dict] = field(default_factory=list)


@dataclass
class DealMemory:
    facts: dict[str, str] = field(default_factory=dict)  # e.g. entry_multiple=8.5x


@dataclass
class InstitutionalMemory:
    conventions: dict[str, str] = field(default_factory=dict)


@dataclass
class WorkingState:
    current_task: str = ""
    outstanding: list[str] = field(default_factory=list)


@dataclass
class AuditEntry:
    timestamp: str
    agent: str
    deal: str
    task: str
    action: str


class MemoryStore(Protocol):
    def load_conversation(self, deal_id: str) -> ConversationMemory: ...
    def load_deal(self, deal_id: str) -> DealMemory: ...
    def save_deal_fact(self, deal_id: str, key: str, value: str, source: str) -> None: ...
