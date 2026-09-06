"""FolioIQ — schema-driven document extraction."""

from folioiq.client import DocumentExtractor
from folioiq.exceptions import FolioIQError, NotImplementedPhaseError, SpecError
from folioiq.models import ExtractionResult
from folioiq.specs import ExtractionSpec, FieldSpec, build_model, load_spec

__all__ = [
    "DocumentExtractor",
    "ExtractionResult",
    "ExtractionSpec",
    "FieldSpec",
    "FolioIQError",
    "NotImplementedPhaseError",
    "SpecError",
    "build_model",
    "load_spec",
]

__version__ = "0.1.0"
