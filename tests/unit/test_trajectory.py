"""Unit tests for the trajectory recorder."""
from __future__ import annotations

from pepe.agent.schemas import Step
from pepe.agent.trajectory import TrajectoryRecorder, latest_run_dir, read_trajectory


def test_record_and_read_roundtrip(tmp_path):
    deal = tmp_path / "atlas"
    deal.mkdir(parents=True)
    rec = TrajectoryRecorder(deal, "atlas")
    rec.record(Step(index=0, action="classify", outputs={"intent": "compute_finance"}))
    rec.record(Step(index=1, action="tool", tool="finance.irr", outputs={"value": 0.11}))
    rec.record(Step(index=2, action="complete", note="done"))

    assert latest_run_dir(deal) == rec.dir
    steps = read_trajectory(deal, run_id=rec.run_id)
    assert len(steps) == 3
    assert steps[0]["action"] == "classify"
    assert steps[0]["outputs"]["intent"] == "compute_finance"
    assert steps[1]["tool"] == "finance.irr"
    assert steps[2]["action"] == "complete"


def test_latest_run_dir_none_when_no_runs(tmp_path):
    deal = tmp_path / "atlas"
    deal.mkdir(parents=True)
    assert latest_run_dir(deal) is None
    assert read_trajectory(deal) == []


def test_each_run_gets_unique_dir(tmp_path):
    deal = tmp_path / "atlas"
    deal.mkdir(parents=True)
    a = TrajectoryRecorder(deal, "atlas")
    b = TrajectoryRecorder(deal, "atlas")
    assert a.run_id != b.run_id
    assert a.dir != b.dir
