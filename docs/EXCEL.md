# EXCEL — First-Class, Granular, Auditable

Never one giant `edit_excel()`. Granular ops in `tools/excel_api.py`:
`inspect_workbook, list_sheets, inspect_range, find_assumption, find_formula,
modify_cell, modify_range, insert_formula, copy_range, insert_row,
insert_column, update_sheet, recalculate, validate_model, compare_versions,
create_snapshot`.

Flow: `original.xlsx` (immutable) → working copy → Pepe modifications →
validation → versioned output (`models/v3_downside_7.0x.xlsx`). Every material
modification carries `audit_reason` + before/after values. Financial semantics
(entry/exit multiples, sources & uses, sweep) map onto openpyxl now, xlwings/COM
later. MCP Excel servers are wrap candidates, not the semantics layer.
