"""Post-extraction checks against the YAML spec."""

from __future__ import annotations

from typing import Any

from folioiq.specs import ExtractionSpec, FieldSpec


def validate_extraction(spec: ExtractionSpec, data: dict[str, Any]) -> list[str]:
    """Return human-readable errors. Empty list means OK."""
    errors: list[str] = []
    for name, field in spec.extraction.fields.items():
        errors.extend(_check_field(name, field, data.get(name)))
    return errors


def _check_field(name: str, field: FieldSpec, value: Any) -> list[str]:
    errors: list[str] = []

    if field.required and _is_empty(value):
        errors.append(f"missing required field: {name}")
        return errors

    if _is_empty(value):
        return errors

    if field.type == "array":
        if not isinstance(value, list):
            errors.append(f"field '{name}' should be an array")
            return errors
        if field.items is not None:
            for i, item in enumerate(value):
                if field.items.type == "object" and field.items.fields:
                    if not isinstance(item, dict):
                        errors.append(f"field '{name}[{i}]' should be an object")
                        continue
                    for child_name, child in field.items.fields.items():
                        errors.extend(
                            _check_field(f"{name}[{i}].{child_name}", child, item.get(child_name))
                        )
        return errors

    if field.type == "object":
        if not isinstance(value, dict):
            errors.append(f"field '{name}' should be an object")
            return errors
        if field.fields:
            for child_name, child in field.fields.items():
                errors.extend(
                    _check_field(f"{name}.{child_name}", child, value.get(child_name))
                )
        return errors

    expected = _simple_type(field.type)
    if expected is not None and not isinstance(value, expected):
        # JSON numbers may arrive as int for number fields — accept both
        if field.type == "number" and isinstance(value, (int, float)):
            return errors
        errors.append(
            f"field '{name}' expected {field.type}, got {type(value).__name__}"
        )
    return errors


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _simple_type(field_type: str) -> type | tuple[type, ...] | None:
    return {
        "string": str,
        "integer": int,
        "boolean": bool,
        "number": (int, float),
    }.get(field_type)
