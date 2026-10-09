"""Debt schedule builder for term loans.

Build-vs-buy: no general-purpose finance library ships a complete LBO-shaped
debt schedule, so this is built on top of NumPy vector ops. The library
*never* calls audit; tool/wrapper layers record the schedule as audit rows.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class DebtPeriod:
    period: int                       # 1-indexed
    opening_balance: float
    interest: float
    scheduled_principal: float        # contractual amortisation
    sweep_principal: float            # discretionary prepayment
    closing_balance: float


def _scheduled_amort(principal: float, opening: float, annual_rate: float, term_years: int, amortisation: str, period: int) -> float:
    if amortisation in ("bullet", "interest_only"):
        return 0.0
    if amortisation == "straight_line":
        # Equal principal each period based on the ORIGINAL principal (not the
        # declining opening balance). Period is 1-indexed.
        if term_years <= 0 or period > term_years:
            return 0.0
        return principal / term_years
    raise ValueError(f"unknown amortisation: {amortisation}")


def build_debt_schedule(
    principal: float,
    annual_rate: float,
    term_years: int,
    amortisation: Literal["interest_only", "straight_line", "bullet"] = "straight_line",
    cash_sweep: float = 0.0,
    fcf_series: list[float] | None = None,
) -> list[DebtPeriod]:
    """Build a per-period debt schedule.

    Args:
        principal: loan size.
        annual_rate: coupon (decimal, e.g. 0.07).
        term_years: number of periods (we assume annual periods here; finer
            granularity is a follow-up).
        amortisation: schedule type.
        cash_sweep: fraction of available FCF (after scheduled amort) applied
            to discretionary prepayment each period. 0 disables sweep.
        fcf_series: optional list of length >= term_years giving projected
            free cash flow available for sweep each period. If None, sweep
            is disabled regardless of `cash_sweep`.
    """
    if principal <= 0:
        raise ValueError("principal must be > 0")
    if annual_rate < 0:
        raise ValueError("annual_rate must be >= 0")
    if term_years <= 0:
        raise ValueError("term_years must be > 0")
    if not 0.0 <= cash_sweep <= 1.0:
        raise ValueError("cash_sweep must be in [0, 1]")
    if fcf_series is not None and len(fcf_series) < term_years:
        raise ValueError(
            f"fcf_series must have at least {term_years} entries, got {len(fcf_series)}"
        )

    period_rate = annual_rate
    schedule: list[DebtPeriod] = []
    balance = float(principal)

    for t in range(1, term_years + 1):
        opening = balance
        interest = opening * period_rate
        sched = _scheduled_amort(principal, opening, annual_rate, term_years, amortisation, t)

        sweep = 0.0
        if cash_sweep > 0 and fcf_series is not None:
            fcf = float(fcf_series[t - 1])
            # FCF available for sweep is whatever is left after interest + sched amort.
            available = fcf - interest - sched
            if available > 0:
                sweep = min(cash_sweep * available, opening - sched)

        closing = opening - sched - sweep
        if closing < -1e-9:
            # Should never happen; guard against negative balances.
            closing = 0.0

        schedule.append(DebtPeriod(
            period=t,
            opening_balance=round(opening, 2),
            interest=round(interest, 2),
            scheduled_principal=round(sched, 2),
            sweep_principal=round(sweep, 2),
            closing_balance=round(closing, 2),
        ))
        balance = closing

    return schedule


def summarise(schedule: list[DebtPeriod]) -> dict:
    """Convenience summary: total interest, WAL (approx), ending balance."""
    if not schedule:
        return {"total_interest": 0.0, "weighted_avg_life_years": 0.0, "ending_balance": 0.0}
    total_interest = sum(p.interest for p in schedule)
    principal_outstanding = sum(p.scheduled_principal + p.sweep_principal for p in schedule) or 1.0
    wal = sum(p.period * (p.scheduled_principal + p.sweep_principal) for p in schedule) / principal_outstanding
    return {
        "total_interest": round(total_interest, 2),
        "weighted_avg_life_years": round(wal, 2),
        "ending_balance": schedule[-1].closing_balance,
    }
