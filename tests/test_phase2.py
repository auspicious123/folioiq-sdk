"""Phase 2 — PDF text + LLM extraction (mocked LLM)."""

from datetime import date
from pathlib import Path

import fitz
import pytest
from pydantic import BaseModel

from folioiq import DocumentExtractor, FolioIQError, load_spec
from folioiq.pdf_text import extract_pdf_text
from folioiq.prompt import build_extraction_prompt

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _make_pdf(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()
    return path


def test_extract_pdf_text(tmp_path: Path):
    pdf = _make_pdf(
        tmp_path,
        "Invoice INV-99\nVendor ACME Corp\nTotal 100.00 USD\nMore text here.",
    )
    text = extract_pdf_text(pdf)
    assert "INV-99" in text
    assert "ACME" in text


def test_extract_pdf_text_rejects_empty(tmp_path: Path):
    pdf = _make_pdf(tmp_path, "x")
    with pytest.raises(FolioIQError, match="little or no embedded text"):
        extract_pdf_text(pdf)


def test_prompt_includes_fields_and_instructions():
    spec = load_spec(EXAMPLES / "invoice.yaml")
    prompt = build_extraction_prompt(spec)
    assert "invoice_number" in prompt
    assert "Never invent" in prompt


class _FakeLLM:
    def extract(self, *, system: str, user: str, model: type[BaseModel]) -> BaseModel:
        assert "DOCUMENT TEXT" in user
        return model(
            invoice_number="INV-99",
            invoice_date=date(2026, 1, 15),
            vendor_name="ACME Corp",
            currency="USD",
            total_amount=100.0,
            po_number=None,
            line_items=None,
        )


def test_extract_with_fake_llm(tmp_path: Path):
    pdf = _make_pdf(
        tmp_path,
        "Invoice INV-99 Vendor ACME Corp Total 100.00 USD extra padding text.",
    )
    extractor = DocumentExtractor(llm=_FakeLLM())
    result = extractor.extract(pdf, spec=EXAMPLES / "invoice.yaml")

    assert result.is_valid is True
    assert result.data["invoice_number"] == "INV-99"
    assert result.data["vendor_name"] == "ACME Corp"
    assert result.metadata["parser"] == "pymupdf"
    assert result.metadata["spec"] == "invoice"
