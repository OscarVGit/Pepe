"""Unit tests for the bounded inner loop using FakeRouter."""
from __future__ import annotations

import pathlib

import pytest

from pepe.agent.inner_loop import InnerLoop
from pepe.routing.intent import FakeRouter
from pepe.tools.registry import default_registry


@pytest.fixture()
def loop(tmp_path):
    (tmp_path / "atlas").mkdir(parents=True, exist_ok=True)
    return InnerLoop(tmp_path, "atlas", router=FakeRouter(), registry=default_registry())


def test_first_step_is_classification(loop):
    out = loop.run("compute irr for cashflows -100, 0, 0, 0, 0, 170")
    assert out.steps[0].action == "classify"
    assert out.steps[0].router is not None
    assert out.steps[0].router["served_by"] == "fake"


def test_finance_intent_executes_deterministically(loop):
    out = loop.run("compute irr for cashflows -100, 0, 0, 0, 0, 170")
    assert out.kind == "complete"
    assert out.result["function"] == "irr"
    assert abs(out.result["value"] - 0.1119) < 0.005


def test_wait_intent_maps_to_waiting(loop):
    out = loop.run("wait for the debt terms from management")
    assert out.kind == "waiting"
    assert "awaiting" in out.reason.lower() or "debt terms" in out.reason.lower()


def test_unclear_intent_asks(loop):
    out = loop.run("asdkfj qwer zzz")
    assert out.kind == "waiting"
    assert "clarify" in out.reason.lower() or "unclear" in out.reason.lower()


def test_status_query_reads_core_index(loop):
    out = loop.run("what is the status")
    assert out.kind == "complete"
    assert "pipeline" in out.result


def test_trajectory_written(loop, tmp_path):
    out = loop.run("compute moic of -100, 170")
    assert out.run_id
    traj_dir = tmp_path / "atlas" / "runs" / out.run_id
    assert (traj_dir / "trajectory.jsonl").exists()


def test_step_cap_for_reasoning(monkeypatch, tmp_path):
    """Force an open-ended intent but no Ollama -> blocked, not a hang."""
    (tmp_path / "atlas").mkdir(parents=True, exist_ok=True)

    class ReasoningRouter(FakeRouter):
        def classify(self, message, context=None):
            from pepe.routing.intent import IntentResult
            return IntentResult(intent="research", confidence=0.99,
                                probabilities={"research": 0.99}, served_by="fake")

    loop = InnerLoop(tmp_path, "atlas", router=ReasoningRouter(), registry=default_registry(),
                     ollama_url="http://localhost:9")  # nothing here
    out = loop.run("do a full diligence deep dive")
    assert out.kind == "blocked"
    assert "ollama" in out.reason.lower() or "reachable" in out.reason.lower()
