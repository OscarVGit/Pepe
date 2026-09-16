# Pepe — Agentic Private Equity Associate

# IN PROGRESS - If you are reading this, please follow me on this journey

## This will link into another project I have built in private

> **Pepe is not an AI that you open. Pepe is an AI employee you contact.**

Pepe is a persistent AI junior private-equity associate. You message him
("Pepe, look into this", "Run a downside", "Wait until I get the debt terms"),
he works on it, remembers the deal, asks questions when necessary, waits for
information or approval, and resumes when you respond.

Primary interface (eventually): Telegram → WhatsApp → Slack/Teams/Web.
The messaging interface is only the front door. The product is the persistent
agent + deal/workspace/runtime infrastructure underneath.

## Where to start reading

1. **`docs/VISION.md`** — general statement of what Pepe is and why it exists.
2. **`docs/PRODUCT.md`** — the employee mental model, target UX, MVP, core product test.
3. **`docs/ARCHITECTURE.md`** — system overview and component map.
4. **`docs/ROADMAP.md`** — Phases 0–7, what is built when.
5. **`docs/BUILD_VS_BUY.md`** — compose-don't-recreate matrix and OSS leverage policy.
6. **`docs/adr/`** — binding architectural decisions (0001–0007).

`AGENTS.md` is the entry point for AI coding agents working in this repo.

## Status

Phase 0 — Architecture bootstrap. Interfaces and documentation exist;
deterministic tools, messaging adapters, and model execution arrive in
Phases 1+. See `docs/ROADMAP.md`.

## Layout

```
src/pepe/       Python package (agent, runtime, state, memory, routing, messaging, ...)
docs/           Product + architecture documentation
docs/adr/       Architecture Decision Records
skills/         PE skill definitions (excel, lbo, dcf, ..., 14 total)
tools/          Tool-side specs (excel, python, sql, pdf, powerpoint, web)
tests/          unit / integration / agent / messaging / excel / fixtures
examples/project-atlas/  Canonical Monday→Friday deal walkthrough
deals/          Runtime deal workspaces (gitignored contents, never commit live deals)
scripts/        Dev utilities
```

## Principles (short)

- **Local-first. Cloud-escalated. Privacy-preserving. Deterministic where possible. Human-approved when necessary.**
- **Compose, don't recreate.** Thin where OSS exists; deep where PE intelligence is required.
- **Deterministic tools calculate; the LLM orchestrates, reasons, explains.**
- **Never fabricate financial data. Never pretend unvalidated work is complete.**
- **Audit everything consequential.**

## Quickstart (Phase 1)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,excel,local]"
pip install litequeue PyMuPDF typer httpx
python -m compileall src
pytest -q
```

## Try it

```bash
# 1. Create a deal workspace + inspect a model
python -m pepe ask atlas "inspect models/base_lbo.xlsx"

# 2. Block the runtime on external info
python -m pepe ask atlas "wait for bridge"

# 3. Confirm the blocked state survives a "restart"
python -m pepe status atlas
python -m pepe status atlas --md      # rendered STATUS.md

# 4. Resume (unblocks + continues)
python -m pepe resume atlas --message "bridge received"

# 5. Run the Monday→Friday walkthrough
python -m pytest tests/integration -q
```

See `examples/project-atlas/README.md` for the target UX walkthrough.
