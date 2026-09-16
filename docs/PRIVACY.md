# PRIVACY — Raw Deal Data Stays Local by Default

## Classification (configurable)

`PUBLIC < INTERNAL < DEAL_SENSITIVE < CONFIDENTIAL < RESTRICTED (local-only
unless explicit approval)`. `APPROVED_CLOUD` marks payloads cleared for
sanitised escalation.

## Rules

- Sanitisation happens **inside** the private environment **before** any cloud
  call — deterministic templating primary ("Atlas" → "Company A", preserve
  numbers), Presidio-style NER secondary.
- Never send a CIM to be anonymised remotely. Send abstracted numerical
  problems, not source documents.
- Small-universe warning: revenue + EBITDA + multiple can re-identify a deal —
  default narrow deals to `RESTRICTED`.
- Scanner failure = fail closed (block, ask user).

## Risks documented

Re-identification via quasi-identifiers; provider retention/logging; tool
permissions; malicious docs / prompt injection; exfiltration via tool args
(MCP request+response filtering per `mcp-gate`/`AegisGate` patterns).
