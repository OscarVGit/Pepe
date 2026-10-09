"""Deterministic finance library.

Contract: pure, deterministic, side-effect-free, no I/O, no LLM. The library
never reads or writes pepe.db. Tools/audit wrap it; the library itself does
not call audit. LLMs never do this arithmetic.
"""
from __future__ import annotations

from .debt import DebtPeriod, build_debt_schedule, summarise
from .returns import (
    IRRNoSolutionError,
    cagr,
    irr,
    moic,
    npv,
)
from .sensitivity import irr_sensitivity, sensitivity_grid

__all__ = [
    "DebtPeriod",
    "IRRNoSolutionError",
    "build_debt_schedule",
    "cagr",
    "summarise",
    "irr",
    "irr_sensitivity",
    "moic",
    "npv",
    "sensitivity_grid",
]
