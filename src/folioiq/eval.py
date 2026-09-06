"""Simple fixture-pack evaluation."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from folioiq.client import DocumentExtractor
from folioiq.exceptions import FolioIQError


@dataclass
class FieldScore:
    name: str
    expected: Any
    actual: Any
    match: bool


@dataclass
class PackReport:
    pack: str
    field_scores: list[FieldScore] = field(default_factory=list)
    is_valid: bool = False
    validation_errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    skipped: bool = False
    skip_reason: str = ""

    @property
    def scored(self) -> list[FieldScore]:
        return [f for f in self.field_scores if f.expected is not None]

    @property
    def accuracy(self) -> float:
        scored = self.scored
        if not scored:
            return 0.0
        return sum(1 for f in scored if f.match) / len(scored)


def normalize_value(value: Any) -> str:
    """Loose compare for eval (case/whitespace/punctuation tolerant)."""
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    if isinstance(value, int):
        return str(value)
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[,\s]+", " ", text)
    return text.strip()


def values_match(expected: Any, actual: Any) -> bool:
    if expected is None:
        return True
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return abs(float(expected) - float(actual)) < 0.01
    exp = normalize_value(expected)
    act = normalize_value(actual)
    if not exp:
        return True
    return exp == act or exp in act or act in exp


def score_fields(expected: dict[str, Any], actual: dict[str, Any]) -> list[FieldScore]:
    scores: list[FieldScore] = []
    for key, exp in expected.items():
        if key.startswith("_"):
            continue
        act = actual.get(key)
        scores.append(
            FieldScore(
                name=key,
                expected=exp,
                actual=act,
                match=values_match(exp, act),
            )
        )
    return scores


def find_document(pack_dir: Path) -> Path:
    for name in ("document.pdf", "document.jpg", "document.jpeg", "document.png"):
        path = pack_dir / name
        if path.is_file():
            return path
    raise FolioIQError(f"No document.* found in {pack_dir}")


def run_pack(
    pack_dir: str | Path,
    extractor: DocumentExtractor | None = None,
) -> PackReport:
    """Run one fixture pack and score against expected.json."""
    pack = Path(pack_dir).resolve()
    report = PackReport(pack=pack.name)

    expected_path = pack / "expected.json"
    spec_path = pack / "spec.yaml"
    if not expected_path.is_file() or not spec_path.is_file():
        report.skipped = True
        report.skip_reason = "missing spec.yaml or expected.json"
        return report

    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    # Pack with only null expectations is a placeholder
    if all(v is None for k, v in expected.items() if not k.startswith("_")):
        report.skipped = True
        report.skip_reason = "expected.json has no labeled values yet"
        return report

    document = find_document(pack)
    instructions = pack / "instructions.md"
    extractor = extractor or DocumentExtractor.from_env()
    result = extractor.extract(
        document,
        spec=spec_path,
        instructions=instructions if instructions.is_file() else None,
    )

    report.is_valid = result.is_valid
    report.validation_errors = list(result.validation_errors)
    report.metadata = dict(result.metadata)
    report.field_scores = score_fields(expected, result.data)
    return report


def format_report(report: PackReport) -> str:
    lines = [f"pack: {report.pack}"]
    if report.skipped:
        lines.append(f"  skipped: {report.skip_reason}")
        return "\n".join(lines)
    lines.append(f"  is_valid: {report.is_valid}")
    lines.append(f"  accuracy: {report.accuracy:.1%} ({sum(1 for f in report.scored if f.match)}/{len(report.scored)})")
    lines.append(f"  parser: {report.metadata.get('parser')}")
    lines.append(f"  fallback_used: {report.metadata.get('fallback_used')}")
    if report.validation_errors:
        lines.append(f"  validation_errors: {report.validation_errors}")
    for fs in report.field_scores:
        if fs.expected is None:
            continue
        mark = "OK" if fs.match else "MISS"
        lines.append(f"  [{mark}] {fs.name}: expected={fs.expected!r} actual={fs.actual!r}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate FolioIQ fixture packs")
    parser.add_argument(
        "pack",
        nargs="?",
        default=None,
        help="Pack directory (default: all under tests/fixtures/packs)",
    )
    args = parser.parse_args(argv)

    if args.pack:
        packs = [Path(args.pack)]
    else:
        root = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "packs"
        if not root.is_dir():
            # installed package — look relative to cwd
            root = Path("tests/fixtures/packs")
        packs = sorted(p for p in root.iterdir() if p.is_dir())

    extractor = DocumentExtractor.from_env()
    exit_code = 0
    for pack in packs:
        report = run_pack(pack, extractor=extractor)
        print(format_report(report))
        print()
        if report.skipped:
            continue
        if report.accuracy < 1.0 or not report.is_valid:
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
