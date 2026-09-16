# Skill: cim-analysis

- **Purpose:** Extract structured deal facts from CIMs with source lineage.
- **When to use:** New deal intake, CIM vs accounts reconciliation.
- **Required inputs:** CIM PDF path.
- **Available tools:** PDF extraction, Python structuring, deal-memory writer.
- **Expected outputs:** Fact table (value + page + confidence) + open questions.
- **Validation:** Every figure cites page/section; conflicts flagged.
- **Approval requirements:** Extraction low-risk (read-only).
- **Failure modes:** Scanned/OCR-poor docs → report confidence, don't guess.
