# HUMAN_IN_LOOP — Approval Boundaries

- **Low-risk (auto):** read files, extract, calculate, run Python, inspect
  Excel, reconcile, draft analysis.
- **Medium-risk (execute + report):** modify working model, update assumptions,
  create outputs, change deck content.
- **High-risk (explicit approval):** send external comms, delete files,
  overwrite originals, commit investment conclusions, distribute IC materials,
  external transactions, irreversible changes.

Cloud escalation of non-`APPROVED_CLOUD` data is at least medium (report what
was sent) and high when `CONFIDENTIAL/RESTRICTED` ("I can send a de-identified
representation to the approved provider. Proceed?"). Approval recorded in audit.
Enforced in `agent/policy.py` + gateway policy file — never prompt-only.

The Von intent router may classify an `approval_response` intent ("yes/no/go
ahead"), but the **grant** is a deterministic, guarded state transition that is
valid only when a task is actually `WAITING_FOR_APPROVAL`. The router never
approves; it only routes. See ADR-0009.
