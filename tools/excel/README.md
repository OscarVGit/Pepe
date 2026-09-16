# Tools — Excel

Granular ops only (`src/pepe/tools/excel_api.py`). Wrap order: openpyxl
(Phase 1+) → xlwings/COM or LibreOffice (later) → Excel MCP servers
(investigate). Pepe owns financial-model semantics, not cell I/O.
Copy-on-write mandatory.
