"""Export diff or validation results to various file formats."""

from __future__ import annotations

import csv
import io
import json
from enum import Enum
from pathlib import Path
from typing import Union

from envdiff.diff import EnvDiffResult
from envdiff.validator import ValidationResult


class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"


class ExportError(Exception):
    """Raised when export fails."""


def _diff_to_dict(result: EnvDiffResult) -> dict:
    return {
        "base": result.base_name,
        "compare": result.compare_name,
        "missing_in_compare": list(result.missing_in_compare),
        "missing_in_base": list(result.missing_in_base),
        "mismatched": [
            {"key": k, "base_value": bv, "compare_value": cv}
            for k, (bv, cv) in result.mismatched.items()
        ],
    }


def _validation_to_dict(result: ValidationResult) -> dict:
    return {
        "valid": result.is_valid,
        "missing_required": list(result.missing_required),
        "type_errors": [
            {"key": k, "expected": exp, "actual": act}
            for k, (exp, act) in result.type_errors.items()
        ],
    }


def _to_csv_rows(data: dict) -> list[dict]:
    rows = []
    for key in data.get("missing_in_compare", []):
        rows.append({"issue": "missing_in_compare", "key": key, "detail": ""})
    for key in data.get("missing_in_base", []):
        rows.append({"issue": "missing_in_base", "key": key, "detail": ""})
    for item in data.get("mismatched", []):
        rows.append({
            "issue": "mismatch",
            "key": item["key"],
            "detail": f"{item['base_value']} -> {item['compare_value']}",
        })
    for key in data.get("missing_required", []):
        rows.append({"issue": "missing_required", "key": key, "detail": ""})
    for item in data.get("type_errors", []):
        rows.append({
            "issue": "type_error",
            "key": item["key"],
            "detail": f"expected {item['expected']}, got {item['actual']}",
        })
    return rows


def export(
    result: Union[EnvDiffResult, ValidationResult],
    fmt: ExportFormat,
    dest: Path,
) -> None:
    """Serialize *result* to *dest* in the requested *fmt*."""
    if isinstance(result, EnvDiffResult):
        data = _diff_to_dict(result)
    elif isinstance(result, ValidationResult):
        data = _validation_to_dict(result)
    else:
        raise ExportError(f"Unsupported result type: {type(result)}")

    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if fmt == ExportFormat.JSON:
            dest.write_text(json.dumps(data, indent=2), encoding="utf-8")
        elif fmt == ExportFormat.CSV:
            rows = _to_csv_rows(data)
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=["issue", "key", "detail"])
            writer.writeheader()
            writer.writerows(rows)
            dest.write_text(buf.getvalue(), encoding="utf-8")
        else:
            raise ExportError(f"Unknown format: {fmt}")
    except OSError as exc:
        raise ExportError(f"Failed to write export file: {exc}") from exc
