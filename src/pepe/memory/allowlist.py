"""Fact allowlist + tool→key mapping.

Deterministic tool outputs only — the loop never guesses. Anything not in the
allowlist is ignored and audited as `fact_skipped`. The mapping is deliberately
narrow: each finance tool may write exactly one fact, keyed on its function name.
"""
from __future__ import annotations

# Ordered — pepe recall uses insertion order for display.
ALLOWED_FACT_KEYS: tuple[str, ...] = (
    # Returns
    "irr", "moic", "cagr", "npv",
    # Multiples / structure
    "entry_multiple", "exit_multiple", "debt_to_ebitda", "interest_rate",
    # P&L anchors
    "revenue", "ebitda", "ebitda_margin",
    # Debt
    "debt_principal",
)

# Which tool is allowed to write which key. Deterministic 1:1 mapping for the
# finance tools; other tools write nothing.
FACT_SOURCES: dict[str, tuple[str, ...]] = {
    "irr": ("finance.irr",),
    "moic": ("finance.moic",),
    "cagr": ("finance.cagr",),
    "npv": ("finance.npv",),
}

# A tool's output field that becomes the fact value. Finance tools store the
# computed value under "value" (see src/pepe/tools/built_in.py).
FACT_VALUE_FIELD = "value"


def allowed_key(key: str) -> bool:
    return key in ALLOWED_FACT_KEYS


def fact_source_tool(key: str) -> str | None:
    tools = FACT_SOURCES.get(key)
    return tools[0] if tools else None
