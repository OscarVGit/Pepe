"""Optional Deep Agents harness client.

Only used when the `deepagents` package is present AND Phase 1.5 sanitiser
+ approval gate are operational. Until then, `is_available()` returns False
and `create_research_worker()` raises.
"""
from __future__ import annotations

from typing import Any, Optional


def is_available() -> bool:
    try:
        import deepagents  # noqa: F401
        return True
    except ImportError:
        return False


def create_research_worker(config: Optional[dict[str, Any]] = None) -> Any:
    """Create a cloud-configured deep agent for research/diligence tasks.

    Phase 3: configure with sanitised input, structured output schema, max steps.
    Returns an object with `.invoke(messages)` matching a simple chat interface.
    """
    if not is_available():
        raise RuntimeError(
            "deepagents not installed. "
            "Run: pip install deepagents  (or pip install pepe[research] when available)"
        )
    # Phase 3 will wire up:
    #   - model = cloud provider approved by routing policy
    #   - tools = PE-specific MCP tools (read-only)
    #   - system prompt = "structured findings table, no free prose"
    #   - output schema = {claims, sources, confidence, gaps}
    #   - max_steps cap to bound error cascades
    raise NotImplementedError(
        "create_research_worker is a Phase 3 stub. "
        "Required prerequisites: Phase 1.5 sanitiser + approval gate operational."
    )
