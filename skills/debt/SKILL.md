# Skill: debt

- **Purpose:** Model debt schedules, covenants, and financing cases.
- **When to use:** Term sheets, leverage scenarios, covenant checks.
- **Required inputs:** Facility terms (margin, amortisation, maturity, covenants).
- **Available tools:** Deterministic schedule builders, Excel skill.
- **Expected outputs:** Schedule + headroom analysis.
- **Validation:** Interest/DS computed in code; cash sweep logic tested.
- **Approval requirements:** Schedule drafts low; assumption updates medium.
- **Failure modes:** Missing terms → wait for user, never assume margin.
