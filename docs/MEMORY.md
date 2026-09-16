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
