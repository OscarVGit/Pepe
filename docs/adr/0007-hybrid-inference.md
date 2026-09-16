# ADR-0007 — Hybrid Inference (Local-First, Cloud-Escalated)

- Status: Accepted
- Date: 2026-09-10

## Context

Local-only would cap Pepe at whatever open-weight model is installed; naive
cloud use would leak deal confidentiality. Requirement: cheapest private
capability that reliably completes the task, escalating only when necessary,
with local sanitisation and human approval.

## Decision

Wrap (don't build): LiteLLM-style Router/Gateway for local↔cloud routing,
fallbacks, and budgets behind an OpenAI-compat interface; Presidio-style
detection secondary to deterministic PE templating for sanitisation;
`mcp-gate`/`AegisGate`-style request+response filtering + signed audit on the
tool path; minimal YAML policy file now (OPA only if the firm already uses it).
`routing/router.py` + `privacy/sanitise.py` + policy file form the enforcement
boundary. De-identification happens locally before any cloud request; sending a
CIM to be anonymised remotely is forbidden.

## Alternatives considered

- Custom Pepe gateway/router — rejected (reinvents LiteLLM/RouteLLM).
- LLM self-policing prompts — rejected (must be code/gateway enforced).
- Full OPA + Redis + Postgres Day 1 — rejected (ops bloat; Phase 5+).

## Consequences

- New Phase 1.5 in ROADMAP; `local`/`gateway` remain optional extras.
- Residual risk recorded: small-universe deals can re-identify from numbers
  alone → RESTRICTED default, minimum-necessary payloads, payload-hash audit.
