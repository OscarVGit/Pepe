"""Tool registry: discoverable, policy-tagged tools.

A `ToolSpec` describes a tool's name, description, risk tier, and callable.
The registry is the Pepe-layer catalogue the inner loop dispatches into.
Risk tiers are enforced at the registry boundary (architectural approvals,
ADR-0007/0008), never by prompt.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from ..agent.policy import RiskTier, classify as classify_action


class ApprovalRequired(RuntimeError):
    """Raised when a high-risk tool is invoked without approval."""

    def __init__(self, tool_name: str):
        super().__init__(f"tool '{tool_name}' requires approval")
        self.tool_name = tool_name


@dataclass
class ToolSpec:
    name: str
    description: str
    callable: Callable[..., Any]
    risk_tier: RiskTier = RiskTier.LOW
    side_effect: str = "read_only"  # read_only | mutates | external
    params: dict[str, str] = field(default_factory=dict)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.callable(*args, **kwargs)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> ToolSpec:
        self._tools[spec.name] = spec
        return spec

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            raise KeyError(f"tool not registered: {name}")
        return self._tools[name]

    def list(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def execute(
        self,
        name: str,
        *,
        approved: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Execute a tool with risk-tier enforcement.

        High-risk tools require `approved=True`; otherwise they raise
        `ApprovalRequired` so the orchestrator can park the task in
        WAITING_FOR_APPROVAL.
        """
        spec = self.get(name)
        tier = spec.risk_tier
        if tier is None:
            tier = classify_action(name)
        if tier is RiskTier.HIGH and not approved:
            raise ApprovalRequired(name)
        return spec(**kwargs)


# ---------------------------------------------------------------------------
# Shared default registry. Populated by `register_builtin_tools()`.
# ---------------------------------------------------------------------------
_default_registry: Optional[ToolRegistry] = None


def default_registry() -> ToolRegistry:
    global _default_registry
    if _default_registry is None:
        _default_registry = ToolRegistry()
        from .built_in import register_builtin_tools

        register_builtin_tools(_default_registry)
    return _default_registry
