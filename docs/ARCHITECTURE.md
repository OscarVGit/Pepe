# ARCHITECTURE — Runtime Pipeline and Components

## Pipeline

```
USER MESSAGE → MESSAGE ADAPTER → PEPE RUNTIME → LOAD DEAL STATE → UNDERSTAND
  → PLAN → EXECUTE TOOLS → UPDATE STATE → WAIT/CONTINUE/ASK → SEND MESSAGE
```

The agent starts, continues, pauses, waits (information / approval / schedule /
event), resumes after hours or days, and reports progress. See `AGENT_STATE.md`.

## Components (`src/pepe/`)

- `runtime/loop.py` — persistent loop; entry point `handle_message()`.
- `state/machine.py` — 10-state machine + SQLite persistence.
- `workspace/deal.py` — one workspace per deal (see `DEAL_WORKSPACE.md`).
- `memory/api.py` — conversation / deal / institutional / working-state / audit.
- `agent/policy.py` — low/medium/high approval tiers (architectural).
- `messaging/base.py` — `MessageChannel` Protocol; Telegram first, others adapters.
- `tools/excel_api.py` — granular Excel ops; deterministic finance in code.
- `skills/base.py` — skill manifest contract.
- `routing/router.py` — deterministic-first → local → sanitised-cloud routing.
- `privacy/sanitise.py` — classification + local sanitisation before any cloud call.
- `audit/record.py` — hash-chained JSONL audit records.

## OpenCode relationship

Hypothesis (ADR-0002): Pepe is the PE brain + persistent state; OpenCode-like
capabilities (Python/Excel/SQL/filesystem/PDF/PPT execution) are the hands,
consumed via composition (subprocess / MCP / adapters) — not a hard fork.
Prefer upstream → configure → extend → wrap → contribute → fork-last so Pepe
absorbs upstream improvements.

## Data flow (hybrid inference)

Deterministic tool? → use code. Else local model (Ollama/MLX, OpenAI-compat).
Else sanitise locally → minimum-necessary abstracted payload → approved
frontier → result returns locally. Sensitive/unabstractable → keep local or
`WAITING_FOR_APPROVAL`. See `MODEL_ROUTING.md`, `PRIVACY.md`.
