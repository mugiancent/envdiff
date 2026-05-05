"""Tests for envdiff.history (SnapshotHistory)."""

from __future__ import annotations

import pytest

from envdiff.diff import EnvDiffResult
from envdiff.history import HistoryError, SnapshotHistory


@pytest.fixture()
def result() -> EnvDiffResult:
    return EnvDiffResult(
        base=".env.dev",
        compare=".env.prod",
        missing_in_compare={"API_KEY"},
        missing_in_base=set(),
        mismatched={},
    )


@pytest.fixture()
def history(tmp_path) -> SnapshotHistory:
    return SnapshotHistory(tmp_path / "snapshots")


def test_save_and_list(history, result):
    history.save(result, "run-001")
    assert history.list_snapshots() == ["run-001"]


def test_save_and_load(history, result):
    history.save(result, "run-001")
    loaded = history.load("run-001")
    assert loaded.base == result.base
    assert loaded.missing_in_compare == result.missing_in_compare


def test_list_empty_when_dir_missing(tmp_path):
    h = SnapshotHistory(tmp_path / "nonexistent")
    assert h.list_snapshots() == []


def test_list_sorted(history, result):
    history.save(result, "run-003")
    history.save(result, "run-001")
    history.save(result, "run-002")
    assert history.list_snapshots() == ["run-001", "run-002", "run-003"]


def test_delete_removes_snapshot(history, result):
    history.save(result, "run-001")
    history.delete("run-001")
    assert history.list_snapshots() == []


def test_delete_missing_raises(history):
    with pytest.raises(HistoryError, match="not found"):
        history.delete("ghost")


def test_invalid_name_raises(history, result):
    with pytest.raises(HistoryError, match="Invalid snapshot name"):
        history.save(result, "a/b")


def test_load_missing_raises(history):
    with pytest.raises(HistoryError):
        history.load("nonexistent")


def test_iter_all(history, result):
    history.save(result, "run-001")
    history.save(result, "run-002")
    items = list(history.iter_all())
    assert [name for name, _ in items] == ["run-001", "run-002"]
    assert all(isinstance(r, EnvDiffResult) for _, r in items)
