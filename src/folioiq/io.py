"""Shared document IO helpers."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from folioiq.exceptions import FolioIQError

DocumentInput = str | Path | bytes | BinaryIO

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp", ".gif"}
_PDF_EXTS = {".pdf"}


def read_document_bytes(document: DocumentInput) -> tuple[bytes, str]:
    """Return (bytes, filename_hint) for routing / OCR."""
    if isinstance(document, (bytes, bytearray)):
        return bytes(document), "document.pdf"

    if hasattr(document, "read"):
        data = document.read()
        if isinstance(data, str):
            data = data.encode("utf-8")
        name = getattr(document, "name", "document.bin")
        return bytes(data), Path(str(name)).name

    path = Path(document).expanduser().resolve()
    if not path.is_file():
        raise FolioIQError(f"Document not found: {path}")
    return path.read_bytes(), path.name


def suffix_of(document: DocumentInput, filename_hint: str | None = None) -> str:
    if filename_hint:
        return Path(filename_hint).suffix.lower()
    if isinstance(document, (str, Path)):
        return Path(document).suffix.lower()
    if hasattr(document, "name"):
        return Path(str(document.name)).suffix.lower()
    return ""


def is_image_suffix(suffix: str) -> bool:
    return suffix in _IMAGE_EXTS


def is_pdf_suffix(suffix: str) -> bool:
    return suffix in _PDF_EXTS or suffix == ""
