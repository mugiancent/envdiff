"""Tests for envdiff.differ_summary (multi-file diff report)."""

from __future__ import annotations

import os
import pytest

from envdiff.differ_summary import multi_diff, MultiDiffReport, MultiDiffEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_env(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(content)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_clean_report_when_all_identical(env_dir):
    base = str(env_dir / "base.env")
    comp = str(env_dir / "comp.env")
    write_env(base, "FOO=bar\nBAZ=qux\n")
    write_env(comp, "FOO=bar\nBAZ=qux\n")

    report = multi_diff(base, [comp])
    assert report.clean is True
    assert report.total_issues == 0


def test_report_detects_missing_in_compare(env_dir):
    base = str(env_dir / "base.env")
    comp = str(env_dir / "comp.env")
    write_env(base, "FOO=bar\nMISSING=value\n")
    write_env(comp, "FOO=bar\n")

    report = multi_diff(base, [comp])
    assert report.clean is False
    assert report.total_issues == 1
    entry = report.entries[0]
    assert "MISSING" in entry.result.missing_in_compare


def test_report_detects_missing_in_base(env_dir):
    base = str(env_dir / "base.env")
    comp = str(env_dir / "comp.env")
    write_env(base, "FOO=bar\n")
    write_env(comp, "FOO=bar\nEXTRA=yes\n")

    report = multi_diff(base, [comp])
    entry = report.entries[0]
    assert "EXTRA" in entry.result.missing_in_base


def test_report_detects_value_mismatch(env_dir):
    base = str(env_dir / "base.env")
    comp = str(env_dir / "comp.env")
    write_env(base, "FOO=original\n")
    write_env(comp, "FOO=changed\n")

    report = multi_diff(base, [comp], check_values=True)
    entry = report.entries[0]
    assert "FOO" in entry.result.mismatched


def test_check_values_false_ignores_mismatch(env_dir):
    base = str(env_dir / "base.env")
    comp = str(env_dir / "comp.env")
    write_env(base, "FOO=original\n")
    write_env(comp, "FOO=changed\n")

    report = multi_diff(base, [comp], check_values=False)
    assert report.clean is True


def test_multiple_compare_files(env_dir):
    base = str(env_dir / "base.env")
    comp1 = str(env_dir / "staging.env")
    comp2 = str(env_dir / "prod.env")
    write_env(base, "FOO=bar\nBAZ=qux\n")
    write_env(comp1, "FOO=bar\n")          # missing BAZ
    write_env(comp2, "FOO=bar\nBAZ=qux\n")  # identical

    report = multi_diff(base, [comp1, comp2])
    assert len(report.entries) == 2
    assert report.total_issues == 1


def test_per_file_summary_ok_label(env_dir):
    base = str(env_dir / "base.env")
    comp = str(env_dir / "comp.env")
    write_env(base, "FOO=bar\n")
    write_env(comp, "FOO=bar\n")

    report = multi_diff(base, [comp])
    summary = report.per_file_summary()
    assert summary["comp.env"] == "OK"


def test_per_file_summary_shows_counts(env_dir):
    base = str(env_dir / "base.env")
    comp = str(env_dir / "comp.env")
    write_env(base, "FOO=bar\nSECRET=x\n")
    write_env(comp, "FOO=changed\n")

    report = multi_diff(base, [comp])
    summary = report.per_file_summary()
    label = summary["comp.env"]
    assert "missing in compare" in label
    assert "mismatched" in label


def test_base_name_stored_on_report(env_dir):
    base = str(env_dir / "my_base.env")
    comp = str(env_dir / "comp.env")
    write_env(base, "A=1\n")
    write_env(comp, "A=1\n")

    report = multi_diff(base, [comp])
    assert report.base_name == "my_base.env"
