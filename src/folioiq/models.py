"""Public result types (minimal for Phase 0)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ExtractionResult(BaseModel):
    """Outcome of one extract() call."""

    data: dict[str, Any] = Field(default_factory=dict)
    is_valid: bool = False
    validation_errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
