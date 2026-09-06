"""Phase 1 — YAML spec loading and Pydantic model building."""

from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from folioiq import DocumentExtractor, SpecError, build_model, load_spec

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_load_invoice_spec_and_sibling_md():
    spec = load_spec(EXAMPLES / "invoice.yaml")
    assert spec.name == "invoice"
    assert spec.version == "1.0"
    assert "invoice_number" in spec.extraction.fields
    assert spec.instructions is not None
    assert "Never invent" in spec.instructions


def test_build_model_accepts_valid_payload():
    spec = load_spec(EXAMPLES / "invoice.yaml")
    Model = build_model(spec)
    obj = Model(
        invoice_number="INV-1",
        invoice_date=date(2026, 9, 4),
        vendor_name="ABC Ltd",
        currency="INR",
        total_amount=72000,
        line_items=[{"description": "Widget", "quantity": 2, "unit_price": 100, "amount": 200}],
    )
    assert obj.invoice_number == "INV-1"
    assert obj.line_items[0].description == "Widget"


def test_build_model_rejects_missing_required():
    spec = load_spec(EXAMPLES / "invoice.yaml")
    Model = build_model(spec)
    with pytest.raises(ValidationError):
        Model(vendor_name="Only vendor")


def test_missing_spec_raises():
    with pytest.raises(SpecError):
        load_spec("/tmp/does-not-exist-folioiq.yaml")


def test_extractor_load_and_build():
    extractor = DocumentExtractor.from_env()
    spec = extractor.load_spec(EXAMPLES / "invoice.yaml")
    Model = extractor.build_model(spec)
    assert Model.__name__ == "invoice"


def test_extract_requires_pdf_file():
    from folioiq import FolioIQError

    extractor = DocumentExtractor.from_env()
    # Spec loads OK; document path missing → FolioIQError from pdf layer
    with pytest.raises(FolioIQError, match="Document not found"):
        extractor.extract("/tmp/folioiq-missing.pdf", spec=EXAMPLES / "invoice.yaml")
