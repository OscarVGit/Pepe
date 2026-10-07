# PRINCIPLES — Design Rules

1. **Local-first. Cloud-escalated. Privacy-preserving. Deterministic where
   possible. Human-approved when necessary.**
2. **Compose, don't recreate.** Smallest PE-specific layer over mature OSS.
3. **The LLM orchestrates; code calculates.** IRR/MOIC/schedules/sensitivities/
   reconciliations are deterministic. Never do finance in LLM arithmetic.
4. **Employee, not app.** Remember context; task lists; concise questions;
   approvals distinct from questions; async work; explain uncertainty; escalate
   ambiguity; never pretend incomplete work is done; never fabricate data.
5. **Facts vs assumptions always labelled.** Sources traceable to documents.
6. **Copy-on-write artifacts.** Never overwrite `original.*`; working copy →
   validation → versioned output; every material change auditable.
7. **Approvals are architectural** (`agent/policy.py`), not prompt hints.
8. **Privacy by construction.** Local sanitisation before cloud; hard policies
   enforced in code/gateway; fail closed.
9. **Documentation is product.** Future agents must learn Pepe from this repo.
10. **Pepe Core Index is the firm-level view; deal state is the source of
    truth.** The index (`pepe.db` at repo root) is a read-aggregated mirror,
    never authoritative. Per-deal `pepe.db` remains sovereign. Sync is
    best-effort and never fails a primary operation.
11. **Reconnaissance vs surgery.** Deep-agent-style long-horizon reasoning is
    reconnaissance only: it explores, proposes, and returns structured
    findings. Surgery (mutating deal artifacts, approving conclusions, writing
    numbers of record) is always deterministic, audit-logged, and
    approval-gated.
