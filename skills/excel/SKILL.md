# Skill: excel

- **Purpose:** Inspect, modify, and validate professional Excel models via granular ops.
- **When to use:** Any read/change/validation of `.xlsx` models.
- **Required inputs:** Workbook path, target sheet/range, audit reason.
- **Available tools:** `tools/excel_api.py` (inspect_range … validate_model, create_snapshot); Python for recalculation checks.
- **Expected outputs:** Working-copy modification + validation report + versioned file.
- **Validation:** `validate_model` clean; key schedules balance; before/after diff recorded.
- **Approval requirements:** Reads low-risk; modifications medium (report); overwriting `original.*` high (forbidden without approval).
- **Failure modes:** Broken formulas, circular refs, macro workbooks — stop and escalate, never silently fix figures.
