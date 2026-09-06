"""Choose pymupdf vs azure_di."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import fitz

from folioiq.io import is_image_suffix, suffix_of
from folioiq.pdf_text import MIN_TEXT_CHARS
from folioiq.specs import ExtractionSpec

ParserName = Literal["pymupdf", "azure_di"]


@dataclass(frozen=True)
class RouteDecision:
    parser: ParserName
    reason: str
    text_chars: int = 0


def choose_parser(
    data: bytes,
    filename: str,
    spec: ExtractionSpec,
) -> RouteDecision:
    """Pick a text parser for this document + spec."""
    explicit = (
        (spec.pipeline.parser or "").strip().lower()
        if spec.pipeline.mode == "explicit"
        else ""
    )
    if explicit in ("pymupdf", "azure_di"):
        return RouteDecision(
            parser=explicit,  # type: ignore[arg-type]
            reason=f"explicit pipeline.parser={explicit}",
        )

    suffix = suffix_of(filename)
    if is_image_suffix(suffix):
        return RouteDecision(parser="azure_di", reason="image file", text_chars=0)

    text = _pdf_text_from_bytes(data)
    if len(text) >= MIN_TEXT_CHARS:
        return RouteDecision(
            parser="pymupdf",
            reason="pdf has embedded text",
            text_chars=len(text),
        )

    return RouteDecision(
        parser="azure_di",
        reason="pdf has little/no text layer",
        text_chars=len(text),
    )


def _pdf_text_from_bytes(data: bytes) -> str:
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception:
        return ""
    try:
        return "\n".join(page.get_text("text") for page in doc).strip()
    finally:
        doc.close()
