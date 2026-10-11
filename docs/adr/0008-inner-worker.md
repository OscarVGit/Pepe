# ADR-0008 — Inner Worker Architecture (Reconnaissance vs Surgery)

- Status: Accepted
- Date: 2026-09-10

## Context

Pepe needs both deterministic calculation and open-ended reasoning. A hand-rolled
bounded ReAct loop is the correct default for short-horizon, verifiable tasks.
Long-horizon reasoning (multi-document diligence, comps synthesis, CIM
interpretation) needs context management and planning that are expensive to
rebuild. Deep Agents (LangChain's opinionated harness) packages those
capabilities: planning, filesystem, subagents, skills, memory, HITL interrupts.
But Deep Agents follows a "trust the LLM" model that conflicts with Pepe's
architectural approval tiers, and its tool-calling loop risks error cascades
in financial models.

## Decision

1. **Default inner loop:** hand-rolled bounded ReAct loop, deterministic-first,
   tool-registry-based, step-capped. Always available; no extra dependencies.
2. **Deep Agents:** adopted **only** as a cloud-escalated research worker
   behind a `Worker` Protocol. Never as the default tool-calling loop.
3. **Pattern:** Plan–Execute–Verify for deterministic tasks; deep agents for
   open-ended reconnaissance. Workers return structured outcomes; the
   orchestrator applies them to per-deal state. Workers never mutate deal
   state directly.
4. **Cloud-only:** Deep Agents requires heavy LangGraph/LangChain dependencies.
   It runs only behind the Phase 1.5 sanitiser + `WAITING_FOR_APPROVAL` gate,
   with a structured findings-table output schema, and a max-step cap to bound
   error cascades.
5. **Scope rule:** LLM proposes, code decides. Deep-agent output touching a
   number lands as a proposal, then a deterministic validator (totals tie,
   source lineage) accepts it.

## Consequences

- New `src/pepe/agent/worker.py` defines the `Worker` Protocol with
  `CustomWorker` (default) and `DeepAgentWorker` (optional, cloud).
- New `src/pepe/routing/deepagent_client.py` guards the import; refuses to
  run without `deepagents` installed and the Phase 1.5 gate operational.
- Phase 1.5 is a hard prerequisite for activating Deep Agents in Phase 3.
- `BUILD_VS_BUY.md` and `ROADMAP.md` updated to reflect the split.
- A future ADR is required to lift the Phase 1.5 gate or change the
  cloud-only constraint.

## Alternatives considered

- Deep Agents as the default inner loop — rejected: "trust the LLM" bypasses
  approval tiers; error cascades are unacceptable in financial models.
- Custom-only (no Deep Agents ever) — rejected: ignores real value of free
  context management for research, and leaves Pepe unable to handle the
  open-ended tasks it needs to.
- LangGraph checkpointer as state owner — rejected: conflicts with
  per-deal pepe.db sovereignty.

## Amendment (2026-10-11)

The bounded inner loop's **first step is now always the Von intent
classification** (ADR-0009). The deterministic fast-path survives only as the
`RuleRouter` test fallback and is not a production path. All other decisions
stand: default CustomWorker remains the local bounded loop; DeepAgents is the
optional cloud research worker; the `Worker` Protocol keeps them swappable.
