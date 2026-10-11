"""System prompt builder for the reasoning path of the inner loop.

Builds the context message handed to the local LLM when an open-ended intent
requires reasoning. Deal context is injected; the tool catalogue is described
in natural language so the model can select a tool.
"""
from __future__ import annotations

from typing import Any

from ..tools.registry import ToolRegistry


def build_system_prompt(deal_context: dict[str, Any] | None = None, registry: ToolRegistry | None = None) -> str:
    deal_context = deal_context or {}
    lines = [
        "You are Pepe, a junior private-equity associate. Be concise. If you do "
        "not know, say so. Never invent financial figures.",
        "",
    ]
    if deal_context:
        lines.append("Deal context:")
        for k, v in deal_context.items():
            lines.append(f"- {k}: {v}")
        lines.append("")
    if registry is not None:
        lines.append("Available tools (name: description):")
        for t in registry.list():
            lines.append(f"- {t.name}: {t.description}")
        lines.append("")
        lines.append(
            "When you need a tool, answer with JSON: {\"tool\": \"<name>\", \"params\": {...}}. "
            "When you have a final answer, answer with plain text."
        )
    return "\n".join(lines)
