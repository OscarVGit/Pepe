# AGENTS.md — Working in the Pepe Repository

This file tells AI coding agents (and humans) how to work in this repo.

## 1. What Pepe is (read first)

1. `docs/VISION.md` — why Pepe exists, employee-not-app distinction.
2. `docs/PRODUCT.md` — mental model, example interaction, MVP, core product test.
3. `docs/ARCHITECTURE.md` — runtime pipeline, components, OpenCode relationship.
4. `docs/ROADMAP.md` — what phase we are in and what comes next.
5. `docs/adr/` — binding decisions. Do not casually contradict an ADR; propose a new one instead.

## 2. What must not be changed casually

- Deal state must survive restarts (SQLite + JSON files). Never store authoritative state only in LLM context.
- Never overwrite `original.*` model files. Copy-on-write → working copy → validation → versioned output.
- Approval tiers (low/medium/high) are architectural (`src/pepe/agent/policy.py`), not prompt suggestions.
- Privacy: raw deal data stays local by default. Sanitisation happens **inside** the private environment **before** any cloud call. Never send a CIM to a cloud model to be anonymised.
- Deterministic finance (IRR, MOIC, debt schedules) lives in code, not in LLM arithmetic.
- Every consequential action needs an audit record (`src/pepe/audit/record.py`).

## 3. Build philosophy

**Compose, don't recreate.** Before building a subsystem, check `docs/BUILD_VS_BUY.md`.
Preferred order: use upstream → configure → extend → wrap/adapter → contribute upstream → fork last.
If you fork, document why, what changed, and how upstream updates flow back.

## 4. Conventions

- Python 3.12+, `src` layout, hatchling. `pip install -e ".[dev]"`.
- Interfaces as `Protocol`/`dataclass`/`Enum` stubs in Phase 0; raise `NotImplementedError` where unimplemented.
- Skills: one dir per skill in `skills/<name>/SKILL.md` with purpose/when/inputs/tools/outputs/validation/approvals/failures.
- Tools: granular Excel ops (see `docs/EXCEL.md`), never one giant `edit_excel()`.
- Tests mirror `src/pepe/`: `tests/unit|integration|agent|messaging|excel|fixtures`.
- Never commit live deal contents under `deals/`.

## 5. Adding an intent

Von classifies every inbound message against the taxonomy in `intents.json`
at the repo root. To add an intent:

1. Edit `intents.json`: add `"label": "description"` under `intents`. The
   description is what Von matches against; write it for the router, not the
   tool.
2. In `src/pepe/agent/inner_loop.py::_dispatch_intent`, add a `case` mapping
   the label to a handler.
3. If the intent needs a new tool, follow "Adding a tool" (§6).
4. Add a unit test in `tests/unit/test_intent_router.py` using `FakeRouter`.

`FakeRouter` is the deterministic test double; CI never downloads Von. Use
`PEPE_ROUTER=fake` (env) or `--router fake` to force it locally.

## 6. Adding a tool

1. Implement a `ToolSpec` in `src/pepe/tools/built_in.py` (or a new module):
   name, description, risk tier, callable.
2. Register it in `register_builtin_tools()` so the registry sees it.
3. High-risk tools raise `ApprovalRequired` from the registry boundary; the
   orchestrator parks the task in `WAITING_FOR_APPROVAL`.
4. Every tool call is audit-logged with inputs/outputs.

## 7. Current phase

Phase 1 — local agent. Deterministic finance lib + tool registry + bounded
inner loop + Von intent router. Do not build full tools beyond the registry,
do not hard-fork OpenCode/LangGraph, keep heavy deps out of the default install
except `von-sdk`.

## 8. Verification

After changes: `python -m compileall src` and `pytest -q`. All tests run with
`FakeRouter`; CI must never download Von weights.
