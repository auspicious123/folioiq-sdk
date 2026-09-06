"""Phase 5 — fixture packs + eval scoring (no live LLM required)."""

import json
from pathlib import Path

from folioiq.eval import normalize_value, run_pack, score_fields, values_match
from folioiq import DocumentExtractor

PACKS = Path(__file__).resolve().parent / "fixtures" / "packs"


def test_normalize_and_match():
    assert values_match("EUR", "eur")
    assert values_match(31830.0, 31830)
    assert values_match("Apex Precision Manufacturing Inc.", "Apex Precision Manufacturing Inc")
    assert normalize_value(31830.0) == "31830"


def test_score_fields_partial():
    scores = score_fields(
        {"po_number": "4500198872", "currency": "EUR"},
        {"po_number": "4500198872", "currency": "USD"},
    )
    by_name = {s.name: s.match for s in scores}
    assert by_name["po_number"] is True
    assert by_name["currency"] is False


def test_po_pack_files_exist():
    po = PACKS / "po"
    assert (po / "document.pdf").is_file()
    assert (po / "spec.yaml").is_file()
    assert (po / "expected.json").is_file()
    expected = json.loads((po / "expected.json").read_text())
    assert expected["po_number"] == "4500198872"


def test_run_pack_with_perfect_fake_llm():
    expected = json.loads((PACKS / "po" / "expected.json").read_text())

    class _PerfectLLM:
        def extract(self, *, system, user, model):
            return model.model_validate(expected)

    extractor = DocumentExtractor(llm=_PerfectLLM())
    report = run_pack(PACKS / "po", extractor=extractor)
    assert not report.skipped
    assert report.is_valid
    assert report.accuracy == 1.0
    assert report.metadata["parser"] == "pymupdf"


def test_dr_pack_skipped_until_labeled():
    report = run_pack(PACKS / "dr", extractor=DocumentExtractor(llm=object()))  # type: ignore[arg-type]
    assert report.skipped
    assert "no labeled" in report.skip_reason
