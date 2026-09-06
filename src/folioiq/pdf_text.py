"""Pull plain text from digital PDFs."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import fitz

from folioiq.exceptions import FolioIQError
from folioiq.io import DocumentInput, read_document_bytes, suffix_of

MIN_TEXT_CHARS = 20


def peek_pdf_text(document: DocumentInput) -> str:
    """Return embedded PDF text (may be empty). Does not raise on short text."""
    data, name = read_document_bytes(document)
    suffix = suffix_of(document, name)
    if suffix and suffix != ".pdf":
        return ""

    doc = fitz.open(stream=data, filetype="pdf")
    try:
        parts = [page.get_text("text") for page in doc]
        return "\n".join(parts).strip()
    finally:
        doc.close()


def extract_pdf_text(document: DocumentInput) -> str:
    """Extract embedded text from a digital PDF. Raises if too little text."""
    # Prefer path open when we have a path (clearer errors)
    if isinstance(document, (str, Path)):
        path = Path(document).expanduser().resolve()
        if not path.is_file():
            raise FolioIQError(f"Document not found: {path}")
        if path.suffix.lower() not in ("", ".pdf"):
            raise FolioIQError(
                f"pymupdf parser expects PDF (got {path.suffix or 'no extension'})."
            )

    text = peek_pdf_text(document)
    if len(text) < MIN_TEXT_CHARS:
        raise FolioIQError(
            "PDF has little or no embedded text. Use parser azure_di (or pipeline auto)."
        )
    return text
