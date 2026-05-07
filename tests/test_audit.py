"""Tests for envdiff.audit."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.audit import (
    AuditEntry,
    AuditError,
    append_entry,
    clear_entries,
    load_entries,
)


@pytest.fixture()
def audit_dir(tmp_path: Path) -> Path:
    return tmp_path / "audit"


def make_entry(action: str = "diff", outcome: str = "ok", detail: str = "no issues") -> AuditEntry:
    return AuditEntry(action=action, outcome=outcome, detail=detail)


def test_append_and_load_single_entry(audit_dir: Path) -> None:
    entry = make_entry()
    append_entry(entry, audit_dir=audit_dir)
    loaded = load_entries(audit_dir=audit_dir)
    assert len(loaded) == 1
    assert loaded[0].action == "diff"
    assert loaded[0].outcome == "ok"


def test_multiple_entries_preserved_in_order(audit_dir: Path) -> None:
    append_entry(make_entry(action="diff", outcome="differences"), audit_dir=audit_dir)
    append_entry(make_entry(action="validate", outcome="invalid"), audit_dir=audit_dir)
    append_entry(make_entry(action="baseline", outcome="ok"), audit_dir=audit_dir)
    entries = load_entries(audit_dir=audit_dir)
    assert [e.action for e in entries] == ["diff", "validate", "baseline"]


def test_load_returns_empty_list_when_no_log(audit_dir: Path) -> None:
    result = load_entries(audit_dir=audit_dir)
    assert result == []


def test_entry_has_timestamp(audit_dir: Path) -> None:
    append_entry(make_entry(), audit_dir=audit_dir)
    entry = load_entries(audit_dir=audit_dir)[0]
    assert entry.timestamp  # non-empty string
    assert "T" in entry.timestamp  # ISO-8601 format


def test_entry_has_version(audit_dir: Path) -> None:
    append_entry(make_entry(), audit_dir=audit_dir)
    entry = load_entries(audit_dir=audit_dir)[0]
    assert entry.version == "1"


def test_clear_removes_all_entries(audit_dir: Path) -> None:
    append_entry(make_entry(), audit_dir=audit_dir)
    append_entry(make_entry(action="validate"), audit_dir=audit_dir)
    clear_entries(audit_dir=audit_dir)
    assert load_entries(audit_dir=audit_dir) == []


def test_clear_on_missing_dir_is_noop(audit_dir: Path) -> None:
    """clear_entries should not raise when the log does not exist."""
    clear_entries(audit_dir=audit_dir)  # must not raise


def test_audit_log_is_valid_jsonl(audit_dir: Path) -> None:
    for i in range(3):
        append_entry(make_entry(detail=f"entry {i}"), audit_dir=audit_dir)
    log_file = audit_dir / "audit.jsonl"
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 3
    for line in lines:
        obj = json.loads(line)
        assert "action" in obj
        assert "outcome" in obj
