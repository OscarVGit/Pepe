"""Build fixture artifacts (Excel, PDF) for restart-resume tests.

Run once. Idempotent: overwrites fixtures on every call.
"""
from __future__ import annotations

import pathlib

import openpyxl
import pymupdf

FIXTURES = pathlib.Path(__file__).resolve().parent


def build_xlsx() -> pathlib.Path:
    path = FIXTURES / "sample.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inputs"
    ws["A1"] = "Period"
    ws["B1"] = "Revenue"
    ws["C1"] = "EBITDA"
    data = [
        ("2024A", 420.0, 84.0),
        ("2025E", 460.0, 92.0),
        ("2026E", 510.0, 105.0),
    ]
    for row in data:
        ws.append(row)
    named = openpyxl.workbook.defined_name.DefinedName(
        name="EntryMultiple", attr_text="Inputs!$C$4"
    )
    wb.defined_names.add(named)
    wb.save(path)
    return path


def build_pdf() -> pathlib.Path:
    path = FIXTURES / "sample.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Project Atlas — Confidential Information Memorandum")
    page.insert_text((72, 92), "Management EBITDA: $42m (FY24).")
    page.insert_text((72, 112), "Revenue: $420m. Growth: 9% CAGR.")
    doc.save(str(path))
    doc.close()
    return path


if __name__ == "__main__":
    print("xlsx:", build_xlsx())
    print("pdf :", build_pdf())
