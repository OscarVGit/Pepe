"""Typer CLI for Pepe Phase 1.

Three commands:

    pepe ask <deal_id> <message>    ingest a message; creates deal if missing
    pepe status <deal_id>           show current state, active tasks, recent audit
    pepe resume <deal_id>           unblock blocked tasks and continue

The runtime loop is intentionally short: one message → one tool step → exit.
State survives restarts via pepe.db and queue.db.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import typer

from .audit.record import AuditRecord, recent, record
from .export.markdown import generate_status_md
from .routing.local_client import ChatMessage, ChatRequest, OllamaClient, OllamaUnavailable, is_running
from .state.connection import get_pepe_db
from .state.machine import (
    AgentState, InvalidTransitionError, load_state, save_state,
)
from .state.tasks import (
    block, claim_next, complete, enqueue, list_active, retry_expired, unblock,
)
from .tools.excel_api import inspect_workbook, list_sheets
from .tools.pdf_api import extract_text, list_pages
from .workspace.deal import WORKSPACE_DIRS, create, open as open_deal


app = typer.Typer(add_completion=False, no_args_is_help=True, help="Pepe — agentic PE associate (Phase 1).")
DEALS_ROOT_DEFAULT = Path("deals")


def _deals_root(ctx: typer.Context) -> Path:
    root: Optional[Path] = ctx.obj.get("deals_root") if ctx.obj else None
    if root is not None:
        return root
    # Default: <cwd>/deals if it exists, else literal "deals/" (relative).
    cwd_deals = Path.cwd() / "deals"
    if cwd_deals.exists():
        return cwd_deals
    return DEALS_ROOT_DEFAULT


# --------------------------------------------------------------------- helpers


def _safe_transition(conn, lock, deal_id, to_state: AgentState, reason: str = "") -> bool:
    """Try to save_state; tolerate `IDLE -> IDLE` (re-runs) and skip impossible ones."""
    try:
        save_state(conn, lock, deal_id, to_state, reason=reason)
        return True
    except InvalidTransitionError:
        return False


def _maybe_use_local_model(prompt: str, model: str, base_url: str) -> Optional[str]:
    """Return the model's reply text, or None if Ollama is unreachable."""
    if not is_running(base_url):
        return None
    with OllamaClient(base_url=base_url) as client:
        try:
            return client.chat(ChatRequest(
                model=model,
                messages=[
                    ChatMessage(role="system", content=(
                        "You are Pepe, a junior PE associate. Be concise. "
                        "If you do not know, say so. Never invent financial figures."
                    )),
                    ChatMessage(role="user", content=prompt),
                ],
            ))
        except OllamaUnavailable:
            return None


# --------------------------------------------------------------------- ask


@app.command()
def ask(
    deal_id: str = typer.Argument(..., help="Deal identifier (creates if missing)."),
    message: str = typer.Argument(..., help="User message to process."),
    model: str = typer.Option("qwen3:8b", "--model", "-m", help="Ollama model name."),
    ollama_url: str = typer.Option("http://localhost:11434/v1", "--ollama-url"),
    deals_root: Path = typer.Option(DEALS_ROOT_DEFAULT, "--deals-root"),
) -> None:
    """Process one user message: enqueue task, run one deterministic step (or
    call Ollama for reasoning), record audit, persist, exit."""
    root = deals_root
    p_db = root / deal_id / "state" / "pepe.db"

    if not p_db.exists():
        typer.echo(f"[new deal] creating workspace for {deal_id}", err=True)
        ws = create(root, deal_id, name=deal_id)
    else:
        ws = open_deal(root, deal_id)

    record(root, AuditRecord.now(deal_id, "message_received", text=message))

    conn, lock = get_pepe_db(root, deal_id)
    # Drive the state machine forward. We tolerate impossible transitions (e.g.
    # if a previous run already advanced state) instead of crashing the CLI.
    _safe_transition(conn, lock, deal_id, AgentState.UNDERSTANDING, reason="message received")
    _safe_transition(conn, lock, deal_id, AgentState.PLANNING, reason="planning tool selection")

    # Enqueue the task, then claim it (one-step-at-a-time runtime).
    enqueue(root, deal_id, description=message, payload={"raw": message})
    task = claim_next(root, deal_id)
    if task is None:
        typer.echo("[error] no task available to claim (queue empty?)")
        raise typer.Exit(code=1)

    record(root, AuditRecord.now(deal_id, "task_claimed",
                                 queue_message_id=task.queue_message_id,
                                 description=task.description))
    _safe_transition(conn, lock, deal_id, AgentState.EXECUTING, reason=task.description)

    # Decide: deterministic tool, local model, or wait for info.
    outcome = _run_one_step(root, deal_id, task, message, model=model, ollama_url=ollama_url)
    record(root, AuditRecord.now(deal_id, "task_outcome", outcome=outcome["kind"], **outcome))

    if outcome["kind"] == "tool_result":
        complete(root, deal_id, task.queue_message_id, task.claim_id)
        record(root, AuditRecord.now(deal_id, "task_complete", description=task.description))
        _safe_transition(conn, lock, deal_id, AgentState.VALIDATING, reason="outcome recorded")
        _safe_transition(conn, lock, deal_id, AgentState.COMPLETE, reason="task complete")
    elif outcome["kind"] == "llm_reply":
        complete(root, deal_id, task.queue_message_id, task.claim_id)
        record(root, AuditRecord.now(deal_id, "task_complete", description=task.description))
        _safe_transition(conn, lock, deal_id, AgentState.VALIDATING, reason="LLM reply recorded")
        _safe_transition(conn, lock, deal_id, AgentState.COMPLETE, reason="task complete")
    elif outcome["kind"] == "blocked":
        # Don't complete; mark the task blocked with the reason.
        block(root, deal_id, task.queue_message_id, task.claim_id, reason=outcome["reason"])
        record(root, AuditRecord.now(deal_id, "task_blocked", reason=outcome["reason"]))
        _safe_transition(conn, lock, deal_id, AgentState.WAITING_FOR_INFORMATION,
                         reason=outcome["reason"])
    else:  # unknown
        record(root, AuditRecord.now(deal_id, "task_unhandled", description=task.description))
        _safe_transition(conn, lock, deal_id, AgentState.FAILED, reason="no tool or model handled it")

    # Refresh human-readable status view.
    generate_status_md(ws)
    typer.echo(json.dumps({"outcome": outcome, "state": load_state(conn, lock, deal_id).value},
                          indent=2, default=str))


# --------------------------------------------------------------------- one step


_INSPECT_XLSX = re.compile(r"(?:inspect|list|show)\s+([^\s]+\.xlsx)", re.IGNORECASE)
_INSPECT_PDF = re.compile(r"(?:inspect|extract|read)\s+([^\s]+\.pdf)", re.IGNORECASE)


def _run_one_step(root: Path, deal_id: str, task, message: str,
                  *, model: str, ollama_url: str) -> dict:
    """Return {kind: 'tool_result'|'llm_reply'|'blocked'|'unknown', ...}.

    Phase 1 routing (checked in order):
      1. Explicit "wait/hold" intent  -> blocked
      2. Excel/PDF inspection regex   -> deterministic tool
      3. Local Ollama model           -> llm_reply
      4. Fallback                     -> blocked with "no handler"
    """
    # 1. Explicit block intent. Checked first so we never accidentally send
    #    a "wait for bridge" message to a model and get a hallucinated bridge.
    if re.search(r"\b(wait|hold|pause)\b\s+(for|on|until)\b", message, re.IGNORECASE):
        m = re.search(r"\b(?:for|on|until)\b\s+(.+)$", message, re.IGNORECASE)
        reason = f"awaiting: {m.group(1).strip()}" if m else "awaiting user-provided information"
        return {"kind": "blocked", "reason": reason}

    # 2. Deterministic tools.
    m = _INSPECT_XLSX.search(message)
    if m:
        path = root / deal_id / "models" / Path(m.group(1)).name
        if not path.exists():
            return {"kind": "blocked", "reason": f"missing file: {path}"}
        info = inspect_workbook(path)
        sheets = list_sheets(path)
        return {"kind": "tool_result", "tool": "excel_inspect_workbook",
                "path": str(path), "sheets": sheets,
                "named_ranges": info.named_ranges,
                "sheet_dimensions": info.sheet_dimensions}

    m = _INSPECT_PDF.search(message)
    if m:
        path = root / deal_id / "documents" / Path(m.group(1)).name
        if not path.exists():
            return {"kind": "blocked", "reason": f"missing file: {path}"}
        n = list_pages(path)
        preview = extract_text(path, page_range=(1, min(2, n)))[:2000]
        return {"kind": "tool_result", "tool": "pdf_inspect",
                "path": str(path), "pages": n, "preview": preview}

    # 3. Local model.
    reply = _maybe_use_local_model(message, model=model, base_url=ollama_url)
    if reply:
        return {"kind": "llm_reply", "tool": "ollama", "model": model, "reply": reply}

    # 4. Nothing matched.
    return {"kind": "unknown", "reason": "no tool matched and Ollama not reachable"}


# --------------------------------------------------------------------- status


@app.command()
def status(
    deal_id: str = typer.Argument(..., help="Deal identifier."),
    as_markdown: bool = typer.Option(False, "--md", help="Print STATUS.md instead of JSON."),
    deals_root: Path = typer.Option(DEALS_ROOT_DEFAULT, "--deals-root"),
) -> None:
    """Show current state, active tasks, and recent audit for a deal."""
    root = deals_root
    p = root / deal_id / "state" / "pepe.db"
    if not p.exists():
        typer.echo(f"[not found] deal {deal_id} has no pepe.db under {p}")
        raise typer.Exit(code=1)
    ws = open_deal(root, deal_id)
    conn, lock = get_pepe_db(root, deal_id)
    state = load_state(conn, lock, deal_id)
    active = list_active(root, deal_id)
    audit = recent(root, deal_id, limit=10)
    if as_markdown:
        typer.echo((ws.root / "STATUS.md").read_text())
        return
    typer.echo(json.dumps({
        "deal": deal_id,
        "name": ws.name,
        "root": str(ws.root),
        "state": state.value,
        "current_status": ws.current_status,
        "active_tasks": [
            {"id": t.id, "description": t.description, "status": t.status,
             "blocked_reason": t.blocked_reason}
            for t in active
        ],
        "recent_audit": audit,
    }, indent=2, default=str))


# --------------------------------------------------------------------- resume


@app.command()
def resume(
    deal_id: str = typer.Argument(..., help="Deal identifier."),
    message: str = typer.Option("", "--message", "-m", help="Optional continuation message."),
    deals_root: Path = typer.Option(DEALS_ROOT_DEFAULT, "--deals-root"),
) -> None:
    """Unblock blocked tasks and continue. Optionally pass a follow-up message."""
    root = deals_root
    p = root / deal_id / "state" / "pepe.db"
    if not p.exists():
        typer.echo(f"[not found] deal {deal_id} has no pepe.db")
        raise typer.Exit(code=1)
    ws = open_deal(root, deal_id)
    conn, lock = get_pepe_db(root, deal_id)
    state = load_state(conn, lock, deal_id)
    if state not in {AgentState.WAITING_FOR_INFORMATION, AgentState.BLOCKED}:
        typer.echo(f"[info] deal state is {state.value}; nothing to unblock.")
        if message:
            ask(deal_id, message, deals_root=deals_root)
        return

    # Recover any expired claims first.
    recovered = retry_expired(root, deal_id, threshold_seconds=0)
    if recovered:
        record(root, AuditRecord.now(deal_id, "expired_claims_recovered", count=recovered))

    # Unblock each blocked task in the pepe.db view.
    unblocked = 0
    for t in list_active(root, deal_id):
        if t.status == "blocked":
            ok = unblock(root, deal_id, t.queue_message_id)
            if ok:
                record(root, AuditRecord.now(deal_id, "task_unblocked",
                                             description=t.description,
                                             was_blocked_on=t.blocked_reason))
                unblocked += 1
    typer.echo(f"[resume] unblocked {unblocked} task(s); recovered {recovered} expired claim(s).")
    _safe_transition(conn, lock, deal_id, AgentState.EXECUTING, reason="user resumed")
    generate_status_md(ws)
    if message:
        ask(deal_id, message, deals_root=deals_root)
