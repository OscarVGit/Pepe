"""Intent router interface + deterministic test double.

Von is the universal System 1 intent router (ADR-0009). Every inbound message
is classified before any tool runs. This module defines the `IntentRouter`
Protocol, the `IntentResult` shape, and `FakeRouter` (a deterministic,
dependency-free router used in tests and CI so the model is never downloaded).

The taxonomy lives in `intents.json` at the repo root so intents are
versionable and greppable, and can be loaded into a database later.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


def _repo_root() -> Path:
    # src/pepe/routing/intent.py -> repo root is three parents up
    return Path(__file__).resolve().parents[3]


def intents_path() -> Path:
    override = os.environ.get("PEPE_INTENTS_PATH")
    return Path(override) if override else _repo_root() / "intents.json"


def load_intents(path: Path | None = None) -> dict[str, Any]:
    p = path or intents_path()
    with p.open() as f:
        return json.load(f)


@dataclass
class IntentResult:
    intent: str
    confidence: float
    probabilities: dict[str, float] = field(default_factory=dict)
    served_by: str = "fake"
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


@runtime_checkable
class IntentRouter(Protocol):
    """The System 1 intent router. Implementations classify a message into an
    intent label from the taxonomy, with a calibrated confidence."""

    name: str

    def classify(self, message: str, context: dict | None = None) -> IntentResult:
        ...


class RouterError(RuntimeError):
    pass


class FakeRouter:
    """Deterministic router for tests and offline development.

    Keyword/regex-backed: it never calls a model and never needs `von-sdk`.
    Useful for CI and for verifying the loop's dispatch without Von weights.
    """

    name = "fake"

    def __init__(self, intents: dict[str, str] | None = None) -> None:
        self.intents = intents or load_intents()["intents"]

    def classify(self, message: str, context: dict | None = None) -> IntentResult:
        text = message.lower()
        intent = self._match(text)
        probs = {k: 0.0 for k in self.intents}
        probs[intent] = 0.99
        return IntentResult(intent=intent, confidence=0.99, probabilities=probs,
                            served_by=self.name)

    def _match(self, text: str) -> str:
        rules: list[tuple[str, str]] = [
            ("wait_for_info", r"\b(wait|hold|pause)\b"),
            ("compute_finance", r"\b(irr|moic|cagr|npv|returns?|sensitivit)\b"),
            # list_deals must precede inspect_file (which also matches "list").
            ("list_deals", r"\b(list|show)\b.*\bdeal|\b(what|which)\b.*\bdeal|\bpipeline\b"),
            ("new_deal", r"\b(new deal|create deal|start (a )?deal|kick off)\b"),
            ("approval_response", r"^\s*(yes|no|go ahead|approve|reject|stop)\b"),
            ("inspect_file", r"\.(xlsx|pdf)\b|\b(inspect|list|show|read)\b"),
            ("long_horizon_task", r"\b(multi[- ]step|end[- ]to[- ]end|deep dive|workstream)\b"),
            ("research", r"\b(research|diligence|comps|market|c im|term sheet)\b"),
            ("run_analysis", r"\b(lbo|dcf|scenario|downside|upside|model)\b"),
            ("status_query", r"\b(status|what changed|next action|progress|update me)\b"),
            ("question", r"\b(why|explain|what is|how|what does)\b"),
        ]
        for label, pattern in rules:
            if re.search(pattern, text, re.IGNORECASE):
                return label if label in self.intents else "unclear"
        return "unclear"
