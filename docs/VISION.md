# VISION — Why Pepe Exists

**General statement of understanding:** Pepe is a persistent AI junior
private-equity associate that a deal professional contacts over messaging.
Pepe maintains deal context across days, performs multi-step analytical work on
real artifacts (CIMs, models, accounts, decks), waits for information or
approval when needed, and resumes correctly — behaving like an employee, not an
app you open.

## The distinction that matters

| Traditional AI tool | Pepe |
|---|---|
| Chatbot you prompt | Employee you message |
| Session-scoped context | Persistent deal workspace + memory |
| Generates a one-off LBO | Maintains a live model across a week of instructions |
| You re-explain the deal each time | Pepe remembers entry thesis, assumptions, blockers |
| Calculations in LLM prose | Deterministic code calculates; LLM orchestrates and explains |

## Cascading importance (read top-down)

1. **Employee UX** — "Pepe, work on Atlas." Simple messaging front door; all
   complexity (identity, memory, state, approvals, Excel, routing, privacy)
   lives underneath. If Pepe cannot hold context across days, nothing else matters.
2. **Persistent deal truth** — one workspace per deal, surviving restarts
   (SQLite + JSON). State must never depend on an LLM context window.
3. **Trustworthy finance** — deterministic computation (IRR, MOIC, schedules)
   in code; copy-on-write model handling; audit trail; facts vs assumptions
   always distinguished; never fabricate.
4. **Local-first privacy** — raw deal data stays local; cloud escalation only
   with locally-sanitised, minimum-necessary payloads under policy + approval.
5. **Composable execution** — thin PE orchestration over mature OSS (OpenCode /
   LangGraph patterns, MCP, openpyxl, DuckDB, LiteLLM-style routing). Pepe's
   moat is deal context, institutional memory, and workflow reliability — not
   another agent framework.

## End state

A firm's persistent institutional intelligence layer: every deal, portfolio
company, IC discussion, and historical decision accumulated into memory Pepe can
draw on — while each deal's confidential data remains controlled.
