"""Restart-resume integration test for Phase 1.

Exercises the real CLI as a subprocess to validate state survives process restarts.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests" / "fixtures" / "sample.xlsx"


def _run(args: list[str], cwd: pathlib.Path, env: dict | None = None) -> subprocess.CompletedProcess:
    full_env = {**os.environ, **(env or {})}
    full_env["PYTHONPATH"] = str(REPO / "src")
    return subprocess.run(
        [sys.executable, "-m", "pepe", *args],
        cwd=cwd,
        env=full_env,
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.fixture()
def deal_root(tmp_path: pathlib.Path) -> pathlib.Path:
    """A fresh per-test deals/ directory + a model file copied in."""
    deals = tmp_path / "deals"
    deals.mkdir()
    deal = deals / "atlas"
    deal.mkdir()
    (deal / "models").mkdir()
    shutil.copy2(FIXTURE, deal / "models" / "base_lbo.xlsx")
    return deals


def test_first_ask_creates_workspace_and_inspects_excel(deal_root):
    res = _run(["ask", "atlas", "inspect models/base_lbo.xlsx"], cwd=deal_root.parent)
    assert res.returncode == 0, res.stderr
    out = json.loads(res.stdout)
    assert out["outcome"]["kind"] == "complete"
    assert out["router"]["served_by"] == "fake"          # PEPE_ROUTER=fake in CI
    assert out["outcome"]["result"]["sheets"] == ["Inputs"]
    assert out["outcome"]["result"]["named_ranges"] == ["EntryMultiple"]
    assert out["state"] in {"COMPLETE", "VALIDATING", "IDLE"}  # last valid

    # Workspace artifacts on disk
    pepe_db = deal_root / "atlas" / "state" / "pepe.db"
    queue_db = deal_root / "atlas" / "state" / "queue.db"
    assert pepe_db.exists() and queue_db.exists()
    status_md = deal_root / "atlas" / "STATUS.md"
    assert status_md.exists()
    audit_jsonl = deal_root / "atlas" / "logs" / "audit.jsonl"
    assert audit_jsonl.exists()


def test_blocked_state_survives_restart(deal_root):
    res1 = _run(["ask", "atlas", "wait for debt terms"], cwd=deal_root.parent)
    assert res1.returncode == 0, res1.stderr
    out = json.loads(res1.stdout)
    assert out["outcome"]["kind"] == "waiting"

    # "Restart" the process by inspecting the persisted state.
    res2 = _run(["status", "atlas"], cwd=deal_root.parent)
    assert res2.returncode == 0, res2.stderr
    s = json.loads(res2.stdout)
    assert s["state"] == "WAITING_FOR_INFORMATION"
    assert any(t["status"] == "blocked" for t in s["active_tasks"])
    assert any(a["action"] == "task_blocked" for a in s["recent_audit"])


def test_resume_unblocks_and_completes(deal_root):
    _run(["ask", "atlas", "wait for bridge"], cwd=deal_root.parent)
    res_resume = _run(["resume", "atlas"], cwd=deal_root.parent)
    assert res_resume.returncode == 0, res_resume.stderr

    res_status = _run(["status", "atlas"], cwd=deal_root.parent)
    s = json.loads(res_status.stdout)
    # After resume the deal should be active or idle, no blocked tasks remaining.
    assert s["state"] in {"EXECUTING", "IDLE"}
    assert not any(t["status"] == "blocked" for t in s["active_tasks"])
    assert any(a["action"] == "task_unblocked" for a in s["recent_audit"])


def test_status_json_and_markdown_views(deal_root):
    _run(["ask", "atlas", "wait for bridge"], cwd=deal_root.parent)
    res_json = _run(["status", "atlas"], cwd=deal_root.parent)
    assert "WAITING_FOR_INFORMATION" in res_json.stdout
    res_md = _run(["status", "atlas", "--md"], cwd=deal_root.parent)
    assert "# atlas — Status" in res_md.stdout
    assert "Active tasks" in res_md.stdout
