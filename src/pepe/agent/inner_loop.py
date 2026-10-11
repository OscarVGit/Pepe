"""Bounded inner loop.

The first step is always the intent classification (Von via `IntentRouter`).
Terminal intents dispatch to deterministic tools and finish. Open-ended
intents (`run_analysis`, `research`, `long_horizon_task`, `question`) escalate
to a bounded ReAct loop that reasons with a local LLM and calls registered
tools, with a hard step cap.

Workers never mutate deal state directly. The loop returns a `TaskOutcome`;
the orchestrator applies it to pepe.db.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Optional

from ..audit.record import AuditRecord, record
from ..core_index import sync_deal
from ..memory.allowlist import allowed_key
from ..memory.store import list_facts, save_fact
from ..routing.factory import make_router
from ..routing.intent import IntentRouter, RouterError
from ..routing.local_client import ChatMessage, ChatRequest, OllamaClient, OllamaUnavailable, is_running
from ..tools.registry import ApprovalRequired, ToolRegistry, default_registry
from .prompts import build_system_prompt
from .schemas import Step, TaskOutcome
from .trajectory import TrajectoryRecorder

DEFAULT_MAX_STEPS = 6

# Terminal intents dispatch deterministically in one step.
TERMINAL_INTENTS = {
    "compute_finance", "inspect_file", "status_query", "wait_for_info",
    "approval_response", "new_deal", "list_deals", "unclear",
}
# Open-ended intents escalate to the bounded reasoning loop. Questions need
# sense-making, so they reason over known facts rather than a dead-end.
REASONING_INTENTS = {"run_analysis", "research", "long_horizon_task", "question"}


class InnerLoop:
    def __init__(
        self,
        deals_root: Path,
        deal_id: str,
        router: Optional[IntentRouter] = None,
        registry: Optional[ToolRegistry] = None,
        model: str = "qwen3:8b",
        ollama_url: str = "http://localhost:11434/v1",
        max_steps: int = DEFAULT_MAX_STEPS,
    ) -> None:
        self.deals_root = deals_root
        self.deal_id = deal_id
        self.router = router or make_router()
        self.registry = registry or default_registry()
        self.model = model
        self.ollama_url = ollama_url
        self.max_steps = max_steps

    # ------------------------------------------------------------------ run

    def run(self, message: str, context: dict[str, Any] | None = None) -> TaskOutcome:
        context = context or {}
        traj = TrajectoryRecorder(self.deals_root / self.deal_id, self.deal_id)
        steps: list[Step] = []

        # Step 0: classify intent. Von is the router; errors become blocked.
        intent_result = self._classify(message, context)
        router_meta = {
            "served_by": intent_result.served_by,
            "confidence": intent_result.confidence,
            "top": self._top3(intent_result.probabilities),
            "error": intent_result.error,
        }
        step = Step(index=0, router=router_meta, action="classify",
                    outputs={"intent": intent_result.intent})
        steps.append(step)
        traj.record(step)

        if intent_result.error is not None:
            return self._finish("blocked", f"router_error: {intent_result.error}", steps, traj)

        intent = intent_result.intent

        if intent == "unclear":
            return self._finish(
                "waiting",
                "Message was unclear; Pepe needs the user to clarify.",
                steps, traj, result={"intent": intent},
            )

        # Terminal intents: one deterministic dispatch.
        if intent in TERMINAL_INTENTS:
            return self._dispatch_terminal(intent, message, context, steps, traj)

        # Open-ended intents: bounded reasoning loop.
        return self._reasoning_loop(intent, message, context, steps, traj)

    # ------------------------------------------------------------------ classify

    def _classify(self, message: str, context: dict[str, Any]):
        try:
            return self.router.classify(message, context)
        except RouterError as e:
            from ..routing.intent import IntentResult
            return IntentResult(intent="unclear", confidence=0.0,
                                probabilities={}, served_by="error", error=str(e))
        except Exception as e:
            from ..routing.intent import IntentResult
            return IntentResult(intent="unclear", confidence=0.0,
                                probabilities={}, served_by="error", error=f"router_error: {e}")

    @staticmethod
    def _top3(probs: dict[str, float]) -> list[list[Any]]:
        items = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)[:3]
        return [[k, round(v, 4)] for k, v in items]

    # ------------------------------------------------------------------ terminal dispatch

    def _dispatch_terminal(self, intent: str, message: str, context: dict,
                           steps: list[Step], traj: TrajectoryRecorder) -> TaskOutcome:
        handler = _TERMINAL_HANDLERS.get(intent)
        if handler is None:
            return self._finish("failed", f"no handler for intent {intent}", steps, traj)
        try:
            out = handler(self, message, context)
        except ApprovalRequired as e:
            return self._finish("needs_approval", f"approval required: {e.tool_name}", steps, traj)
        step = Step(index=len(steps), action="tool" if out.get("kind") == "complete" else out["kind"],
                    note=intent, outputs=out)
        steps.append(step)
        traj.record(step)
        result = dict(out.get("result", {}))
        if out.get("reply"):
            result["reply"] = out["reply"]
        return self._finish(out["kind"], out.get("reason", ""), steps, traj, result=result)

    # ------------------------------------------------------------------ reasoning loop

    def _reasoning_loop(self, intent: str, message: str, context: dict,
                        steps: list[Step], traj: TrajectoryRecorder) -> TaskOutcome:
        if not is_running(self.ollama_url):
            return self._finish(
                "blocked",
                f"intent '{intent}' needs reasoning but Ollama is not reachable at {self.ollama_url}",
                steps, traj,
            )
        system = build_system_prompt(context, self.registry,
                                     facts=[{"key": f.key, "value": f.value, "source": f.source}
                                            for f in list_facts(self.deals_root, self.deal_id)])
        messages = [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=message),
        ]
        with OllamaClient(base_url=self.ollama_url) as client:
            for i in range(1, self.max_steps + 1):
                try:
                    reply = client.chat(ChatRequest(model=self.model, messages=messages))
                except OllamaUnavailable as e:
                    return self._finish("blocked", f"ollama unavailable: {e}", steps, traj)
                tool_call = self._parse_tool_call(reply)
                if tool_call is None:
                    step = Step(index=len(steps), action="reason", note=intent,
                                outputs={"reply": reply})
                    steps.append(step); traj.record(step)
                    return self._finish("complete", "reasoning produced an answer",
                                        steps, traj, result={"reply": reply})
                # Execute tool
                name = tool_call["tool"]
                params = tool_call.get("params", {})
                try:
                    output = self.registry.execute(name, **params)
                except ApprovalRequired as e:
                    return self._finish("needs_approval", f"approval required: {e.tool_name}",
                                        steps, traj)
                except KeyError:
                    output = {"error": f"unknown tool {name}"}
                except Exception as e:
                    output = {"error": str(e)}
                obs = json.dumps(output, default=str)
                if isinstance(output, dict) and "error" not in output:
                    _record_facts(self, name, output)
                step = Step(index=len(steps), action="tool", tool=name,
                            inputs=params, outputs={"result": output if isinstance(output, (dict, list)) else str(output)})
                steps.append(step); traj.record(step)
                messages.append(ChatMessage(role="assistant", content=reply))
                messages.append(ChatMessage(role="user", content=f"Observation for {name}: {obs}"))
        return self._finish("failed", f"step cap reached ({self.max_steps})", steps, traj)

    @staticmethod
    def _parse_tool_call(text: str) -> Optional[dict]:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
        except Exception:
            return None
        if isinstance(data, dict) and "tool" in data:
            return {"tool": data["tool"], "params": data.get("params", {})}
        return None

    # ------------------------------------------------------------------ finish

    def _finish(self, kind: str, reason: str, steps: list[Step], traj: TrajectoryRecorder,
                result: dict[str, Any] | None = None) -> TaskOutcome:
        step = Step(index=len(steps), action=kind, note=reason)
        steps.append(step)
        traj.record(step)
        return TaskOutcome(kind=kind, reason=reason, result=result or {},
                           steps=steps, run_id=traj.run_id)


# ---------------------------------------------------------------------------
# Terminal intent handlers. Each returns {"kind": ..., "reason": ..., "result": ...}
# kind in {complete, blocked, needs_approval, waiting}
# ---------------------------------------------------------------------------

def _handle_compute_finance(loop: InnerLoop, message: str, context: dict) -> dict:
    text = message.lower()
    nums = re.findall(r"-?\d+(?:\.\d+)?", message)
    cf = [float(n) for n in nums]
    if len(cf) < 2:
        return {"kind": "blocked", "reason": "no cashflow numbers found in message"}
    for fn in ("irr", "moic", "npv", "cagr"):
        if fn in text:
            try:
                if fn == "cagr":
                    if len(cf) < 3:
                        return {"kind": "blocked", "reason": "cagr needs start, end, years"}
                    out = loop.registry.execute("finance.cagr", start=cf[0], end=cf[1], years=cf[2])
                elif fn == "npv":
                    rate = cf[0]
                    cfs = cf[1:]
                    out = loop.registry.execute("finance.npv", rate=rate, cashflows=cfs)
                else:
                    out = loop.registry.execute(f"finance.{fn}", cashflows=cf)
            except ApprovalRequired:
                raise
            except Exception as e:
                return {"kind": "blocked", "reason": f"finance error: {e}"}
            _record_facts(loop, f"finance.{fn}", out)
            return {"kind": "complete", "result": out}
    return {"kind": "blocked", "reason": "could not determine which finance function to run"}


def _record_facts(loop: InnerLoop, tool_name: str, out: dict) -> None:
    """Record allowlisted facts from a tool result. Deterministic: only the
    mapped tool may write the key, and only the `value` field becomes the fact."""
    if not isinstance(out, dict):
        return
    if "value" not in out:
        return
    if not allowed_key(fn_key := fn_key_from_tool(tool_name)):
        return
    written, prev = save_fact(loop.deals_root, loop.deal_id, fn_key, out["value"], source=tool_name)
    if written:
        record(loop.deals_root, AuditRecord.now(
            loop.deal_id, "fact_overwritten" if prev else "fact_written",
            key=fn_key,
            value=str(out["value"]),
            source=tool_name,
            **({"old_value": str(prev.value)} if prev else {}),
        ))


def fn_key_from_tool(tool_name: str) -> str:
    """finance.irr -> irr, finance.moic -> moic, etc."""
    return tool_name.rsplit(".", 1)[-1]


def _handle_inspect_file(loop: InnerLoop, message: str, context: dict) -> dict:
    m = re.search(r"([^\s]+\.xlsx)", message, re.IGNORECASE)
    if m:
        path = loop.deals_root / loop.deal_id / "models" / Path(m.group(1)).name
        if not path.exists():
            return {"kind": "blocked", "reason": f"missing file: {path}"}
        out = loop.registry.execute("excel.inspect_workbook", path=str(path))
        return {"kind": "complete", "result": out}
    m = re.search(r"([^\s]+\.pdf)", message, re.IGNORECASE)
    if m:
        path = loop.deals_root / loop.deal_id / "documents" / Path(m.group(1)).name
        if not path.exists():
            return {"kind": "blocked", "reason": f"missing file: {path}"}
        out = loop.registry.execute("pdf.extract_text", path=str(path))
        return {"kind": "complete", "result": out}
    return {"kind": "blocked", "reason": "no .xlsx or .pdf path found in message"}


def _handle_status_query(loop: InnerLoop, message: str, context: dict) -> dict:
    from ..core_index.query import list_active_deals, pipeline_summary, list_deals
    from ..core_index.sync import sync_deal as sync_deal_to_index
    from ..state.machine import load_state
    from ..state.connection import get_pepe_db
    from ..memory.store import list_facts
    from ..state.tasks import list_active
    from ..audit.record import recent

    _, repo_root = _resolve_repo(loop.deals_root)
    # Sync the current deal to the Core Index first so the firm view reflects
    # the latest per-deal state (auto-sync runs after the handler, not before).
    try:
        sync_deal_to_index(repo_root, loop.deal_id)
    except Exception:
        pass

    # If the message names a deal (as `id` or as a word after 'the ... deal'),
    # report on that deal specifically instead of the whole firm.
    named = _named_deal_in(message, list_deals(repo_root))
    if named is not None:
        deal_root = loop.deals_root / named
        p = deal_root / "state" / "pepe.db"
        if not p.exists():
            return {"kind": "complete", "result": {},
                    "reply": f"Deal '{named}' has no workspace yet."}
        conn, lock = get_pepe_db(loop.deals_root, named)
        state = load_state(conn, lock, named)
        active = list_active(loop.deals_root, named)
        facts = list_facts(loop.deals_root, named)
        audit = recent(loop.deals_root, named, limit=3)
        details = {
            "deal": named,
            "state": state.value,
            "active_tasks": [
                {"description": t.description, "status": t.status,
                 "blocked_reason": t.blocked_reason} for t in active
            ],
            "facts_count": len(facts),
        }
        reply = _render_deal_status(named, state.value, active)
        return {"kind": "complete", "result": details, "reply": reply}

    # Firm-level status.
    result = {"pipeline": pipeline_summary(repo_root),
              "active_deals": list_active_deals(repo_root)}
    reply = _render_firm_status(result["pipeline"], result["active_deals"])
    return {"kind": "complete", "result": result, "reply": reply}


def _named_deal_in(message: str, deals: list[dict]) -> str | None:
    """Find a deal id/name referenced in the message. Checks:
       1. exact id match (lowercased), e.g. 'atlas'
       2. a word following 'the ... deal' or 'deal named X'
    Returns the deal id or None.
    """
    ml = message.lower()
    for d in deals:
        did = d["id"].lower()
        if did and re.search(rf"\b{re.escape(did)}\b", ml):
            return d["id"]
    m = re.search(r"\bdeal\s+(?:named\s+)?([a-z0-9_-]+)", ml)
    if m:
        for d in deals:
            if d["id"].lower() == m.group(1).lower():
                return d["id"]
    return None


def _render_deal_status(deal_id: str, state: str, active) -> str:
    if active:
        parts = []
        for t in active:
            if t.status == "blocked":
                parts.append(f"{t.description} (blocked: {t.blocked_reason or 'pending info'})")
            else:
                parts.append(f"{t.description} ({t.status})")
        return f"{deal_id} is {state}. Active: " + "; ".join(parts) + "."
    return f"{deal_id} is {state}. No active tasks."


def _render_firm_status(summary: dict, active: list[dict]) -> str:
    bits = [f"{summary['total_deals']} deal(s) total",
            f"{summary['active']} active",
            f"{summary['blocked_tasks']} blocked task(s)",
            f"{summary['pending_tasks']} pending"]
    s = ", ".join(bits) + "."
    if active:
        names = ", ".join(d["id"] for d in active[:5])
        s += f" Active: {names}."
    return s


def _handle_wait_for_info(loop: InnerLoop, message: str, context: dict) -> dict:
    m = re.search(r"\b(?:for|on|until)\b\s+(.+)$", message, re.IGNORECASE)
    reason = f"awaiting: {m.group(1).strip()}" if m else "awaiting user-provided information"
    return {"kind": "waiting", "reason": reason}


def _handle_approval_response(loop: InnerLoop, message: str, context: dict) -> dict:
    # The actual grant/deny is a guarded deterministic state transition; the
    # orchestrator applies it. Here we just record the user's answer.
    affirmative = bool(re.search(r"^\s*(yes|go ahead|approve|proceed|ok)\b", message, re.IGNORECASE))
    return {"kind": "complete", "result": {"approved": affirmative}}


def _handle_new_deal(loop: InnerLoop, message: str, context: dict) -> dict:
    return {"kind": "complete", "result": {"note": "workspace already exists for this deal"}}


def _handle_list_deals(loop: InnerLoop, message: str, context: dict) -> dict:
    from ..core_index.query import list_deals
    _, repo_root = _resolve_repo(loop.deals_root)
    return {"kind": "complete", "result": {"deals": list_deals(repo_root)}}


def _resolve_repo(deals_root: Path) -> tuple[Path, Path]:
    repo_root = deals_root.parent if deals_root.name == "deals" else Path.cwd()
    return deals_root, repo_root


_TERMINAL_HANDLERS: dict[str, Callable[[InnerLoop, str, dict], dict]] = {
    "compute_finance": _handle_compute_finance,
    "inspect_file": _handle_inspect_file,
    "status_query": _handle_status_query,
    "wait_for_info": _handle_wait_for_info,
    "approval_response": _handle_approval_response,
    "new_deal": _handle_new_deal,
    "list_deals": _handle_list_deals,
    "unclear": lambda loop, m, c: {"kind": "waiting", "reason": "message unclear; please clarify"},
}
