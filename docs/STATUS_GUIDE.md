# STATUS_GUIDE — What goes in `pepe status` vs `pepe recall`

This is the single source of truth for the per-deal headline surface.

## `pepe status <deal>` — the headline

High-level, scannable. Never a wall of facts.

Always shows:
- `state` — the state machine position (the truth).
- `current_status` — the workspace's human status string.
- `active_tasks` — pending/active/blocked with blocked reasons.
- `facts_count` — number of recorded facts (how much Pepe knows).
- `recent_audit` — last N consequential actions.

Never shows the fact list, the full trajectory, or tool internals.

## `pepe ask <deal> "what is the status…"` — the conversational reply

Sending a status request **as a message** routes through Von to `status_query`
and returns a deterministic, human-readable `reply`, e.g.:

```
[pepe] 1 deal(s) total, 1 active, 1 blocked task(s), 0 pending. Active: atlas.
[pepe] atlas is BLOCKED. Active: wait for management's revised accounts (blocked).
```

Rules:
- If the message names a deal (`atlas`, `the Atlas deal`), the reply is
  **deal-specific** (state + its active/blocked tasks). The JSON `result`
  carries `deal`, `state`, and `active_tasks`.
- Otherwise the reply is **firm-level** (totals + active deal names). JSON
  carries `pipeline` and `active_deals`.
- The current deal is synced to the Core Index before the firm view is read,
  so the reply always reflects the latest per-deal state.
- The reply is printed to **stderr** (`[pepe] …`), so `pepe ask` stdout stays
  pure JSON for machines.
- The reply is deterministic — no LLM is involved.

## `pepe recall <deal>` — the memory

What Pepe knows about the deal, in insertion order (what it learned first,
first). This is the detail surface. `--json` for scripts.

## `pepe trajectory <deal>` — the steps

The step-by-step run record (classify → tool → …) for a run_id. Use `--run` to
pin a specific run.

## `STATUS.md` — the human view

Generated per deal on every run. Includes the "Deal facts" section (key/value/
source), tasks, and recent audit — because an employee's workspace summary is
the natural place for facts, whereas the chat surface stays terse.

## Why

- Headline surfaces answer "what's happening right now?"
- Detail surfaces answer "what do we know?" and "what did we do?"
- Keeping them separate keeps the chat UX employee-like and the audit surface
  honest.
