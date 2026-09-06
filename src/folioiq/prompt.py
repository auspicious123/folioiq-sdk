"""Build extraction prompts from a loaded spec."""

from __future__ import annotations

from folioiq.specs import ExtractionSpec, FieldSpec


def build_extraction_prompt(spec: ExtractionSpec) -> str:
    """Human prompt: instructions + field list. Schema is enforced by the LLM client."""
    lines: list[str] = []

    if spec.instructions:
        lines.append(spec.instructions.strip())
        lines.append("")

    lines.append(f"Extract fields for document type: {spec.name} (v{spec.version}).")
    lines.append("Return only values found in the document. Use null when missing.")
    lines.append("")
    lines.append("Fields:")
    for name, field in spec.extraction.fields.items():
        lines.extend(_describe_field(name, field, indent=0))

    return "\n".join(lines)


def _describe_field(name: str, field: FieldSpec, indent: int) -> list[str]:
    pad = "  " * indent
    req = "required" if field.required else "optional"
    lines = [f"{pad}- {name} ({field.type}, {req})"]
    if field.description:
        lines.append(f"{pad}  {field.description.strip()}")
    if field.type == "object" and field.fields:
        for child_name, child in field.fields.items():
            lines.extend(_describe_field(child_name, child, indent + 1))
    if field.type == "array" and field.items is not None:
        lines.append(f"{pad}  items:")
        if field.items.type == "object" and field.items.fields:
            for child_name, child in field.items.fields.items():
                lines.extend(_describe_field(child_name, child, indent + 2))
        else:
            lines.extend(_describe_field("item", field.items, indent + 2))
    return lines
