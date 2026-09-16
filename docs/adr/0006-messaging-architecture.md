# ADR-0006 — Messaging Architecture

- Status: Accepted
- Date: 2026-09-10

## Context

Telegram is easiest for dev; WhatsApp/Slack/Teams must not require rewrites.
The agent must not know which channel a message arrived on.

## Decision

`MessageChannel` Protocol + `NormalizedMessage`. Runtime binds user↔agent and
conversation↔deal. Telegram polling adapter first; WhatsApp webhook second;
Slack/Teams/Web later behind the same interface.

## Consequences

- Channel code is replaceable; deal binding and approvals live in the runtime.
- Auth = user allowlist from day one of Phase 2.
