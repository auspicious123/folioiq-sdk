"""Load YAML extraction specs and build Pydantic models."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, create_model

from folioiq.exceptions import SpecError

FieldType = Literal[
    "string",
    "number",
    "integer",
    "boolean",
    "date",
    "datetime",
    "array",
    "object",
]


class FieldSpec(BaseModel):
    """One field in the extraction schema."""

    type: FieldType = "string"
    required: bool = False
    description: str = ""
    items: FieldSpec | None = None
    fields: dict[str, FieldSpec] | None = None


class PipelineSpec(BaseModel):
    mode: Literal["auto", "explicit"] = "auto"
    parser: str | None = None
    llm: str | None = None
    model: str | None = None


class DocumentSpec(BaseModel):
    allowed_types: list[str] = Field(default_factory=lambda: ["pdf", "png", "jpg", "jpeg"])


class ExtractionBlock(BaseModel):
    fields: dict[str, FieldSpec]


class ExtractionSpec(BaseModel):
    """Machine-readable extraction contract (from YAML)."""

    name: str
    version: str = "1.0"
    document: DocumentSpec = Field(default_factory=DocumentSpec)
    pipeline: PipelineSpec = Field(default_factory=PipelineSpec)
    extraction: ExtractionBlock
    # Filled by loader — not from YAML
    path: Path | None = None
    instructions: str | None = None


# Allow nested FieldSpec references
FieldSpec.model_rebuild()


_TYPE_MAP: dict[str, type] = {
    "string": str,
    "number": float,
    "integer": int,
    "boolean": bool,
    "date": date,
    "datetime": datetime,
}


def load_spec(
    path: str | Path,
    *,
    instructions: str | Path | None = None,
) -> ExtractionSpec:
    """Load a YAML spec and optional Markdown instructions.

    If ``instructions`` is omitted, uses a sibling ``.md`` with the same stem
    when it exists (e.g. ``invoice.yaml`` → ``invoice.md``).
    """
    spec_path = Path(path).expanduser().resolve()
    if not spec_path.is_file():
        raise SpecError(f"Spec not found: {spec_path}")

    try:
        raw = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SpecError(f"Invalid YAML in {spec_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise SpecError(f"Spec must be a mapping: {spec_path}")

    try:
        spec = ExtractionSpec.model_validate(raw)
    except Exception as exc:
        raise SpecError(f"Invalid spec structure in {spec_path}: {exc}") from exc

    if not spec.extraction.fields:
        raise SpecError(f"Spec has no extraction.fields: {spec_path}")

    spec.path = spec_path
    spec.instructions = _resolve_instructions(spec_path, instructions)
    return spec


def _resolve_instructions(
    spec_path: Path,
    instructions: str | Path | None,
) -> str | None:
    if instructions is None:
        sibling = spec_path.with_suffix(".md")
        if sibling.is_file():
            return sibling.read_text(encoding="utf-8")
        return None

    instr_path = Path(instructions)
    if instr_path.is_file():
        return instr_path.read_text(encoding="utf-8")
    # Treat as inline markdown text
    return str(instructions)


def build_model(spec: ExtractionSpec) -> type[BaseModel]:
    """Build a dynamic Pydantic model from ``extraction.fields``."""
    return _build_object_model(
        name=_safe_model_name(spec.name),
        fields=spec.extraction.fields,
    )


def _safe_model_name(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in name.strip())
    return cleaned[:50] or "Document"


def _build_object_model(name: str, fields: dict[str, FieldSpec]) -> type[BaseModel]:
    definitions: dict[str, Any] = {}
    for field_name, field in fields.items():
        py_type, default = _python_type(field, field_name)
        definitions[field_name] = (
            py_type,
            Field(default=default, description=field.description or None),
        )
    return create_model(name, **definitions)  # type: ignore[call-overload]


def _python_type(field: FieldSpec, name: str) -> tuple[Any, Any]:
    """Return (annotation, default) for one field."""
    required = field.required
    default: Any = ... if required else None

    if field.type == "object":
        if not field.fields:
            raise SpecError(f"Field '{name}' type=object needs nested fields")
        nested = _build_object_model(f"{_safe_model_name(name)}Item", field.fields)
        annotation: Any = nested if required else nested | None
        return annotation, default

    if field.type == "array":
        if field.items is None:
            raise SpecError(f"Field '{name}' type=array needs items")
        # List elements are concrete types (not Optional).
        item_spec = field.items.model_copy(update={"required": True})
        item_type, _ = _python_type(item_spec, f"{name}_item")
        list_type: Any = list[item_type]  # type: ignore[valid-type]
        annotation = list_type if required else list_type | None
        return annotation, default

    base = _TYPE_MAP.get(field.type)
    if base is None:
        raise SpecError(f"Unsupported field type '{field.type}' on '{name}'")

    annotation = base if required else base | None
    return annotation, default
