"""Integration test: finance tool run -> fact recorded in pepe.db."""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]


def _run(args: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(REPO / "src")}
    return subprocess.run(
        [sys.executable, "-m", "pepe", *args],
        cwd=cwd, env=env, capture_output=True, text=True, timeout=60,
    )


@pytest.fixture()
def deal_root(tmp_path: pathlib.Path) -> pathlib.Path:
    deals = tmp_path / "deals"
    (deals / "atlas").mkdir(parents=True)
    return tmp_path


def test_irr_run_writes_fact(deal_root):
    env = {"PEPE_ROUTER": "fake"}
    res = _run(["ask", "atlas", "compute irr for -100, 0, 0, 0, 0, 170"], cwd=deal_root)
    assert res.returncode == 0, res.stderr
    out = json.loads(res.stdout)
    assert out["outcome"]["kind"] == "complete"

    # Fact should be persisted.
    res2 = _run(["recall", "atlas", "--json"], cwd=deal_root)
    assert res2.returncode == 0, res2.stderr
    facts = json.loads(res2.stdout)
    keys = [f["key"] for f in facts]
    assert "irr" in keys
    irr = next(f for f in facts if f["key"] == "irr")
    assert irr["source"] == "finance.irr"
    assert abs(float(irr["value"]) - 0.112) < 0.005


def test_moic_run_writes_fact_in_insertion_order(deal_root):
    _run(["ask", "atlas", "compute irr for -100, 0, 0, 0, 0, 170"], cwd=deal_root)
    _run(["ask", "atlas", "compute moic of -100, 50, 50, 50, 80"], cwd=deal_root)
    res = _run(["recall", "atlas", "--json"], cwd=deal_root)
    facts = json.loads(res.stdout)
    keys = [f["key"] for f in facts]
    assert keys == ["irr", "moic"]  # insertion order


def test_overwrite_writes_new_value(deal_root):
    _run(["ask", "atlas", "compute irr for -100, 0, 0, 0, 0, 170"], cwd=deal_root)
    _run(["ask", "atlas", "compute irr for -100, 0, 0, 0, 0, 200"], cwd=deal_root)
    res = _run(["recall", "atlas", "--json"], cwd=deal_root)
    facts = json.loads(res.stdout)
    irr = next(f for f in facts if f["key"] == "irr")
    assert abs(float(irr["value"]) - 0.1487) < 0.005  # -100 -> 200 over 5y


def test_status_json_shows_facts_count(deal_root):
    _run(["ask", "atlas", "compute irr for -100, 0, 0, 0, 0, 170"], cwd=deal_root)
    res = _run(["status", "atlas"], cwd=deal_root)
    out = json.loads(res.stdout)
    assert "facts_count" in out
    assert out["facts_count"] >= 1


def test_recall_empty_deal(deal_root):
    res = _run(["recall", "atlas"], cwd=deal_root)
    assert res.returncode == 0
    assert "no facts recorded" in res.stdout
