# ROADMAP — Phases 0–7

- **Phase 0 — Architecture:** repo, docs, ADRs 0001–0008, interface stubs,
  Atlas example. No heavy deps, no forks. Exit: `compileall` + `collect-only` green.
- **Phase 1 — Local Agent:** persistent runtime + SQLite/JSON state, deal
  workspace CRUD, task tracking, basic memory, filesystem + Python tools,
  local model via OpenAI-compat (Ollama), classification stubs, deterministic
  finance lib. **Pepe Core Index** at repo root: deal registry + global
  tasks mirror + user prefs; `pepe sync/list/pipeline/search` commands;
  auto-sync on every mutation.
- **Phase 1.5 — Hybrid escalation (prerequisite for Phase 3):** sanitiser
  (deterministic templating + Presidio), LiteLLM-compatible gateway client,
  approval-gated cloud path, escalation audit. **Hard prerequisite for Phase
  3 deep-agent activation.**
- **Phase 2 — Messaging:** Telegram adapter (polling) first; user↔agent and
  conversation↔deal binding; async updates. WhatsApp second; Slack/Teams/Web
  later. Core Index queries (`pepe pipeline`, `pepe status` with no deal_id)
  become the user-facing summary across all deals.
- **Phase 3 — Financial Analyst + bounded deep-agent worker:** CIM
  extraction, Excel inspection, financial extraction/reconciliation,
  LBO/DCF/scenarios, validation tooling. **Add bounded deep-agent worker for
  open-ended diligence/research (cloud-only, behind Phase 1.5 sanitiser +
  approval gate).** Deterministic tools remain default for all financial
  operations and all tool calling.
- **Phase 4 — PE Associate:** PowerPoint + IC memo, research/diligence
  workflows (deep-agent worker active here), deal memory, approval
  workflows, full audit.
- **Phase 5 — Autonomous Worker:** schedules, events, waiting states,
  background execution, proactive notifications, email/calendar.
  `pepe sync --watch` becomes a file-system watcher feeding the Core Index.
- **Phase 6 — Portfolio Associate:** company workspaces, recurring reporting,
  variance/covenant/KPI monitoring, board materials.
- **Phase 7 — Firm Intelligence:** cross-deal institutional memory layer,
  backed by `pepe.db` `institutional_knowledge` table (seeded in Phase 1).
