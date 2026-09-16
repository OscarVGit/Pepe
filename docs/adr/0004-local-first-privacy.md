# ADR-0004 — Local-First Privacy

- Status: Accepted
- Date: 2026-09-10

## Context

CIMs, accounts, debt docs, and customer data are highly confidential. Provider
retention, re-identification via quasi-identifiers, and tool exfiltration are
real risks.

## Decision

Raw deal data stays local by default (SQLite + JSON under `deals/`).
External models receive only minimum-necessary, locally-sanitised
representations. Classification taxonomy
(PUBLIC…RESTRICTED + APPROVED_CLOUD) gates every outbound call. Scanner
failure = fail closed.

## Consequences

- `privacy/sanitise.py` + policy file are security boundaries, not helpers.
- Escalation audit must answer "what left, to whom, why, under whose authority?"
