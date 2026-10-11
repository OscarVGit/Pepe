"""Unit tests for the Worker Protocol stubs."""
from __future__ import annotations

import pathlib

import pytest

from pepe.agent.worker import CustomWorker, DeepAgentWorker, Worker, is_deepagents_installed
from pepe.routing.deepagent_client import create_research_worker, is_available
from pepe.routing.factory import make_router
from pepe.routing.intent import FakeRouter


def test_custom_worker_exists_and_named(tmp_path):
    w = CustomWorker(tmp_path, "atlas", router=FakeRouter())
    assert w.name == "custom"


def test_custom_worker_runs_terminal_intent(tmp_path):
    """A compute_finance intent should execute deterministically via the loop."""
    (tmp_path / "atlas").mkdir(parents=True, exist_ok=True)
    w = CustomWorker(tmp_path, "atlas", router=FakeRouter())
    outcome = w.execute({"description": "compute irr for cashflows -100, 0, 0, 0, 0, 170"})
    assert outcome.kind == "complete"
    assert outcome.result["function"] == "irr"
    assert abs(outcome.result["value"] - 0.1119) < 0.005


def test_custom_worker_satisfies_worker_protocol(tmp_path):
    assert isinstance(CustomWorker(tmp_path, "atlas", router=FakeRouter()), Worker)


def test_deepagent_worker_raises_without_package():
    if is_deepagents_installed():
        pytest.skip("deepagents package is present in this environment")
    with pytest.raises(RuntimeError, match="deepagents package not installed"):
        DeepAgentWorker()


def test_create_research_worker_raises_without_package():
    if is_available():
        pytest.skip("deepagents package is present")
    with pytest.raises(RuntimeError, match="deepagents not installed"):
        create_research_worker()


def test_is_deepagents_installed_returns_bool():
    assert isinstance(is_deepagents_installed(), bool)
    assert isinstance(is_available(), bool)


def test_make_router_fake_is_default_safe():
    assert isinstance(make_router("fake"), FakeRouter)
