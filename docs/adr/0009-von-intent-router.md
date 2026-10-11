# ADR-0009 — Universal System 1 Intent Router (Von)

- Status: Accepted
- Date: 2026-10-11

## Context

Pepe needs a fast "System 1" layer that decides what kind of work an inbound
message represents before any tool runs. The previous design used hand-written
regexes in `cli.py::_run_one_step`. Regexes are brittle: they cannot tell
"Pepe, run a downside" from "Pepe, run the LBO with a lower exit multiple"
without an ever-growing list of patterns. A full LLM call to classify intent
is too slow and too expensive for the hot path. What is needed is a small,
local, promptable classifier: a **System One decision model**.

`wfzyx/von` is an open-source, non-autoregressive decision model (395M
ModernBERT-large + Option-Marker head, Apache-2.0). It answers Choice / Noul /
Score questions over a JSON or text state in a single forward pass (~96 ms p50
on a 4-vCPU CPU, ~23 ms on GPU), with calibrated confidence. Intents are
supplied as described options at query time, so **no training or labelling is
required to add a new intent**. Its `/v1/systemone` wire protocol is
byte-compatible with TypeSafe Jev.

## Decision

1. **Von is the universal intent router.** Every inbound message — CLI now,
   Telegram in Phase 2 — is classified by Von before any tool runs. This is
   the only place a model is permitted to look at a message before tool
   execution.
2. **The intent taxonomy lives in `intents.json`** at the repo root (a JSON
   file), not in Python source. This makes intents versionable, greppable,
   and trivially loadable into a database later. `src/pepe/routing/von_router.py`
   reads it at startup.
3. **Routing is probabilistic; execution is deterministic.** Von decides
   *which* intent/handler; deterministic tools and state transitions do the
   arithmetic and the mutation. Von never computes a number, never writes a
   record, never approves an action, never gates privacy.
4. **Confidence-gated abstention.** Von's Choice returns a calibrated
   confidence. Below the threshold (default `0.80`) or on an explicit
   `unclear` intent, Pepe asks the user to disambiguate (`WAITING_FOR_INFORMATION`)
   rather than guessing. This is an employee behaviour, and it requires no LLM.
5. **Evals by design.** Every classification writes an audit row
   (`router.served_by`, top-3 probabilities, confidence, message digest). A
   proper evaluation harness is deferred but the audit schema is built to
   support it (labels can be joined against decisions).
6. **Reliance on Von.** We rely on Von for the hot path; we do not maintain a
   first-class parallel rule-based router. For tests, `FakeRouter` (a
   deterministic test double) is injected via `PEPE_ROUTER=fake` or
   `--router=fake` so CI never downloads the model. If Von errors at runtime,
   the message is not dropped: the outcome is recorded as blocked with reason
   `router_error` and audited.
7. **Calibration is deferred to Phase 1.5.** The shipped confidence map is
   JevBench-shaped and does not carry to PE phrasing; `pepe calibrate` (Phase
   1.5) refits it on a labelled PE message set.
8. **Hosting.** Default is **in-process** (`von-sdk` loaded inside the Pepe
   process). An optional **sidecar** (`von serve` exposing `/v1/systemone`) is
   supported via `VonHttpRouter` for multi-process deployments. See
   `docs/HOSTING.md` and `docs/VON_DEPLOYMENT.md`.

## Alternatives considered

- **Regex only** — rejected: brittle, no semantic generalisation.
- **LLM-as-router (Ollama) on the hot path** — rejected: slow, costly, and Von
  is purpose-built for exactly this.
- **Embedding-based router (Aurelio semantic-router)** — viable but does not
  give calibrated Choice-style probabilities out of the box; kept as a future
  "router lite" option.
- **Train a custom classifier** — rejected: cold-start labelling burden; Von is
  promptable so we get the same benefit without labels.
- **Strong-AI-Lab/Von** (research assistant) — different project, not the
  decision model.

## Consequences

- `pyproject.toml`: `von-sdk>=1.3.7` added to `dependencies`; `router-cpu`
  (OpenVINO) and `router-gpu` (CUDA) extras added.
- New `intents.json` at repo root.
- New modules: `routing/intent.py`, `routing/von_router.py`,
  `routing/von_http_router.py`.
- `agent/inner_loop.py`'s first step is always the router classification.
- `agent/trajectory.py` + audit rows carry router metadata.
- ADR-0008 (`inner-worker.md`) is amended: the loop's first step is the router;
  the deterministic fast-path survives only as `RuleRouter` for tests and is
  not a production path.
- Tests use `FakeRouter`; CI never downloads Von weights.
