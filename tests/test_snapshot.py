"""Tests for envdiff.snapshot (save/load EnvDiffResult)."""

from __future__ import annotations

import json
import pytest

from envdiff.diff import EnvDiffResult
from envdiff.snapshot import SnapshotError, load_snapshot, save_snapshot


@pytest.fixture()
def sample_result() -> EnvDiffResult:
    return EnvDiffResult(
        base=".env.staging",
        compare=".env.production",
        missing_in_compare={"SECRET_KEY"},
        missing_in_base={"NEW_FEATURE_FLAG"},
        mismatched={"DATABASE_URL": ("postgres://old", "postgres://new")},
    )


def test_save_and_load_roundtrip(tmp_path, sample_result):
    snap = tmp_path / "snap.json"
    save_snapshot(sample_result, snap)
    loaded = load_snapshot(snap)

    assert loaded.base == sample_result.base
    assert loaded.compare == sample_result.compare
    assert loaded.missing_in_compare == sample_result.missing_in_compare
    assert loaded.missing_in_base == sample_result.missing_in_base
    assert loaded.mismatched == sample_result.mismatched


def test_snapshot_file_contains_version(tmp_path, sample_result):
    snap = tmp_path / "snap.json"
    save_snapshot(sample_result, snap)
    data = json.loads(snap.read_text())
    assert data["version"] == 1


def test_snapshot_file_contains_created_at(tmp_path, sample_result):
    snap = tmp_path / "snap.json"
    save_snapshot(sample_result, snap)
    data = json.loads(snap.read_text())
    assert "created_at" in data


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(SnapshotError, match="Could not read"):
        load_snapshot(tmp_path / "nonexistent.json")


def test_load_invalid_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    with pytest.raises(SnapshotError, match="Invalid JSON"):
        load_snapshot(bad)


def test_load_wrong_version_raises(tmp_path):
    snap = tmp_path / "snap.json"
    snap.write_text(json.dumps({"version": 99}), encoding="utf-8")
    with pytest.raises(SnapshotError, match="Unsupported snapshot version"):
        load_snapshot(snap)


def test_load_missing_field_raises(tmp_path):
    snap = tmp_path / "snap.json"
    snap.write_text(json.dumps({"version": 1, "base": "a"}), encoding="utf-8")
    with pytest.raises(SnapshotError, match="missing required field"):
        load_snapshot(snap)


def test_save_to_bad_path_raises():
    with pytest.raises(SnapshotError, match="Could not write"):
        save_snapshot(
            EnvDiffResult(
                base="a", compare="b",
                missing_in_compare=set(), missing_in_base=set(), mismatched={}
            ),
            "/no/such/directory/snap.json",
        )
