# MEMORY — Five Separate Concepts

- **Conversation Memory** — recent turns per conversation (short-lived).
- **Deal Memory** — per-transaction facts (entry 8.5x, mgmt EBITDA $42m,
  normalisation $3.2m, debt pending, IC preliminary). Source-labelled.
- **Institutional Memory** — firm-wide: modelling conventions, IC memo
  structure, house assumptions, return definitions, approved sources, criteria,
  formatting.
- **Working State** — what Pepe is doing now: current task, outstanding items,
  blockers, next planned action.
- **Audit History** — what Pepe did: append-only, hash-chained, tamper-evident.

Built on SQLite + JSON files (Phase 1); vector/semantic stores investigated
later for retrieval — semantics (the five splits) are Pepe's layer, not the DB.

## Wired vs deferred

| Concept | Status (Phase 1) | Storage |
|---|---|---|
| Deal Memory | **Wired** — deterministic tool outputs only; `pepe recall <deal>` lists facts in insertion order; overwrite + audit | `facts` table in per-deal `pepe.db` |
| Working State | **Wired** — tasks + state machine drive it | `tasks` + `state_transitions` |
| Audit History | **Wired** — every consequential action is an `AuditRecord` | `audit_log` + `audit.jsonl` |
| Conversation Memory | Deferred — needs message-history table | Phase 2 (with messaging) |
| Institutional Memory | Deferred — needs a knowledge-editor surface | Phase 7 |

## Deal facts rules

- **Deterministic only.** Facts come from tool outputs, never LLM extraction.
- **Allowlist.** `memory/allowlist.py` is the single source of truth. Anything
  off-list is ignored and audited as `fact_skipped`.
- **Overwrite + audit.** Recomputing a fact overwrites it and writes a
  `fact_overwritten` row with old and new values.
- **Insertion order.** `pepe recall` lists facts in the order they were
  learned. Rework later to rank by deal-relevance if needed.
- **Importance** is currently implicit (insertion order). A separate
  `docs/STATUS_GUIDE.md` defines what `pepe status` vs `pepe recall` surface.
