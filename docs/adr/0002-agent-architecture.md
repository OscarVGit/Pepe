# ADR-0002 — Agent Architecture (Compose, Don't Fork)

- Status: Accepted
- Date: 2026-09-10

## Context

Candidates: OpenCode (Effect-kernel app runtime, Bun-based, client-server
session loop, MCP client, permission system — powerful but a coding-agent
server, not a persistent PE runtime); LangGraph (checkpointer/store
persistence, durable execution, interrupts — closest to our wait/resume needs);
plain Python runtime; MCP as tool protocol.

## Decision

Phase 0: custom stub runtime (`runtime/loop.py`) + our own state machine and
SQLite persistence. Consume OpenCode-like execution and LangGraph persistence
*patterns* via adapters/MCP in later phases. No hard fork of OpenCode, no
LangGraph dependency in the default install.

## Rationale

- OpenCode's Effect/Bun substrate and TUI-server model don't match a
  headless, restart-durable, messaging-driven PE worker; forking would strand
  us from upstream.
- LangGraph's durability model is the right pattern but adds weight before our
  semantics (5-memory split, approval tiers) are stable.

## Consequences

- `BUILD_VS_BUY.md` stays the gate for any runtime/tool adoption.
- A future ADR is required before adding LangGraph or OpenCode as a dependency.
