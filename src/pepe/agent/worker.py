"""Worker Protocol — pluggable task executors.

Phase 1 default: `CustomWorker` (hand-rolled bounded ReAct loop).
Phase 3: `DeepAgentWorker` (cloud-only research worker, optional).

The Worker Protocol keeps the inner loop swappable per task type. Workers
must never mutate deal state directly — they return structured outcomes
that the orchestrator applies to pepe.db.
"""
from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable

from .inner_loop import InnerLoop
from .schemas import TaskOutcome


@runtime_checkable
class Worker(Protocol):
    """A pluggable task executor.

    Implementations must return a structured `TaskOutcome`. The orchestrator
    applies the outcome to per-deal state — workers do not touch pepe.db.
    """

    name: str

    def execute(self, task: dict[str, Any]) -> TaskOutcome:
        """Execute one task and return a structured outcome."""
        ...


class CustomWorker:
    """Default bounded ReAct loop. Always available; no extra dependencies.

    Bridges a task into the `InnerLoop`, whose first step is always the Von
    intent classification.
    """

    name = "custom"

    def __init__(self, deals_root, deal_id: str, router=None, registry=None,
                 model: str = "qwen3:8b", ollama_url: str = "http://localhost:11434/v1",
                 max_steps: int = 6) -> None:
        self._loop = InnerLoop(
            deals_root, deal_id, router=router, registry=registry,
            model=model, ollama_url=ollama_url, max_steps=max_steps,
        )

    def execute(self, task: dict[str, Any]) -> TaskOutcome:
        message = task.get("description", "")
        context = task.get("payload", {})
        return self._loop.run(message, context=context)


class DeepAgentWorker:
    """Optional cloud-only research worker.

    Requires the `deepagents` package (`pip install deepagents`) AND a passing
    approval gate (Phase 1.5 sanitiser + WAITING_FOR_APPROVAL gate). Until
    those exist, this worker refuses to run.
    """

    name = "deepagent"

    def __init__(self) -> None:
        if not is_deepagents_installed():
            raise RuntimeError(
                "deepagents package not installed. "
                "Run: pip install deepagents"
            )

    def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """Phase 3 stub. Real implementation configures the harness with a
        sanitised payload, structured output schema, and max-steps cap."""
        raise NotImplementedError(
            "DeepAgentWorker.execute lands in Phase 3, after Phase 1.5 "
            "sanitiser + approval gate are operational."
        )


def is_deepagents_installed() -> bool:
    try:
        import deepagents  # noqa: F401
        return True
    except ImportError:
        return False
