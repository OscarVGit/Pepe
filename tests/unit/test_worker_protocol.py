"""Unit tests for the Worker Protocol stubs."""
from __future__ import annotations

import pytest

from pepe.agent.worker import CustomWorker, DeepAgentWorker, Worker, is_deepagents_installed
from pepe.routing.deepagent_client import create_research_worker, is_available


def test_custom_worker_exists_and_named():
    w = CustomWorker()
    assert w.name == "custom"


def test_custom_worker_execute_is_phase1_stub():
    w = CustomWorker()
    with pytest.raises(NotImplementedError):
        w.execute({"description": "test"})


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


def test_custom_worker_satisfies_worker_protocol():
    # Protocol runtime_checkable — structural check.
    assert isinstance(CustomWorker(), Worker)


def test_is_deepagents_installed_returns_bool():
    assert isinstance(is_deepagents_installed(), bool)
    assert isinstance(is_available(), bool)
