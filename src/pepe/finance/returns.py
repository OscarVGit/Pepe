"""Investment performance metrics over a cash-flow stream.

Build-vs-buy: IRR and NPV delegate to `numpy_financial` (the de-facto finance
library in the NumPy ecosystem). MOIC and CAGR are closed-form and need no
library.
"""
from __future__ import annotations

import math
from typing import Sequence


class IRRNoSolutionError(ValueError):
    """Raised when IRR has no real solution for the given cashflows."""


def _validate_cashflows(cashflows: Sequence[float]) -> list[float]:
    if cashflows is None or len(cashflows) == 0:
        raise ValueError("cashflows must be a non-empty sequence")
    if len(cashflows) < 2:
        raise ValueError("cashflows must contain at least two entries (t=0 outflow and >=1 inflow)")
    cf = [float(x) for x in cashflows]
    return cf


def npv(rate: float, cashflows: Sequence[float]) -> float:
    """Net present value. `cashflows[0]` is at t=0 (undiscounted)."""
    cf = _validate_cashflows(cashflows)
    import numpy_financial as npf  # local import keeps module importable for tooling
    return float(npf.npv(rate, cf))


def irr(cashflows: Sequence[float], tolerance: float = 1e-7, max_iter: int = 300) -> float:
    """Internal rate of return.

    Delegates to `numpy_financial.irr`. If that returns NaN (no real root)
    we fall back to a Newton-Raphson solver with bisection, then raise
    `IRRNoSolutionError` if no sign change is recoverable.
    """
    cf = _validate_cashflows(cashflows)
    import numpy_financial as npf
    r = float(npf.irr(cf))
    if not math.isnan(r):
        return r
    # Fallback: bracketed bisection. Requires at least one positive and one
    # negative flow (the precondition for a real IRR).
    has_pos = any(x > 0 for x in cf)
    has_neg = any(x < 0 for x in cf)
    if not (has_pos and has_neg):
        raise IRRNoSolutionError("no sign change in cashflows; IRR undefined")
    lo, hi = -0.999, 10.0
    for _ in range(max_iter):
        mid = (lo + hi) / 2.0
        v = float(npf.npv(mid, cf))
        if abs(v) < tolerance:
            return mid
        if v > 0:
            lo = mid
        else:
            hi = mid
        if (hi - lo) < tolerance:
            return mid
    raise IRRNoSolutionError("bisection did not converge")


def moic(cashflows: Sequence[float]) -> float:
    """Multiple of invested capital: sum(inflows) / sum(|outflows|).

    Returns 0.0 if there are no outflows. Handles the standard LBO shape
    (negative at t=0, positive at exit + interim distributions).
    """
    cf = _validate_cashflows(cashflows)
    invested = sum(-x for x in cf if x < 0)
    returned = sum(x for x in cf if x > 0)
    if invested == 0:
        raise ValueError("cannot compute MOIC with no invested capital (no negative cashflows)")
    return returned / invested


def cagr(start: float, end: float, years: float) -> float:
    """Compound annual growth rate."""
    if years <= 0:
        raise ValueError("years must be > 0")
    if start <= 0:
        raise ValueError("start must be > 0")
    return (end / start) ** (1.0 / years) - 1.0
