# SECURITY — Baseline Controls

- Auth: messaging allowlist (Telegram user IDs), no open bot.
- Secrets: env-only, never in repo/logs; `.env` gitignored.
- Execution: sandbox untrusted docs; timeouts + output-size caps on tools;
  no shell interpolation of model output.
- MCP: least-privilege servers, pinned tool definitions (rug-pull tripwire),
  per-call policy (allow/deny/redact/require_approval), OAuth scopes minimal.
- Audit logs append-only; access-separated (ops vs investigations); retention
  policy defined before Phase 2.
- EU AI Act / SOC 2 evidence export is a Phase 4+ concern; keep the audit
  schema stable now so evidence exists later.
