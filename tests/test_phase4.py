"""Phase 4 — validation + one parser fallback."""

from datetime import date
from pathlib import Path

import fitz

from folioiq import DocumentExtractor, load_spec
from folioiq.validation import validate_extraction

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _pdf(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "doc.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()
    return path


def test_validate_missing_required():
    spec = load_spec(EXAMPLES / "invoice.yaml")
    errors = validate_extraction(spec, {"vendor_name": "ACME"})
    assert any("invoice_number" in e for e in errors)
    assert any("total_amount" in e for e in errors)


def test_validate_ok_payload():
    spec = load_spec(EXAMPLES / "invoice.yaml")
    errors = validate_extraction(
        spec,
        {
            "invoice_number": "INV-1",
            "invoice_date": "2026-01-01",
            "vendor_name": "ACME",
            "currency": "USD",
            "total_amount": 10.0,
        },
    )
    assert errors == []


class _BadThenGoodLLM:
    """First call returns incomplete data; later calls return a full payload."""

    def __init__(self) -> None:
        self.calls = 0

    def extract(self, *, system, user, model):
        self.calls += 1
        if self.calls == 1:
            # Bypass pydantic required fields by building via model_construct
            return model.model_construct(
                invoice_number=None,
                invoice_date=None,
                vendor_name="ACME",
                currency=None,
                total_amount=None,
                po_number=None,
                line_items=None,
            )
        return model(
            invoice_number="INV-1",
            invoice_date=date(2026, 1, 1),
            vendor_name="ACME",
            currency="USD",
            total_amount=10.0,
            po_number=None,
            line_items=None,
        )


class _FakeOCR:
    def extract_text(self, document):
        return "Invoice INV-1 Vendor ACME Total 10 USD currency USD date 2026-01-01"


def test_fallback_to_azure_di_when_primary_invalid(tmp_path: Path):
    # Text-rich PDF → primary pymupdf; validation fails → fallback azure_di
    path = _pdf(tmp_path, "Invoice INV-1 plenty of embedded text for routing path.")
    llm = _BadThenGoodLLM()
    extractor = DocumentExtractor(llm=llm, ocr=_FakeOCR())
    result = extractor.extract(path, spec=EXAMPLES / "invoice.yaml")

    assert result.is_valid is True
    assert result.metadata["fallback_used"] is True
    assert result.metadata["parser"] == "azure_di"
    assert result.metadata["primary_parser"] == "pymupdf"
    assert result.data["invoice_number"] == "INV-1"
    assert llm.calls == 2
