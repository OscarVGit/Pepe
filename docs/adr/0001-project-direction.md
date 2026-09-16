# ADR-0001 — Project Direction

- Status: Accepted
- Date: 2026-09-10

## Context

PE professionals drown in disconnected tools. The goal is an AI employee
contacted over messaging — not another chatbot, Excel copilot, or analysis app.

## Decision

Build Pepe as a persistent deal-centric associate: one workspace per deal,
messaging front door (Telegram first), deterministic finance in code, audit +
approvals architectural.

## Consequences

- Deal state survives restarts; context never re-explained.
- MVP scoped to one deal over messaging (PRODUCT.md core test).
- All later ADRs must preserve the employee-not-app distinction.
