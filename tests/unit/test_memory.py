"""Unit tests for the memory store + allowlist (deterministic tool outputs)."""
from __future__ import annotations

import pathlib
import sqlite3

import pytest

from pepe.memory.allowlist import ALLOWED_FACT_KEYS, allowed_key, fact_source_tool
from pepe.memory.store import get_fact, list_facts, save_fact
from pepe.state.connection import get_pepe_db
from pepe.workspace.deal import create as create_deal


@pytest.fixture()
def deals_root(tmp_path):
    d = tmp_path / "deals"
    create_deal(d, "atlas", name="Atlas")
    return d


def test_allowlist_contains_expected_keys():
    for k in ("irr", "moic", "cagr", "npv", "ebitda", "revenue"):
        assert k in ALLOWED_FACT_KEYS


def test_allowed_key():
    assert allowed_key("irr")
    assert not allowed_key("whatever")


def test_fact_source_tool_mapping():
    assert fact_source_tool("irr") == "finance.irr"
    assert fact_source_tool("revenue") is None


def test_save_and_list_facts(deals_root):
    written, prev = save_fact(deals_root, "atlas", "irr", "0.112", source="finance.irr")
    assert written is True
    assert prev is None
    facts = list_facts(deals_root, "atlas")
    assert len(facts) == 1
    assert facts[0].key == "irr" and facts[0].value == "0.112"


def test_insertion_order_is_preserved(deals_root):
    save_fact(deals_root, "atlas", "irr", "0.112", source="finance.irr")
    save_fact(deals_root, "atlas", "moic", "1.7", source="finance.moic")
    facts = list_facts(deals_root, "atlas")
    assert [f.key for f in facts] == ["irr", "moic"]


def test_disallowed_key_is_not_written(deals_root):
    written, prev = save_fact(deals_root, "atlas", "nonsense_key", "x", source="test")
    assert written is False and prev is None
    assert list_facts(deals_root, "atlas") == []


def test_overwrite_writes_new_value_and_returns_previous(deals_root):
    save_fact(deals_root, "atlas", "irr", "0.112", source="finance.irr")
    written, prev = save_fact(deals_root, "atlas", "irr", "0.118", source="finance.irr")
    assert written is True
    assert prev is not None and prev.value == "0.112"
    facts = list_facts(deals_root, "atlas")
    assert len(facts) == 1  # overwritten, not duplicated
    assert facts[0].value == "0.118"


def test_get_fact(deals_root):
    save_fact(deals_root, "atlas", "moic", "1.7", source="finance.moic")
    f = get_fact(deals_root, "atlas", "moic")
    assert f is not None and f.value == "1.7"
    assert get_fact(deals_root, "atlas", "irr") is None


def test_malformed_key_rejected(deals_root):
    written, _ = save_fact(deals_root, "atlas", "", "x", source="test")
    assert written is False
