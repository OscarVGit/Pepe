"""Typer CLI for Pepe Phase 1.

Commands:

    pepe ask <deal_id> <message>    ingest a message; creates deal if missing
    pepe status [deal_id]           per-deal or firm-level status
    pepe resume <deal_id>           unblock blocked tasks and continue
    pepe sync                       rebuild the firm-level Pepe Core Index
    pepe list                       list all deals
    pepe pipeline                   firm-level pipeline summary

The runtime loop is intentionally short: one message → one tool step → exit.
State survives restarts via pepe.db and queue.db. After every mutation the
per-deal state is auto-synced into the firm-level Pepe Core Index.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import typer

from .audit.record import AuditRecord, recent, record
from .core_index import sync_all, sync_deal
from .core_index.query import (
    global_search,
    list_active_deals,
    list_deals,
    pipeline_summary,
)
from .agent.inner_loop import InnerLoop
from .agent.trajectory import read_trajectory
from .export.markdown import generate_status_md
from .memory.store import list_facts
from .routing.factory import make_router
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
REPO_ROOT_MARKER = "pepe.db"  # distinguishes repo root from deals/


def _resolve_roots(deals_root: Path) -> tuple[Path, Path]:
    """Return (deals_root, repo_root).

    If `deals_root` is the literal `deals/` directory inside a repo, the repo
    root is its parent. If the user explicitly passes a deeper path, the repo
    root defaults to the cwd (where pepe.db is expected).
    """
    repo_root = deals_root.parent if deals_root.name == "deals" else Path.cwd()
    return deals_root, repo_root


def _deals_root(ctx: typer.Context) -> Path:
    root: Optional[Path] = ctx.obj.get("deals_root") if ctx.obj else None
    if root is not None:
        return root
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


def _auto_sync(deals_root: Path, deal_id: str) -> None:
    """Push the deal's state into the firm-level Pepe Core Index."""
    _, repo_root = _resolve_roots(deals_root)
    try:
        sync_deal(repo_root, deal_id)
    except Exception:
        # Index is a mirror — never fail a primary operation because sync failed.
        pass


# --------------------------------------------------------------------- ask


@app.command()
def ask(
    deal_id: str = typer.Argument(..., help="Deal identifier (creates if missing)."),
    message: str = typer.Argument(..., help="User message to process."),
    model: str = typer.Option("qwen3:8b", "--model", "-m", help="Ollama model name."),
    ollama_url: str = typer.Option("http://localhost:11434/v1", "--ollama-url"),
    router: Optional[str] = typer.Option(None, "--router", "-r", help="Intent router: von | von-http | fake. Defaults to PEPE_ROUTER env (or 'von')."),
    deals_root: Path = typer.Option(DEALS_ROOT_DEFAULT, "--deals-root"),
) -> None:
    """Process one user message through the Von intent router and inner loop.

    The first step is always intent classification (Von). Terminal intents
    dispatch to deterministic tools; open-ended intents escalate to the
    bounded reasoning loop. Every step is audited and recorded in a trajectory.
    """
    root = deals_root
    p_db = root / deal_id / "state" / "pepe.db"

    if not p_db.exists():
        typer.echo(f"[new deal] creating workspace for {deal_id}", err=True)
        ws = create(root, deal_id, name=deal_id)
    else:
        ws = open_deal(root, deal_id)

    record(root, AuditRecord.now(deal_id, "message_received", text=message))

    conn, lock = get_pepe_db(root, deal_id)
    # A new message after a finished/failed task resets the deal to IDLE so the
    # state machine can advance again.
    current = load_state(conn, lock, deal_id)
    if current in (AgentState.COMPLETE, AgentState.FAILED):
        _safe_transition(conn, lock, deal_id, AgentState.IDLE, reason="new message on finished deal")
    _safe_transition(conn, lock, deal_id, AgentState.UNDERSTANDING, reason="message received")
    _safe_transition(conn, lock, deal_id, AgentState.PLANNING, reason="routing intent")

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

    # Route + execute via the inner loop (Von first).
    loop = InnerLoop(root, deal_id, router=make_router(router),
                     model=model, ollama_url=ollama_url)
    outcome = loop.run(message, context={"deal_id": deal_id})

    # Audit the outcome, including router metadata from step 0.
    router_meta = outcome.steps[0].router if outcome.steps else None
    record(root, AuditRecord.now(
        deal_id, "task_outcome",
        outcome=outcome.kind, reason=outcome.reason, result=outcome.result,
        router=router_meta, run_id=outcome.run_id,
    ))

    if outcome.kind == "complete":
        complete(root, deal_id, task.queue_message_id, task.claim_id)
        record(root, AuditRecord.now(deal_id, "task_complete", description=task.description))
        _safe_transition(conn, lock, deal_id, AgentState.VALIDATING, reason="outcome recorded")
        _safe_transition(conn, lock, deal_id, AgentState.COMPLETE, reason="task complete")
    elif outcome.kind == "waiting":
        block(root, deal_id, task.queue_message_id, task.claim_id, reason=outcome.reason)
        record(root, AuditRecord.now(deal_id, "task_blocked", reason=outcome.reason))
        _safe_transition(conn, lock, deal_id, AgentState.WAITING_FOR_INFORMATION,
                         reason=outcome.reason)
    elif outcome.kind == "needs_approval":
        record(root, AuditRecord.now(deal_id, "task_needs_approval", reason=outcome.reason))
        _safe_transition(conn, lock, deal_id, AgentState.WAITING_FOR_APPROVAL,
                         reason=outcome.reason)
    elif outcome.kind == "blocked":
        block(root, deal_id, task.queue_message_id, task.claim_id, reason=outcome.reason)
        record(root, AuditRecord.now(deal_id, "task_blocked", reason=outcome.reason))
        _safe_transition(conn, lock, deal_id, AgentState.BLOCKED, reason=outcome.reason)
    else:  # failed
        record(root, AuditRecord.now(deal_id, "task_failed", reason=outcome.reason))
        _safe_transition(conn, lock, deal_id, AgentState.FAILED, reason=outcome.reason)

    # Refresh human-readable status view.
    generate_status_md(ws)

    # Auto-sync into the firm-level Pepe Core Index (best-effort, never fatal).
    _auto_sync(root, deal_id)

    # A deterministic `reply` string (when handlers produce one) is the
    # conversational answer. It goes to stderr so stdout stays pure JSON for
    # machines; humans see it in the terminal as the "Pepe said" line.
    reply = outcome.result.get("reply") if isinstance(outcome.result, dict) else None
    if reply:
        typer.echo(f"[pepe] {reply}", err=True)
    typer.echo(json.dumps({
        "outcome": {"kind": outcome.kind, "reason": outcome.reason, "result": outcome.result},
        "router": router_meta,
        "run_id": outcome.run_id,
        "steps": len(outcome.steps),
        "state": load_state(conn, lock, deal_id).value,
    }, indent=2, default=str))




# --------------------------------------------------------------------- status


@app.command()
def status(
    deal_id: Optional[str] = typer.Argument(None, help="Deal identifier (omit for firm-level)."),
    as_markdown: bool = typer.Option(False, "--md", help="Print STATUS.md instead of JSON."),
    deals_root: Path = typer.Option(DEALS_ROOT_DEFAULT, "--deals-root"),
) -> None:
    """Show per-deal state, active tasks, and recent audit — or firm-level summary if no deal_id."""
    root = deals_root
    if deal_id is None:
        _, repo_root = _resolve_roots(root)
        typer.echo(json.dumps({
            "scope": "firm",
            "summary": pipeline_summary(repo_root),
            "active_deals": list_active_deals(repo_root),
            "all_deals": list_deals(repo_root),
        }, indent=2, default=str))
        return

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
        "facts_count": len(list_facts(root, deal_id)),
        "recent_audit": audit,
    }, indent=2, default=str))


# --------------------------------------------------------------------- recall


@app.command()
def recall(
    deal_id: str = typer.Argument(..., help="Deal identifier."),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON instead of a table."),
    deals_root: Path = typer.Option(DEALS_ROOT_DEFAULT, "--deals-root"),
) -> None:
    """List a deal's known facts in insertion order."""
    root = deals_root
    p = root / deal_id / "state" / "pepe.db"
    if not p.exists():
        # A deal with no workspace yet is fine — no facts.
        if as_json:
            typer.echo(json.dumps([]))
        else:
            typer.echo(f"[info] no facts recorded yet for deal {deal_id}")
        return
    facts = list_facts(root, deal_id)
    if as_json:
        typer.echo(json.dumps([
            {"key": f.key, "value": f.value, "source": f.source, "timestamp": f.timestamp}
            for f in facts
        ], indent=2))
        return
    if not facts:
        typer.echo(f"[info] no facts recorded yet for deal {deal_id}")
        return
    typer.echo(f"# Facts — {deal_id} (insertion order)")
    for f in facts:
        src = f" (source: {f.source})" if f.source else ""
        typer.echo(f"- **{f.key}**: {f.value}{src} — {f.timestamp}")


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
    _auto_sync(root, deal_id)
    if message:
        ask(deal_id, message, deals_root=deals_root)


# --------------------------------------------------------------------- core index


@app.command()
def sync(
    deals_root: Path = typer.Option(DEALS_ROOT_DEFAULT, "--deals-root"),
) -> None:
    """Full scan of all deals and rebuild the firm-level Pepe Core Index."""
    _, repo_root = _resolve_roots(deals_root)
    n = sync_all(repo_root)
    typer.echo(json.dumps({
        "synced": n,
        "summary": pipeline_summary(repo_root),
    }, indent=2, default=str))


@app.command()
def list(
    deals_root: Path = typer.Option(DEALS_ROOT_DEFAULT, "--deals-root"),
) -> None:
    """List all deals known to the firm-level index (newest activity first)."""
    _, repo_root = _resolve_roots(deals_root)
    typer.echo(json.dumps(list_deals(repo_root), indent=2, default=str))


@app.command()
def pipeline(
    deals_root: Path = typer.Option(DEALS_ROOT_DEFAULT, "--deals-root"),
) -> None:
    """Firm-level pipeline summary: counts of deals, active states, blocked tasks."""
    _, repo_root = _resolve_roots(deals_root)
    out = {
        "summary": pipeline_summary(repo_root),
        "active_deals": list_active_deals(repo_root),
    }
    typer.echo(json.dumps(out, indent=2, default=str))


@app.command()
def search(
    query: str = typer.Argument(..., help="Search term (deal name/id or task description)."),
    deals_root: Path = typer.Option(DEALS_ROOT_DEFAULT, "--deals-root"),
) -> None:
    """Cross-deal search across deal names and task descriptions."""
    _, repo_root = _resolve_roots(deals_root)
    typer.echo(json.dumps(global_search(repo_root, query), indent=2, default=str))


@app.command()
def trajectory(
    deal_id: str = typer.Argument(..., help="Deal identifier."),
    run_id: Optional[str] = typer.Option(None, "--run", "-r", help="Run id (default: latest)."),
    deals_root: Path = typer.Option(DEALS_ROOT_DEFAULT, "--deals-root"),
) -> None:
    """Print the step-by-step trajectory of the latest (or given) run."""
    steps = read_trajectory(deals_root / deal_id, run_id=run_id)
    if not steps:
        typer.echo(f"[info] no trajectory found for deal {deal_id}")
        raise typer.Exit(code=1)
    for s in steps:
        idx = s.get("index", "?")
        action = s.get("action", "?")
        router = s.get("router") or {}
        served = router.get("served_by", "")
        conf = router.get("confidence", "")
        note = s.get("note", "")
        tool = s.get("tool", "")
        suffix = ""
        if action == "classify" and served:
            suffix = f"  [{served} conf={conf} -> {s.get('outputs', {}).get('intent')}]"
        elif tool:
            suffix = f"  [{tool}]"
        elif note:
            suffix = f"  [{note}]"
        typer.echo(f"step {idx}: {action}{suffix}")
