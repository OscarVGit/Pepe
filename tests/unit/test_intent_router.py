"""Unit tests for the intent router (FakeRouter + taxonomy loading)."""
from __future__ import annotations

import pytest

from pepe.routing.factory import make_router
from pepe.routing.intent import FakeRouter, IntentRouter, load_intents


def test_intents_json_loads_and_has_unclear():
    cfg = load_intents()
    assert "intents" in cfg
    assert "unclear" in cfg["intents"]
    assert cfg["confidence_threshold"] == pytest.approx(0.80)


def test_fake_router_classifies_finance():
    r = FakeRouter()
    out = r.classify("Pepe, compute IRR for cashflows -100, 0, 0, 0, 170")
    assert out.intent == "compute_finance"
    assert out.served_by == "fake"
    assert out.confidence > 0.8


def test_fake_router_classifies_wait():
    r = FakeRouter()
    out = r.classify("wait for the debt terms")
    assert out.intent == "wait_for_info"


def test_fake_router_classifies_status():
    r = FakeRouter()
    assert r.classify("what is the status of atlas").intent == "status_query"


def test_fake_router_unclear_on_gibberish():
    r = FakeRouter()
    out = r.classify("asdkfj qwer zzz")
    assert out.intent == "unclear"


def test_fake_router_probabilities_cover_intents():
    r = FakeRouter()
    out = r.classify("list all deals please")
    assert out.intent == "list_deals"
    assert out.probabilities["list_deals"] == pytest.approx(0.99)


def test_make_router_fake():
    assert isinstance(make_router("fake"), FakeRouter)
    assert isinstance(make_router("fake"), IntentRouter)


def test_make_router_unknown_raises():
    with pytest.raises(ValueError):
        make_router("bogus")
