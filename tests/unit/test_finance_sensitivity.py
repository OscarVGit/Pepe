"""Unit tests for src/pepe/finance.sensitivity."""
from __future__ import annotations

from pepe.finance import irr_sensitivity, sensitivity_grid


def test_sensitivity_grid_shape():
    def metric(a, b):
        return a + b

    grid = sensitivity_grid(
        metric=metric, base={},
        axes={"a": [1, 2, 3], "b": [10, 20]},
    )
    assert len(grid) == 6  # 3 x 2
    assert grid[0] == {"a": 1, "b": 10, "metric_value": 11.0}
    assert grid[5] == {"a": 3, "b": 20, "metric_value": 23.0}


def test_sensitivity_grid_no_axes_returns_single_row():
    grid = sensitivity_grid(metric=lambda: 42.0, base={}, axes={})
    assert len(grid) == 1
    assert grid[0]["metric_value"] == 42.0


def test_irr_sensitivity_scales_exits():
    """Vary exit proceeds (t5) across a range and confirm IRR moves correctly."""
    base = [-100, 0, 0, 0, 0, 170]
    rows = irr_sensitivity(base, vary=[("t5", [150, 170, 190])])
    assert len(rows) == 3
    irrs = [r["metric_value"] for r in rows]
    # Higher exit -> higher IRR
    assert irrs[0] < irrs[1] < irrs[2]
    # Middle one ~ 11.19%
    assert abs(irrs[1] - 0.1119) < 0.005


def test_irr_sensitivity_scale_factor():
    """The 'scale' key multiplies all positive flows by the factor."""
    base = [-100, 0, 0, 0, 0, 170]
    rows = irr_sensitivity(base, vary=[("scale", [0.5, 1.0, 1.5])])
    irrs = [r["metric_value"] for r in rows]
    assert irrs[0] < irrs[1] < irrs[2]