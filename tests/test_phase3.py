"""Phase 3 — router + Azure DI path (OCR mocked)."""

from datetime import date
from pathlib import Path

import fitz
import yaml

from folioiq import DocumentExtractor, load_spec
from folioiq.router import choose_parser
from folioiq.specs import ExtractionSpec

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _pdf(tmp_path: Path, text: str, name: str = "doc.pdf") -> Path:
    path = tmp_path / name
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()
    return path


def test_router_prefers_pymupdf_for_text_pdf(tmp_path: Path):
    path = _pdf(tmp_path, "Invoice INV-1 plenty of embedded text for routing.")
    data = path.read_bytes()
    spec = load_spec(EXAMPLES / "invoice.yaml")
    decision = choose_parser(data, path.name, spec)
    assert decision.parser == "pymupdf"


def test_router_uses_azure_di_for_empty_pdf(tmp_path: Path):
    path = _pdf(tmp_path, "x")
    data = path.read_bytes()
    spec = load_spec(EXAMPLES / "invoice.yaml")
    decision = choose_parser(data, path.name, spec)
    assert decision.parser == "azure_di"
    assert "little" in decision.reason or "no text" in decision.reason


def test_router_images_use_azure_di(tmp_path: Path):
    img = tmp_path / "scan.png"
    # minimal invalid-as-pdf bytes; router only checks suffix
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 40)
    spec = load_spec(EXAMPLES / "invoice.yaml")
    decision = choose_parser(img.read_bytes(), img.name, spec)
    assert decision.parser == "azure_di"
    assert decision.reason == "image file"


def test_explicit_pipeline_parser(tmp_path: Path):
    path = _pdf(tmp_path, "Invoice INV-1 plenty of embedded text for routing.")
    raw = yaml.safe_load((EXAMPLES / "invoice.yaml").read_text())
    raw["pipeline"] = {"mode": "explicit", "parser": "azure_di"}
    spec = ExtractionSpec.model_validate(raw)
    decision = choose_parser(path.read_bytes(), path.name, spec)
    assert decision.parser == "azure_di"
    assert "explicit" in decision.reason


class _FakeLLM:
    def extract(self, *, system, user, model):
        assert "OCR FROM DI" in user or "INV" in user or "DOCUMENT TEXT" in user
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
        return "OCR FROM DI Invoice INV-1 Vendor ACME Total 10 USD"


def test_extract_scan_path_uses_ocr(tmp_path: Path):
    path = _pdf(tmp_path, "x")  # routes to azure_di
    extractor = DocumentExtractor(llm=_FakeLLM(), ocr=_FakeOCR())
    result = extractor.extract(path, spec=EXAMPLES / "invoice.yaml")
    assert result.is_valid
    assert result.metadata["parser"] == "azure_di"
    assert result.data["invoice_number"] == "INV-1"
