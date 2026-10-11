"""Built-in tool registrations.

Maps the deterministic finance/Excel/PDF functions into `ToolSpec`s with risk
tiers. Read-only tools are LOW risk. Writing tools (not yet implemented) are
MEDIUM/HIGH and gated by the registry's risk-tier enforcement.
"""
from __future__ import annotations

from pathlib import Path

from ..agent.policy import RiskTier
from ..finance import cagr, irr, moic, npv
from .excel_api import inspect_workbook, list_sheets
from .pdf_api import extract_text, list_pages
from .registry import ToolRegistry, ToolSpec


def _finance_irr(cashflows: list[float]) -> dict:
    return {"function": "irr", "cashflows": cashflows, "value": irr(cashflows)}


def _finance_moic(cashflows: list[float]) -> dict:
    return {"function": "moic", "cashflows": cashflows, "value": moic(cashflows)}


def _finance_npv(rate: float, cashflows: list[float]) -> dict:
    return {"function": "npv", "rate": rate, "cashflows": cashflows, "value": npv(rate, cashflows)}


def _finance_cagr(start: float, end: float, years: float) -> dict:
    return {"function": "cagr", "start": start, "end": end, "years": years, "value": cagr(start, end, years)}


def _excel_inspect_workbook(path: str) -> dict:
    return inspect_workbook(Path(path)).to_dict()


def _excel_list_sheets(path: str) -> list[str]:
    return list_sheets(Path(path))


def _pdf_extract_text(path: str) -> dict:
    p = Path(path)
    return {"path": path, "pages": list_pages(p), "preview": extract_text(p)[:2000]}


def register_builtin_tools(reg: ToolRegistry) -> ToolRegistry:
    reg.register(ToolSpec(
        name="finance.irr", description="Compute IRR from a cashflow list",
        callable=_finance_irr, risk_tier=RiskTier.LOW, side_effect="read_only",
        params={"cashflows": "list[float]"},
    ))
    reg.register(ToolSpec(
        name="finance.moic", description="Compute MOIC from a cashflow list",
        callable=_finance_moic, risk_tier=RiskTier.LOW, side_effect="read_only",
        params={"cashflows": "list[float]"},
    ))
    reg.register(ToolSpec(
        name="finance.npv", description="Compute NPV at a discount rate over cashflows",
        callable=_finance_npv, risk_tier=RiskTier.LOW, side_effect="read_only",
        params={"rate": "float", "cashflows": "list[float]"},
    ))
    reg.register(ToolSpec(
        name="finance.cagr", description="Compute CAGR from start, end, years",
        callable=_finance_cagr, risk_tier=RiskTier.LOW, side_effect="read_only",
        params={"start": "float", "end": "float", "years": "float"},
    ))
    reg.register(ToolSpec(
        name="excel.inspect_workbook", description="Inspect an Excel workbook (sheets, named ranges, dimensions)",
        callable=_excel_inspect_workbook, risk_tier=RiskTier.LOW, side_effect="read_only",
        params={"path": "str"},
    ))
    reg.register(ToolSpec(
        name="excel.list_sheets", description="List sheets in an Excel workbook",
        callable=_excel_list_sheets, risk_tier=RiskTier.LOW, side_effect="read_only",
        params={"path": "str"},
    ))
    reg.register(ToolSpec(
        name="pdf.extract_text", description="Extract preview text + page count from a PDF",
        callable=_pdf_extract_text, risk_tier=RiskTier.LOW, side_effect="read_only",
        params={"path": "str"},
    ))
    return reg
