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
- `agent/inner_loop.py` — bounded ReAct loop; first step is always the router.
- `agent/schemas.py` — Pydantic TaskOutcome/Step/ToolCall.
- `agent/prompts.py` — system prompt builder.
- `agent/trajectory.py` — per-run trajectory JSONL recorder.
- `messaging/base.py` — `MessageChannel` Protocol; Telegram first, others adapters.
- `tools/registry.py` — `ToolSpec`/`ToolRegistry`; risk-tagged tools.
- `tools/excel_api.py` — granular Excel ops; deterministic finance in code.
- `tools/pdf_api.py` — PyMuPDF read-only PDF.
- `tools/built_in.py` — registers the built-in tools.
- `skills/base.py` — skill manifest contract.
- `routing/intent.py` — `IntentRouter` Protocol, `IntentResult`, `FakeRouter`.
- `routing/von_router.py` — `VonRouter` (in-process `von-sdk`; reads `intents.json`).
- `routing/von_http_router.py` — `VonHttpRouter` (sidecar `/v1/systemone`).
- `routing/router.py` — model routing policy (local vs cloud).
- `routing/local_client.py` — Ollama OpenAI-compat client (httpx).
- `privacy/sanitise.py` — classification + local sanitisation before any cloud call.
- `audit/record.py` — hash-chained JSONL audit records.
- `core_index/` — firm-level Pepe Core Index (`pepe.db` at repo root).

## OpenCode relationship

Hypothesis (ADR-0002): Pepe is the PE brain + persistent state; OpenCode-like
capabilities (Python/Excel/SQL/filesystem/PDF/PPT execution) are the hands,
consumed via composition (subprocess / MCP / adapters) — not a hard fork.
Prefer upstream → configure → extend → wrap → contribute → fork-last so Pepe
absorbs upstream improvements.

## Data flow (Von-first, deterministic execution)

```
inbound message
   ↓
Von.classify(message, context)      (System 1 intent router; the only model
   ↓                                  that sees a message before tools run)
intent + confidence
   ↓
confidence < threshold or intent == "unclear"
   → WAITING_FOR_INFORMATION: Pepe asks the user to disambiguate
   ↓ else
intent handler
   ├── deterministic intent → tool executes in code → audit
   └── open-ended intent (research / long_horizon_task / run_analysis)
       → bounded inner loop → local LLM or sanitised cloud → audit
```

Deterministic tool? → code (finance/Excel/PDF). Open-ended? → bounded inner
loop → local LLM (Ollama/MLX, OpenAI-compat) → else sanitise locally →
minimum-necessary abstracted payload → approved frontier → result returns
locally. Sensitive/unabstractable → keep local or `WAITING_FOR_APPROVAL`.
See `MODEL_ROUTING.md`, `PRIVACY.md`, ADR-0009.
