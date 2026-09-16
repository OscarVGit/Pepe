# MODEL_ROUTING — Cheapest Capable Capability First

Order per task:

1. **Deterministic?** IRR/MOIC/CAGR/schedules/sensitivities/reconciliations →
   code. No LLM arithmetic. Ever.
2. **Local model** (Ollama / MLX / self-hosted OpenAI-compat): classification,
   extraction, normal reasoning, complex local reasoning.
3. **Frontier cloud**: only when local is insufficient AND payload can be
   safely abstracted AND policy/approval permits. Sanitise locally first;
   send minimum necessary (e.g. "Company A, Rev $420m…" not the CIM).

Routing signals: task complexity, data sensitivity/classification, local
capability + confidence, latency, cost, provider availability, firm/deal policy,
cloud-permitted flag, approval status. Implementation: wrap LiteLLM-style
Router/Gateway (fallbacks, budgets, OpenAI-compat) + RouteLLM-style
weak-vs-strong classification as investigation targets; Pepe owns the PE policy
and confidence threshold, not a bespoke gateway. See ADR-0007.
