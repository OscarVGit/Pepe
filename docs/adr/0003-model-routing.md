# ADR-0003 — Model Routing (Deterministic-First, Cost-Aware)

- Status: Accepted
- Date: 2026-09-10

## Context

The largest model must not handle every task — cost, latency, privacy, and
reliability all argue for tiering.

## Decision

Routing order: deterministic code (IRR/MOIC/schedules) → cheap local →
medium local → large local → frontier cloud (sanitised, approved only).
Router considers task complexity, sensitivity, local capability, latency, cost,
context size, and policy. Local/private preferred where practical.

## Consequences

- `routing/router.py` owns the decision; finance never routes to LLM arithmetic.
- Gateway integration (ADR-0007) must preserve OpenAI-compat swappability.
