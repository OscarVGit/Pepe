"""Unit tests for the state machine: transitions + persistence."""
from __future__ import annotations

import sqlite3
import threading

import pytest

from pepe.state.machine import (
    AgentState, InvalidTransitionError, can_transition, load_state, save_state,
)
from pepe.state.schema import init as init_schema


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    init_schema(c)
    yield c
    c.close()


@pytest.fixture()
def lock():
    return threading.Lock()


def test_initial_state_is_idle(conn, lock):
    assert load_state(conn, lock, "atlas") == AgentState.IDLE


def test_valid_transition_persists(conn, lock):
    save_state(conn, lock, "atlas", AgentState.UNDERSTANDING, reason="test")
    assert load_state(conn, lock, "atlas") == AgentState.UNDERSTANDING


def test_invalid_transition_raises(conn, lock):
    save_state(conn, lock, "atlas", AgentState.UNDERSTANDING, reason="test")
    with pytest.raises(InvalidTransitionError):
        # EXECUTING is not reachable directly from UNDERSTANDING.
        save_state(conn, lock, "atlas", AgentState.EXECUTING)


def test_full_happy_path(conn, lock):
    path = [
        AgentState.UNDERSTANDING,
        AgentState.PLANNING,
        AgentState.EXECUTING,
        AgentState.WAITING_FOR_INFORMATION,
        AgentState.EXECUTING,
        AgentState.VALIDATING,
        AgentState.COMPLETE,
        AgentState.IDLE,
    ]
    for s in path:
        save_state(conn, lock, "atlas", s)
    assert load_state(conn, lock, "atlas") == AgentState.IDLE


def test_expected_from_guard(conn, lock):
    save_state(conn, lock, "atlas", AgentState.UNDERSTANDING)
    with pytest.raises(InvalidTransitionError):
        save_state(conn, lock, "atlas", AgentState.PLANNING,
                   expected_from=AgentState.EXECUTING)


def test_can_transition_table_consistency():
    # Every state must list at least one outgoing edge or be terminal-ish.
    for s in AgentState:
        if s in (AgentState.IDLE, AgentState.WAITING_FOR_INFORMATION,
                 AgentState.WAITING_FOR_APPROVAL, AgentState.BLOCKED,
                 AgentState.VALIDATING, AgentState.FAILED,
                 AgentState.SCHEDULED, AgentState.COMPLETE):
            assert TRANSITIONS_HAS_OUT(s) or s in TERMINAL_OK


def TRANSITIONS_HAS_OUT(s):
    from pepe.state.machine import TRANSITIONS
    return len(TRANSITIONS[s]) > 0


TERMINAL_OK = set()  # all states should have an outgoing edge in this design
