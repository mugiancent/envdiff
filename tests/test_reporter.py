"""Tests for envdiff.reporter."""

from __future__ import annotations

import json
import io

import pytest

from envdiff.diff import EnvDiffResult
from envdiff.reporter import OutputFormat, render


@pytest.fixture()
def sample_result() -> EnvDiffResult:
    return EnvDiffResult(
        missing_in_compare={"SECRET_KEY"},
        missing_in_base={"NEW_FEATURE_FLAG"},
        mismatched_values={"DATABASE_URL": ("postgres://old", "postgres://new")},
    )


@pytest.fixture()
def clean_result() -> EnvDiffResult:
    return EnvDiffResult(
        missing_in_compare=set(),
        missing_in_base=set(),
        mismatched_values={},
    )


def test_text_output_contains_base_and_compare_names(sample_result):
    buf = io.StringIO()
    output = render(sample_result, "base.env", "prod.env", OutputFormat.TEXT, stream=buf)
    assert "base.env" in output
    assert "prod.env" in output


def test_text_output_lists_missing_keys(sample_result):
    buf = io.StringIO()
    output = render(sample_result, "base.env", "prod.env", OutputFormat.TEXT, stream=buf)
    assert "SECRET_KEY" in output
    assert "NEW_FEATURE_FLAG" in output


def test_text_output_lists_mismatch(sample_result):
    buf = io.StringIO()
    output = render(sample_result, "base.env", "prod.env", OutputFormat.TEXT, stream=buf)
    assert "DATABASE_URL" in output
    assert "postgres://old" in output
    assert "postgres://new" in output


def test_text_output_no_differences(clean_result):
    buf = io.StringIO()
    output = render(clean_result, "a.env", "b.env", OutputFormat.TEXT, stream=buf)
    assert "No differences found" in output


def test_json_output_is_valid_json(sample_result):
    buf = io.StringIO()
    output = render(sample_result, "base.env", "prod.env", OutputFormat.JSON, stream=buf)
    data = json.loads(output)
    assert data["base"] == "base.env"
    assert data["compare"] == "prod.env"
    assert "SECRET_KEY" in data["missing_in_compare"]
    assert "NEW_FEATURE_FLAG" in data["missing_in_base"]
    assert "DATABASE_URL" in data["mismatched_values"]
    assert data["mismatched_values"]["DATABASE_URL"]["base"] == "postgres://old"


def test_json_output_clean_result(clean_result):
    buf = io.StringIO()
    output = render(clean_result, "a.env", "b.env", OutputFormat.JSON, stream=buf)
    data = json.loads(output)
    assert data["missing_in_compare"] == []
    assert data["missing_in_base"] == []
    assert data["mismatched_values"] == {}


def test_markdown_output_contains_table_header(sample_result):
    buf = io.StringIO()
    output = render(sample_result, "base.env", "prod.env", OutputFormat.MARKDOWN, stream=buf)
    assert "| Key |" in output
    assert "DATABASE_URL" in output


def test_markdown_output_no_differences(clean_result):
    buf = io.StringIO()
    output = render(clean_result, "a.env", "b.env", OutputFormat.MARKDOWN, stream=buf)
    assert "No differences found" in output


def test_render_returns_string_and_writes_to_stream(sample_result):
    buf = io.StringIO()
    result = render(sample_result, "base.env", "prod.env", OutputFormat.TEXT, stream=buf)
    assert isinstance(result, str)
    written = buf.getvalue()
    assert result.strip() in written
