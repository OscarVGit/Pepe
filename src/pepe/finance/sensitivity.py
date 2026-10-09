"""Sensitivity grids: 2-way (and n-way) tables over a metric callable."""
from __future__ import annotations

import itertools
from collections.abc import Callable
from typing import Any


def sensitivity_grid(
    metric: Callable[..., float],
    base: dict[str, Any],
    axes: dict[str, list[Any]],
) -> list[dict]:
    """Compute the metric at every combination of axis values.

    `metric` is called as `metric(**{**base, **cell})` for each cell. Returns
    a list of dicts, one per cell, with the cell values merged in plus a
    `metric_value` key. Order is the natural Cartesian product order.
    """
    if not axes:
        return [{**base, "metric_value": float(metric(**base))}]
    keys = list(axes.keys())
    grid: list[dict] = []
    for combo in itertools.product(*(axes[k] for k in keys)):
        cell = dict(zip(keys, combo))
        params = {**base, **cell}
        value = float(metric(**params))
        grid.append({**cell, "metric_value": value})
    return grid


def irr_sensitivity(
    cashflows: list[float],
    vary: list[tuple[str, list[float]]],
) -> list[dict]:
    """Convenience: vary one or more indexed cashflows and re-solve IRR.

    `vary` is a list of (label, values) pairs. For each value, a copy of
    `cashflows` is made and the value substituted (label must be of the form
    "t{i}" meaning the i-th cashflow, or "scale" meaning multiply all
    positive flows by that factor).
    """
    from .returns import irr

    rows: list[dict] = []
    if not vary:
        return [{"metric_value": irr(cashflows)}]
    keys = [k for k, _ in vary]
    values_lists = [v for _, v in vary]
    for combo in itertools.product(*values_lists):
        cell = dict(zip(keys, combo))
        cf = list(cashflows)
        for k, v in cell.items():
            if k.startswith("t") and k[1:].isdigit():
                idx = int(k[1:])
                if 0 <= idx < len(cf):
                    cf[idx] = v
            elif k == "scale":
                cf = [x * v if x > 0 else x for x in cf]
        rows.append({**cell, "metric_value": irr(cf)})
    return rows
