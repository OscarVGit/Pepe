# ROADMAP — Phases 0–7

- **Phase 0 — Architecture (now):** repo, docs, ADRs 0001–0007, interface stubs,
  Atlas example. No heavy deps, no forks. Exit: `compileall` + `collect-only` green.
- **Phase 1 — Local Agent:** persistent runtime + SQLite/JSON state, deal
  workspace CRUD, task tracking, basic memory, filesystem + Python tools, local
  model via OpenAI-compat (Ollama), classification stubs, deterministic finance lib.
- **Phase 1.5 — Hybrid escalation (new):** sanitiser (deterministic templating +
  Presidio), LiteLLM-compatible gateway client, approval-gated cloud path, escalation audit.
- **Phase 2 — Messaging:** Telegram adapter (polling) first; user↔agent and
  conversation↔deal binding; async updates. WhatsApp second; Slack/Teams/Web later.
- **Phase 3 — Financial Analyst:** CIM extraction, Excel inspection, financial
  extraction/reconciliation, LBO/DCF/scenarios, validation tooling.
- **Phase 4 — PE Associate:** PowerPoint + IC memo, research/diligence
  workflows, deal memory, approval workflows, full audit.
- **Phase 5 — Autonomous Worker:** schedules, events, waiting states, background
  execution, proactive notifications, email/calendar. E.g. "remind me when
  management sends revised accounts."
- **Phase 6 — Portfolio Associate:** company workspaces, recurring reporting,
  variance/covenant/KPI monitoring, board materials.
- **Phase 7 — Firm Intelligence:** cross-deal institutional memory layer.
