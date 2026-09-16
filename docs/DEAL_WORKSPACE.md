# DEAL_WORKSPACE — The Fundamental Unit

Each deal is a persistent workspace:

```
Deal/
├── documents/      CIM, term sheets, transaction docs (immutable inputs)
├── models/         original.* (immutable) + working copies + versioned outputs
├── research/       market / diligence notes
├── presentations/  IC decks (versioned)
├── outputs/        memos, sensitivities, exports
├── assumptions/    agreed assumption log (source + date + owner)
├── memory/         deal facts (JSON)
├── tasks/          task list + status
├── sources/        extraction lineage (doc → value → cell)
├── approvals/      approval records
├── logs/           run logs
└── state/          SQLite store + state machine snapshots
```

Conversation ↔ deal binding lives in `memory/` + `state/`. Current-deal pointer
(default deal per user) avoids re-explaining context. `workspace/deal.py`
defines `create/open/snapshot`. Live contents under `deals/` are gitignored.
