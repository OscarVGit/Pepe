"""Unit tests for src/pepe/finance.debt."""
from __future__ import annotations

from pepe.finance import build_debt_schedule, summarise
from pepe.finance.debt import DebtPeriod


def test_straight_line_amort_reconciles():
    """100 principal, 10% rate, 5y straight-line -> 20 principal/year, 10/8/6/4/2 interest."""
    sched = build_debt_schedule(
        principal=100.0, annual_rate=0.10, term_years=5,
        amortisation="straight_line", cash_sweep=0.0,
    )
    assert len(sched) == 5
    assert [p.scheduled_principal for p in sched] == [20.0, 20.0, 20.0, 20.0, 20.0]
    assert [p.interest for p in sched] == [10.0, 8.0, 6.0, 4.0, 2.0]
    assert sched[0].opening_balance == 100.0
    assert sched[-1].closing_balance == pytest_approx_zero()
    # Every period: opening - principal - sweep == closing
    for p in sched:
        assert abs(p.opening_balance - p.scheduled_principal - p.sweep_principal - p.closing_balance) < 1e-9


def test_interest_only_amortisation():
    """No scheduled principal; interest each year on the original balance."""
    sched = build_debt_schedule(
        principal=100.0, annual_rate=0.05, term_years=3,
        amortisation="interest_only", cash_sweep=0.0,
    )
    assert all(p.scheduled_principal == 0.0 for p in sched)
    assert all(p.interest == 5.0 for p in sched)
    assert sched[-1].closing_balance == 100.0


def test_bullet_amortisation():
    """No scheduled principal; entire repayment must come from sweep or end-of-term."""
    sched = build_debt_schedule(
        principal=100.0, annual_rate=0.05, term_years=3,
        amortisation="bullet", cash_sweep=0.0,
    )
    assert all(p.scheduled_principal == 0.0 for p in sched)
    assert all(p.sweep_principal == 0.0 for p in sched)
    assert sched[-1].closing_balance == 100.0


def test_cash_sweep_against_fcf():
    """With 50% sweep and ample FCF, balance prepays ahead of schedule."""
    fcf = [40.0, 40.0, 40.0, 40.0, 40.0]
    sched = build_debt_schedule(
        principal=100.0, annual_rate=0.10, term_years=5,
        amortisation="straight_line", cash_sweep=0.50, fcf_series=fcf,
    )
    # Year 1: opening 100, interest 10, scheduled 20, available FCF 40-10-20=10,
    # sweep = 0.5 * 10 = 5, closing = 100 - 20 - 5 = 75.
    assert sched[0].interest == 10.0
    assert sched[0].scheduled_principal == 20.0
    assert sched[0].sweep_principal == 5.0
    assert sched[0].closing_balance == 75.0


def test_cash_sweep_without_fcf_is_disabled():
    """Without fcf_series, cash_sweep has no effect."""
    sched = build_debt_schedule(
        principal=100.0, annual_rate=0.10, term_years=5,
        amortisation="straight_line", cash_sweep=0.50, fcf_series=None,
    )
    assert all(p.sweep_principal == 0.0 for p in sched)


def test_summarise_returns_summary_dict():
    sched = build_debt_schedule(
        principal=100.0, annual_rate=0.10, term_years=5,
        amortisation="straight_line",
    )
    s = summarise(sched)
    assert s["total_interest"] == 30.0  # 10 + 8 + 6 + 4 + 2
    assert s["ending_balance"] == 0.0
    # WAL: principal repayments of 20 each year -> (1+2+3+4+5)/5 = 3.0
    assert s["weighted_avg_life_years"] == 3.0


def test_invalid_inputs_raise():
    import pytest
    with pytest.raises(ValueError):
        build_debt_schedule(principal=0, annual_rate=0.05, term_years=3)
    with pytest.raises(ValueError):
        build_debt_schedule(principal=100, annual_rate=0.05, term_years=0)
    with pytest.raises(ValueError):
        build_debt_schedule(
            principal=100, annual_rate=0.05, term_years=3,
            cash_sweep=1.5, fcf_series=[10, 10, 10],
        )


# local helper for the closing-balance assertion
def pytest_approx_zero():
    return 0.0  # tolerate rounded cents