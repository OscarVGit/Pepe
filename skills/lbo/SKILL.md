# Skill: lbo

- **Purpose:** Build and stress leveraged-buyout models (sources & uses, debt schedule, returns).
- **When to use:** Entry/exit, leverage, and case analysis requests.
- **Required inputs:** Entry EBITDA + multiple, debt terms, operating assumptions, exit assumptions.
- **Available tools:** Deterministic finance lib (Phase 1+), Excel skill, Python sensitivities.
- **Expected outputs:** Base/downside cases with IRR/MOIC + sensitivity commentary.
- **Validation:** Sources = uses; debt amortises; returns recomputed from cash flows, not LLM arithmetic.
- **Approval requirements:** Draft analysis low; updating working model medium; IC conclusions high.
- **Failure modes:** Missing debt terms → `WAITING_FOR_INFORMATION`, never invent leverage.
