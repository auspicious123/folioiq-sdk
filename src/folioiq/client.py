"""Main entrypoint — schema-driven extraction."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from pydantic import BaseModel

from folioiq.azure_di import OCRClient, get_default_ocr
from folioiq.config import FolioIQSettings
from folioiq.io import is_image_suffix, read_document_bytes, suffix_of
from folioiq.llm import LLMClient, get_default_llm
from folioiq.models import ExtractionResult
from folioiq.pdf_text import extract_pdf_text
from folioiq.prompt import build_extraction_prompt
from folioiq.router import ParserName, choose_parser
from folioiq.specs import ExtractionSpec, build_model, load_spec
from folioiq.validation import validate_extraction

DocumentInput = str | Path | bytes | BinaryIO

_SYSTEM = (
    "You are a document extraction engine. "
    "Extract fields exactly as present in the document text. "
    "Never invent values. Use null for missing fields."
)


class DocumentExtractor:
    """Extract structured fields from a document using a YAML spec."""

    def __init__(
        self,
        settings: FolioIQSettings | None = None,
        llm: LLMClient | None = None,
        ocr: OCRClient | None = None,
    ) -> None:
        self.settings = settings or FolioIQSettings()
        self._llm = llm
        self._ocr = ocr

    @classmethod
    def from_env(cls) -> DocumentExtractor:
        """Build from environment variables / .env."""
        return cls(settings=FolioIQSettings())

    def load_spec(
        self,
        spec: str | Path,
        *,
        instructions: str | Path | None = None,
    ) -> ExtractionSpec:
        """Load YAML spec (+ optional / sibling Markdown instructions)."""
        return load_spec(spec, instructions=instructions)

    def build_model(self, spec: ExtractionSpec) -> type[BaseModel]:
        """Build a Pydantic model from the loaded spec."""
        return build_model(spec)

    def extract(
        self,
        document: DocumentInput,
        spec: str | Path,
        *,
        instructions: str | Path | None = None,
    ) -> ExtractionResult:
        """Extract structured data from a PDF or image.

        On validation failure (or parse failure), retries once with the
        alternate parser when that makes sense.
        """
        loaded = self.load_spec(spec, instructions=instructions)
        model_cls = self.build_model(loaded)
        data, filename = read_document_bytes(document)
        decision = choose_parser(data, filename, loaded)

        primary = self._run(
            data=data,
            filename=filename,
            spec=loaded,
            model_cls=model_cls,
            parser=decision.parser,
            route_reason=decision.reason,
            fallback_used=False,
        )
        if primary.is_valid:
            return primary

        alt = _alternate_parser(decision.parser, filename)
        if alt is None:
            return primary

        secondary = self._run(
            data=data,
            filename=filename,
            spec=loaded,
            model_cls=model_cls,
            parser=alt,
            route_reason=f"fallback after {decision.parser} failed",
            fallback_used=True,
            primary_parser=decision.parser,
            primary_errors=primary.validation_errors,
        )
        # Prefer a valid fallback; otherwise keep the richer primary errors
        if secondary.is_valid:
            return secondary
        return primary

    def _run(
        self,
        *,
        data: bytes,
        filename: str,
        spec: ExtractionSpec,
        model_cls: type[BaseModel],
        parser: ParserName,
        route_reason: str,
        fallback_used: bool,
        primary_parser: str | None = None,
        primary_errors: list[str] | None = None,
    ) -> ExtractionResult:
        meta: dict = {
            "spec": spec.name,
            "spec_version": spec.version,
            "parser": parser,
            "route_reason": route_reason,
            "fallback_used": fallback_used,
        }
        if primary_parser:
            meta["primary_parser"] = primary_parser
        if primary_errors:
            meta["primary_errors"] = primary_errors

        try:
            text = self._read_text(data, parser)
        except Exception as exc:
            return ExtractionResult(
                data={},
                is_valid=False,
                validation_errors=[str(exc)],
                metadata=meta,
            )

        llm = self._llm or get_default_llm(self.settings)
        meta["llm"] = type(llm).__name__
        meta["chars"] = len(text)
        prompt = build_extraction_prompt(spec)
        user = f"{prompt}\n\n--- DOCUMENT TEXT ---\n{text}"

        try:
            parsed = llm.extract(system=_SYSTEM, user=user, model=model_cls)
            payload = parsed.model_dump(mode="json")
        except Exception as exc:
            return ExtractionResult(
                data={},
                is_valid=False,
                validation_errors=[str(exc)],
                metadata=meta,
            )

        errors = validate_extraction(spec, payload)
        return ExtractionResult(
            data=payload,
            is_valid=not errors,
            validation_errors=errors,
            metadata=meta,
        )

    def _read_text(self, data: bytes, parser: str) -> str:
        if parser == "pymupdf":
            return extract_pdf_text(data)
        ocr = self._ocr or get_default_ocr(self.settings)
        return ocr.extract_text(data)


def _alternate_parser(parser: ParserName, filename: str) -> ParserName | None:
    """One flip: pymupdf ↔ azure_di. Images cannot use pymupdf."""
    if parser == "pymupdf":
        return "azure_di"
    if is_image_suffix(suffix_of(filename)):
        return None
    return "pymupdf"
