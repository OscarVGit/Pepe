"""Unit tests for the Pepe Core Index."""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import pytest

from pepe.core_index import (
    get_firm_db,
    global_search,
    list_active_deals,
    list_deals,
    pipeline_summary,
    sync_all,
    sync_deal,
)
from pepe.state.connection import get_pepe_db as get_deal_db
from pepe.state.schema import init as init_deal_schema
from pepe.workspace.deal import create as create_deal


def _bootstrap_deal(deals_root: Path, deal_id: str, name: str | None = None) -> None:
    create_deal(deals_root, deal_id, name=name or deal_id)


def test_sync_deal_creates_registry_row(tmp_path: Path):
    deals_root = tmp_path / "deals"
    _bootstrap_deal(deals_root, "atlas", name="Atlas")

    ok = sync_deal(tmp_path, "atlas")
    assert ok is True
    rows = list_deals(tmp_path)
    assert len(rows) == 1
    assert rows[0]["id"] == "atlas"
    assert rows[0]["name"] == "Atlas"


def test_pipeline_summary_counts(tmp_path: Path):
    deals_root = tmp_path / "deals"
    _bootstrap_deal(deals_root, "atlas", name="Atlas")
    _bootstrap_deal(deals_root, "nova", name="Nova")
    sync_all(tmp_path)

    s = pipeline_summary(tmp_path)
    assert s["total_deals"] == 2
    # Both deals are in IDLE state — not "active" by our filter.
    assert s["active"] == 0
    assert s["blocked_tasks"] == 0
    assert s["pending_tasks"] == 0


def test_global_search_finds_deals_and_tasks(tmp_path: Path):
    deals_root = tmp_path / "deals"
    _bootstrap_deal(deals_root, "atlas", name="Atlas")
    sync_all(tmp_path)

    result = global_search(tmp_path, "Atlas")
    assert any(d["id"] == "atlas" for d in result["deals"])
    assert result["tasks"] == []

    result = global_search(tmp_path, "atlas")
    assert any(d["id"] == "atlas" for d in result["deals"])


def test_sync_reflects_blocked_tasks(tmp_path: Path):
    from pepe.state.tasks import block, claim_next, enqueue

    deals_root = tmp_path / "deals"
    _bootstrap_deal(deals_root, "atlas")
    enqueue(deals_root, "atlas", "wait for bridge")
    t = claim_next(deals_root, "atlas")
    assert t is not None
    block(deals_root, "atlas", t.queue_message_id, t.claim_id, reason="debt terms")
    sync_deal(tmp_path, "atlas")

    s = pipeline_summary(tmp_path)
    assert s["blocked_tasks"] == 1
    rows = list_active_deals(tmp_path)  # IDLE state → empty by filter
    assert rows == []


def test_sync_all_handles_empty_deals_dir(tmp_path: Path):
    (tmp_path / "deals").mkdir()
    assert sync_all(tmp_path) == 0
    assert pipeline_summary(tmp_path) == {
        "total_deals": 0,
        "active": 0,
        "blocked_tasks": 0,
        "pending_tasks": 0,
    }


def test_sync_deal_is_idempotent(tmp_path: Path):
    deals_root = tmp_path / "deals"
    _bootstrap_deal(deals_root, "atlas")
    sync_deal(tmp_path, "atlas")
    sync_deal(tmp_path, "atlas")
    sync_deal(tmp_path, "atlas")
    rows = list_deals(tmp_path)
    assert len(rows) == 1
