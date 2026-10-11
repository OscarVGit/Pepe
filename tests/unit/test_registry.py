"""Unit tests for the tool registry."""
from __future__ import annotations

import pytest

from pepe.agent.policy import RiskTier
from pepe.tools.registry import (
    ApprovalRequired,
    ToolRegistry,
    ToolSpec,
    default_registry,
)


def test_register_and_lookup():
    reg = ToolRegistry()
    reg.register(ToolSpec(name="t.one", description="d", callable=lambda: 1))
    assert reg.get("t.one").name == "t.one"
    assert "t.one" in reg.names()


def test_unknown_tool_raises():
    reg = ToolRegistry()
    with pytest.raises(KeyError):
        reg.get("nope")


def test_builtin_registry_has_finance_tools():
    reg = default_registry()
    names = reg.names()
    assert "finance.irr" in names
    assert "finance.moic" in names
    assert "excel.inspect_workbook" in names
    assert "pdf.extract_text" in names


def test_high_risk_requires_approval():
    reg = ToolRegistry()
    reg.register(ToolSpec(name="t.high", description="d",
                          callable=lambda: "done", risk_tier=RiskTier.HIGH,
                          side_effect="external"))
    with pytest.raises(ApprovalRequired):
        reg.execute("t.high")
    # With approval it runs.
    assert reg.execute("t.high", approved=True) == "done"


def test_low_risk_runs_without_approval():
    reg = default_registry()
    out = reg.execute("finance.irr", cashflows=[-100, 110])
    assert out["function"] == "irr"
    assert abs(out["value"] - 0.10) < 1e-4
