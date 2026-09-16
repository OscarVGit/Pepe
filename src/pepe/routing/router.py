"""Model routing + local-first hybrid inference. See docs/MODEL_ROUTING.md and ADR-0007."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Capability(str, Enum):
    DETERMINISTIC = "deterministic"  # IRR/MOIC/schedules → code, never LLM arithmetic
    LOCAL = "local"                  # Ollama / MLX / self-hosted OpenAI-compat
    CLOUD = "cloud"                  # approved frontier, sanitised payload only


@dataclass
class RoutingDecision:
    capability: Capability
    model: str = ""
    reason: str = ""
    needs_approval: bool = False


def route(task_complexity: str, classification: str, local_capable: bool, cloud_permitted: bool) -> RoutingDecision:
    """Phase 1: policy + confidence routing. Phase 0: deterministic-first stub logic."""
    if task_complexity == "deterministic":
        return RoutingDecision(Capability.DETERMINISTIC, reason="code calculates")
    if local_capable:
        return RoutingDecision(Capability.LOCAL, model="local", reason="cheapest private capable")
    if cloud_permitted:
        return RoutingDecision(Capability.CLOUD, reason="escalation", needs_approval=True)
    return RoutingDecision(Capability.LOCAL, model="local", reason="keep local, ask user")
