# Skill: dcf

- **Purpose:** Discounted-cash-flow valuation with defensible assumptions.
- **When to use:** Valuation cross-checks alongside multiples/LBO.
- **Required inputs:** FCF build, WACC components, terminal assumption.
- **Available tools:** Deterministic DCF functions, Excel skill.
- **Expected outputs:** Enterprise value bridge + sensitivity to WACC/g.
- **Validation:** FCF reconciles to statements; discounting recomputed in code.
- **Approval requirements:** Draft low; assumption changes medium.
- **Failure modes:** Unstable terminal value → flag, don't smooth silently.
