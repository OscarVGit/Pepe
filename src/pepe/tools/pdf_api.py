"""Read-only PDF inspection. PyMuPDF (imported as `pymupdf`)."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pymupdf  # PyMuPDF (preferred import; `fitz` is the legacy alias)


def list_pages(path: Path) -> int:
    return pymupdf.open(str(path)).page_count


def extract_text(path: Path, page_range: tuple[int, int] | None = None) -> str:
    """Extract plain text. Optional page_range is inclusive 1-indexed."""
    doc = pymupdf.open(str(path))
    try:
        if page_range is None:
            return "\n".join(p.get_text() for p in doc)
        start, end = page_range
        return "\n".join(doc[i].get_text() for i in range(start - 1, end))
    finally:
        doc.close()


def iter_pages(path: Path) -> Iterator[tuple[int, str]]:
    doc = pymupdf.open(str(path))
    try:
        for i, page in enumerate(doc):
            yield i + 1, page.get_text()
    finally:
        doc.close()
