"""Von-backed intent router.

`VonRouter` uses the `von-sdk` package in-process to classify every inbound
message into one of the intents defined in `intents.json`. Von is a
non-autoregressive System One decision model: one forward pass, no token
generation, ~96 ms p50 on CPU.

The taxonomy is loaded from `intents.json` (repo root) at first use, so adding
an intent is a file edit, not a code change.

Requires the `von-sdk` package and model weights. Weight source, in order:
   1. `VON_CHECKPOINT_DIR` (explicit).
   2. The self-contained repo-local copy at `models/von/` (fully offline).
   3. The Hugging Face Hub cache (`HF_HOME`), downloading on first use.
Tests should use `FakeRouter` (PEPE_ROUTER=fake) so CI never downloads a model.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .intent import (
    IntentResult,
    RouterError,
    load_intents,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_checkpoint_dir() -> str | None:
    """Prefer the self-contained repo-local copy (models/von) so Von runs fully
    offline with no download. Falls back to the Hub cache otherwise."""
    local = _repo_root() / "models" / "von"
    if (local / "option_marker.pt").exists() and (local / "model.safetensors").exists():
        return str(local)
    return None


class VonRouter:
    """In-process Von router. The default production router."""

    name = "von"

    def __init__(
        self,
        intents_path: Path | None = None,
        confidence_threshold: float | None = None,
        model: str = "von-latest",
        checkpoint_dir: str | None = None,
    ) -> None:
        self._cfg = load_intents(intents_path)
        self._intents: dict[str, str] = self._cfg["intents"]
        self._instructions: str = self._cfg["instructions"]
        self._model = model
        # Set VON_CHECKPOINT_DIR so von-sdk loads the local copy when present.
        resolved = checkpoint_dir or os.environ.get("VON_CHECKPOINT_DIR") or default_checkpoint_dir()
        if resolved is not None and "VON_CHECKPOINT_DIR" not in os.environ:
            os.environ["VON_CHECKPOINT_DIR"] = resolved
        if confidence_threshold is not None:
            self.confidence_threshold = confidence_threshold
        else:
            self.confidence_threshold = float(
                os.environ.get("VON_CONFIDENCE", self._cfg.get("confidence_threshold", 0.80))
            )
        self._client = None  # lazy

    def _get_client(self):
        if self._client is None:
            try:
                import von  # noqa: F401
            except ImportError as e:
                raise RouterError(
                    "von-sdk is not installed. Run: pip install 'von-sdk>=1.3.7'"
                ) from e
            # Lazy import + lazy model load so importing this module is cheap.
            self._client = von
        return self._client

    def classify(self, message: str, context: dict | None = None) -> IntentResult:
        von = self._get_client()
        # Von's loader prints weight-load progress to stdout on first use; keep
        # stdout clean for CLI JSON output.
        import contextlib, io
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                answer = von.decide(
                    state={"message": message, "context": context or {}},
                    choices=self._intents,
                    instructions=self._instructions,
                    model=self._model,
                )
        except Exception as e:
            raise RouterError(f"von classify failed: {e}") from e

        probs = {k: float(v) for k, v in getattr(answer, "probabilities", {}).items()}
        top = answer.choice
        conf = float(getattr(answer, "confidence", 0.0) or 0.0)
        if conf < self.confidence_threshold:
            top = "unclear"
        return IntentResult(
            intent=top,
            confidence=conf,
            probabilities=probs,
            served_by=self.name,
        )
