"""Integration test: cross-deal pipeline via the CLI end-to-end."""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]


def _run(args: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(REPO / "src")}
    return subprocess.run(
        [sys.executable, "-m", "pepe", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.fixture()
def repo_root(tmp_path: pathlib.Path) -> pathlib.Path:
    """A fresh repo root with a deals/ directory and one fixture model."""
    deals = tmp_path / "deals"
    deals.mkdir()
    deal = deals / "atlas"
    deal.mkdir()
    (deal / "models").mkdir()
    fixture = REPO / "tests" / "fixtures" / "sample.xlsx"
    shutil.copy2(fixture, deal / "models" / "base_lbo.xlsx")
    return tmp_path


def test_ask_auto_syncs_to_core_index(repo_root):
    res = _run(["ask", "atlas", "wait for bridge"], cwd=repo_root)
    assert res.returncode == 0, res.stderr

    firm_db = repo_root / "pepe.db"
    assert firm_db.exists(), "auto-sync should have created pepe.db at repo root"

    res_pipeline = _run(["pipeline"], cwd=repo_root)
    assert res_pipeline.returncode == 0, res_pipeline.stderr
    out = json.loads(res_pipeline.stdout)
    assert out["summary"]["total_deals"] == 1
    assert out["summary"]["blocked_tasks"] == 1


def test_explicit_sync_rebuilds_index(repo_root):
    # First ask, which auto-syncs.
    _run(["ask", "atlas", "wait for bridge"], cwd=repo_root)
    # Now do an explicit sync.
    res = _run(["sync"], cwd=repo_root)
    assert res.returncode == 0, res.stderr
    out = json.loads(res.stdout)
    assert out["synced"] == 1
    assert out["summary"]["total_deals"] == 1


def test_list_command_enumerates_deals(repo_root):
    _run(["ask", "atlas", "wait for bridge"], cwd=repo_root)
    res = _run(["list"], cwd=repo_root)
    assert res.returncode == 0, res.stderr
    out = json.loads(res.stdout)
    assert len(out) == 1
    assert out[0]["id"] == "atlas"


def test_search_finds_across_deals(repo_root):
    _run(["ask", "atlas", "wait for bridge"], cwd=repo_root)
    res = _run(["search", "atlas"], cwd=repo_root)
    assert res.returncode == 0, res.stderr
    out = json.loads(res.stdout)
    assert any(d["id"] == "atlas" for d in out["deals"])

    res2 = _run(["search", "bridge"], cwd=repo_root)
    out2 = json.loads(res2.stdout)
    assert any("bridge" in t["description"].lower() for t in out2["tasks"])


def test_firm_level_status_no_deal_id(repo_root):
    _run(["ask", "atlas", "wait for bridge"], cwd=repo_root)
    res = _run(["status"], cwd=repo_root)
    assert res.returncode == 0, res.stderr
    out = json.loads(res.stdout)
    assert out["scope"] == "firm"
    assert out["summary"]["total_deals"] == 1
    assert len(out["all_deals"]) == 1


def test_status_query_produces_reply_on_stderr(repo_root):
    _run(["ask", "atlas", "wait for bridge"], cwd=repo_root)
    res = _run(["ask", "atlas", "what is the status"], cwd=repo_root)
    assert res.returncode == 0, res.stderr
    # The conversational reply is on stderr, stdout stays pure JSON.
    assert "[pepe]" in res.stderr
    out = json.loads(res.stdout)
    assert out["outcome"]["kind"] == "complete"
    assert "reply" in out["outcome"]["result"]


def test_status_query_reports_named_deal(repo_root):
    _run(["ask", "atlas", "wait for bridge"], cwd=repo_root)
    res = _run(["ask", "atlas", "what is the status of atlas"], cwd=repo_root)
    assert res.returncode == 0, res.stderr
    assert "[pepe] atlas " in res.stderr
    out = json.loads(res.stdout)
    result = out["outcome"]["result"]
    assert result.get("deal") == "atlas"
    assert "state" in result
