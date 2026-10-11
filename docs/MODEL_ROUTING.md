# MODEL_ROUTING — Von-First Intent Routing, Deterministic Execution

Every inbound message passes through **Von**, the System 1 intent router,
before any tool runs. Von classifies the message into one of the intents in
`intents.json`. The router never computes, never writes, never approves, never
gates privacy — it only decides *which* handler receives the message.

## Order of routing decisions

```
inbound message (CLI now, Telegram in Phase 2)
   ↓
1. Von.classify(message, context)         ← the router (System 1)
   → intent label + calibrated confidence + probabilities
   ↓
   confidence >= threshold AND intent != "unclear"
     ├── yes → dispatch to intent handler → deterministic tool / state
     └── no  → WAITING_FOR_INFORMATION: Pepe asks the user to disambiguate
   ↓
2. Deterministic execution                ← the tool does the work
   (finance IRR/MOIC/CAGR, Excel/PDF read, state transitions)
   ↓
3. Reasoning escalation (only for open-ended intents)
   research / long_horizon_task / run_analysis → bounded inner loop →
   local LLM (Ollama) or sanitised cloud, approval-gated.
```

## The router

- `src/pepe/routing/intent.py` — `IntentRouter` Protocol, `IntentResult`,
  `FakeRouter` (deterministic test double).
- `src/pepe/routing/von_router.py` — `VonRouter`: in-process `von-sdk`
  (default). Reads the taxonomy from `intents.json`.
- `src/pepe/routing/von_http_router.py` — `VonHttpRouter`: talks to a
  sidecar `von serve` at `/v1/systemone` (multi-process / Phase 2).

`PEPE_ROUTER` selects the implementation: `von` (default), `von-http`,
`fake`. `RuleRouter` is a documented degraded fallback only, never a
production path.

## What Von is not

- **Not a calculator.** IRR/MOIC/CAGR/debt schedules are deterministic
  (`src/pepe/finance/`). Von only routes to them.
- **Not a writer of record.** The audit log and deal state are written by
  code, never by the router's output.
- **Not an approver.** Approvals are architectural (`agent/policy.py`); the
  router may classify an `approval_response` intent, but the grant is a
  deterministic, guarded state transition.
- **Not a privacy gate.** Sanitisation and the cloud-escalation gate are
  deterministic and fail-closed (ADR-0007).

## Confidence gating and abstention

- Default threshold: **0.80** (Von's measured Choice gate on JevBench).
- Below threshold or `unclear` intent → `WAITING_FOR_INFORMATION` with a
  clarifying question. Never silently guess.
- The threshold is retuned in Phase 1.5 by `pepe calibrate` on a labelled PE
  message set.

## Caveats recorded

- **English only.** Non-English input gets token overlap with unearned
  confidence.
- **Calibration is distribution-specific.** The shipped map is
  JevBench-shaped; PE phrasing needs `pepe calibrate`.
- **Selects/scores, never generates.** Any open-ended synthesis is the inner
  loop's job, not the router's.

See ADR-0009 for the decision record, `docs/HOSTING.md` for hosting, and
`docs/VON_DEPLOYMENT.md` for deployment diagrams.
