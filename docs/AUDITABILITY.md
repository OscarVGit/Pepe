# AUDITABILITY — Answer "What Changed and Why"

Every consequential action → `AuditRecord` (timestamp, agent, deal, task,
source, action, old/new value, reason, model, tool, approval, result),
append-only hash-chained JSONL (SQLite index later).

Lineage: source doc → extracted value → transformation → assumption → formula →
final result. Cloud escalations additionally record: provider/model, reason,
classification, payload hash + sanitisation report, approval, result reference.
Supports "What did you change in the model?" and "Why is EBITDA $45.2m?"
