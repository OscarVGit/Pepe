# AGENT_STATE — Explicit State Machine

States: `IDLE, UNDERSTANDING, PLANNING, EXECUTING, WAITING_FOR_INFORMATION,
WAITING_FOR_APPROVAL, VALIDATING, BLOCKED, SCHEDULED, COMPLETE, FAILED`.

Core loop: `EXECUTING → WAITING_FOR_INFORMATION → (user responds) → EXECUTING
→ VALIDATING → COMPLETE`. Cloud escalation pauses in `WAITING_FOR_APPROVAL`.

Rules:

- Every transition validated against `TRANSITIONS` (`state/machine.py`).
- State persisted to SQLite synchronously before continuing (durable execution);
  in-memory only is a dev error.
- Waiting states carry `reason + needed_input + resume_plan` so Pepe resumes
  after hours/days without re-asking.
- `SCHEDULED` backs Phase 5 triggers ("remind me when…").
- `FAILED` requires reason + next-step proposal, never silent.
