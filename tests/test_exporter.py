"""Tests for envdiff.exporter."""

from __future__ import annotations

import json
import csv
from pathlib import Path

import pytest

from envdiff.diff import EnvDiffResult
from envdiff.validator import ValidationResult
from envdiff.exporter import ExportError, ExportFormat, export


@pytest.fixture()
def diff_result() -> EnvDiffResult:
    return EnvDiffResult(
        base_name=".env.base",
        compare_name=".env.prod",
        missing_in_compare={"SECRET_KEY"},
        missing_in_base={"NEW_FLAG"},
        mismatched={"DB_HOST": ("localhost", "db.prod.example.com")},
    )


@pytest.fixture()
def validation_result() -> ValidationResult:
    return ValidationResult(
        missing_required={"API_KEY"},
        type_errors={"PORT": ("int", "str")},
    )


def test_export_diff_json(tmp_path: Path, diff_result: EnvDiffResult) -> None:
    dest = tmp_path / "out.json"
    export(diff_result, ExportFormat.JSON, dest)
    data = json.loads(dest.read_text())
    assert data["base"] == ".env.base"
    assert data["compare"] == ".env.prod"
    assert "SECRET_KEY" in data["missing_in_compare"]
    assert "NEW_FLAG" in data["missing_in_base"]
    assert data["mismatched"][0]["key"] == "DB_HOST"


def test_export_diff_csv(tmp_path: Path, diff_result: EnvDiffResult) -> None:
    dest = tmp_path / "out.csv"
    export(diff_result, ExportFormat.CSV, dest)
    rows = list(csv.DictReader(dest.read_text().splitlines()))
    issues = {r["issue"] for r in rows}
    keys = {r["key"] for r in rows}
    assert "missing_in_compare" in issues
    assert "missing_in_base" in issues
    assert "mismatch" in issues
    assert "SECRET_KEY" in keys
    assert "NEW_FLAG" in keys
    assert "DB_HOST" in keys


def test_export_validation_json(tmp_path: Path, validation_result: ValidationResult) -> None:
    dest = tmp_path / "validation.json"
    export(validation_result, ExportFormat.JSON, dest)
    data = json.loads(dest.read_text())
    assert data["valid"] is False
    assert "API_KEY" in data["missing_required"]
    assert data["type_errors"][0]["key"] == "PORT"


def test_export_validation_csv(tmp_path: Path, validation_result: ValidationResult) -> None:
    dest = tmp_path / "validation.csv"
    export(validation_result, ExportFormat.CSV, dest)
    rows = list(csv.DictReader(dest.read_text().splitlines()))
    issues = {r["issue"] for r in rows}
    assert "missing_required" in issues
    assert "type_error" in issues


def test_export_creates_parent_dirs(tmp_path: Path, diff_result: EnvDiffResult) -> None:
    dest = tmp_path / "nested" / "dir" / "out.json"
    export(diff_result, ExportFormat.JSON, dest)
    assert dest.exists()


def test_export_csv_mismatch_detail(tmp_path: Path, diff_result: EnvDiffResult) -> None:
    dest = tmp_path / "out.csv"
    export(diff_result, ExportFormat.CSV, dest)
    rows = list(csv.DictReader(dest.read_text().splitlines()))
    mismatch_row = next(r for r in rows if r["issue"] == "mismatch")
    assert "localhost" in mismatch_row["detail"]
    assert "db.prod.example.com" in mismatch_row["detail"]


def test_export_unsupported_type_raises(tmp_path: Path) -> None:
    with pytest.raises(ExportError, match="Unsupported result type"):
        export(object(), ExportFormat.JSON, tmp_path / "out.json")  # type: ignore[arg-type]
