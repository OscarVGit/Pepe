# ADR-0005 — Persistent Agent State

- Status: Accepted
- Date: 2026-09-10

## Context

Pepe must pause for hours/days (waiting on debt terms, bridges, approvals) and
resume exactly — including across process restarts.

## Decision

Explicit 10-state machine (`IDLE…FAILED`) with a `TRANSITIONS` table, persisted
to SQLite synchronously (LangGraph `sync`-durability pattern without the
dependency). Waiting states carry reason + needed input + resume plan. LLM
context is never authoritative.

## Consequences

- `state/machine.py` validates every transition; invalid ones are rejected.
- Schedules/events (Phase 5) build on `SCHEDULED`, not a parallel system.
