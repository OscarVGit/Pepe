# BUILD_VS_BUY — Compose, Don't Recreate

Living matrix. Default: use upstream → configure → extend → wrap/adapter →
contribute → fork last. Forks document why/what/updates/compat.

| Capability | Ecosystem | Default | Pepe layer |
|---|---|---|---|
| Agent runtime | OpenCode (Effect-kernel, Bun; session loop, MCP client, permissions), LangGraph (checkpointer/store, durable execution, interrupts) | Integrate patterns, no hard dep P0 | PE orchestration, state machine, approvals |
| Tool protocol | MCP Python SDK (`FastMCP`), existing Excel/data servers | Integrate | PE tools + financial semantics |
| Excel | openpyxl (now), xlwings/COM, LibreOffice, Excel MCP servers | Integrate | Model semantics (multiples, sweep, schedules) |
| Python/SQL | pandas, DuckDB/Postgres, OpenBB (investigate) | Integrate | Deterministic finance lib |
| PDF/docs | pypdf/pdfplumber, OCR, python-docx | Integrate | CIM analysis (doc→deal-fact lineage) |
| PowerPoint | python-pptx | Integrate | Slide-registry (deal-change → slides) |
| Messaging | python-telegram-bot (polling), WhatsApp Cloud API, slack-bolt socket | Integrate | `MessageChannel` adapter + deal binding |
| Scheduling | cron/APScheduler/temporal-style queues (investigate P5) | Investigate | Task semantics (wait/resume/notify) |
| Models | Ollama, MLX, OpenAI-compat servers | Integrate | Routing policy |
| Routing/gateway | LiteLLM Router/Proxy (fallbacks, budgets), RouteLLM weak-vs-strong | Wrap | PE policy + confidence thresholds |
| Privacy/PII | Presidio (analyzer+anonymizer), CloakLLM tokenization, AegisGate/mcp-gate filtering | Wrap | Classification + deterministic templating |
| Policy/audit | OPA/Rego (if firm uses it), hash-chained JSONL → Postgres/SIEM later | Minimal YAML now | Approval tiers + escalation audit |
| Memory | SQLite + JSON (now); Postgres/pgvector, Redis (later, investigate) | Integrate later | 5-memory semantics |

Anti-pattern: `PepeAgentFramework`, `PepeExcelFramework`, `PepeGateway` —
ask "what is the smallest PE layer on top of existing infra?" first.
