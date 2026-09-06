"""Phase 0 smoke tests — package imports and stub behavior."""

import pytest

from folioiq import DocumentExtractor, ExtractionResult, NotImplementedPhaseError, __version__


def test_version():
    assert __version__ == "0.1.0"


def test_from_env_constructs():
    extractor = DocumentExtractor.from_env()
    assert extractor.settings.pipeline_mode == "auto"


def test_extract_not_implemented_yet():
    """Without a real spec file, extract fails on SpecError (Phase 1+)."""
    from folioiq import SpecError

    extractor = DocumentExtractor.from_env()
    with pytest.raises(SpecError):
        extractor.extract("doc.pdf", spec="spec.yaml")


def test_result_model_defaults():
    result = ExtractionResult()
    assert result.data == {}
    assert result.is_valid is False
    assert result.validation_errors == []
