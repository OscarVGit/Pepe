"""Von router talking to a sidecar `von serve` endpoint (HTTP /v1/systemone).

Used for multi-process deployments (Phase 2 messaging gateway, multiple Pepe
processes) where weights are loaded once by the server and shared.

Requires `httpx`. The sidecar runs `von serve` and exposes the TypeSafe
`/v1/systemone` wire protocol.
"""
from __future__ import annotations

import os
from typing import Any

from .intent import IntentResult, RouterError, load_intents


class VonHttpRouter:
    """HTTP client router for a `von serve` sidecar."""

    name = "von-http"

    def __init__(
        self,
        base_url: str | None = None,
        confidence_threshold: float | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = (base_url or os.environ.get("VON_BASE_URL", "http://127.0.0.1:8000")).rstrip("/")
        self._cfg = load_intents()
        self._intents: dict[str, str] = self._cfg["intents"]
        self._instructions: str = self._cfg["instructions"]
        self.confidence_threshold = float(
            confidence_threshold
            if confidence_threshold is not None
            else os.environ.get("VON_CONFIDENCE", self._cfg.get("confidence_threshold", 0.80))
        )
        self.timeout = timeout

    def classify(self, message: str, context: dict | None = None) -> IntentResult:
        try:
            import httpx
        except ImportError as e:
            raise RouterError("httpx is not installed") from e

        payload = {
            "state": {"message": message, "context": context or {}},
            "questions": {
                "intent": {
                    "type": "choice",
                    "instructions": self._instructions,
                    "criteria": self._intents,
                }
            },
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.post(f"{self.base_url}/v1/systemone", json=payload)
                r.raise_for_status()
                data = r.json()
        except Exception as e:
            raise RouterError(f"von-http classify failed: {e}") from e

        ans = (data.get("answers") or {}).get("intent", {})
        probs = {k: float(v) for k, v in (ans.get("probabilities") or {}).items()}
        top = ans.get("choice", "unclear")
        conf = float(ans.get("confidence", 0.0) or 0.0)
        if conf < self.confidence_threshold:
            top = "unclear"
        return IntentResult(
            intent=top,
            confidence=conf,
            probabilities=probs,
            served_by=self.name,
        )
