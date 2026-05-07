"""Tests for envdiff.baseline."""

from __future__ import annotations

import json
import os
import pytest

from envdiff.baseline import BaselineError, compare_against_latest, compare_against_snapshot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_snapshot(path: str, name: str, env: dict[str, str]) -> None:
    data = {"version": 1, "name": name, "env": env, "created_at": "2024-01-01T00:00:00"}
    with open(path, "w") as fh:
        json.dump(data, fh)


# ---------------------------------------------------------------------------
# compare_against_snapshot
# ---------------------------------------------------------------------------

def test_compare_no_differences(tmp_path):
    snap_file = str(tmp_path / "snap.json")
    env = {"KEY": "value", "PORT": "8080"}
    write_snapshot(snap_file, "prod", env)

    result = compare_against_snapshot(env, snap_file)
    assert not result.diff.missing_in_compare
    assert not result.diff.missing_in_base
    assert not result.diff.mismatched
    assert result.snapshot_name == "prod"


def test_compare_detects_missing_in_current(tmp_path):
    snap_file = str(tmp_path / "snap.json")
    write_snapshot(snap_file, "prod", {"KEY": "val", "SECRET": "s3cr3t"})

    result = compare_against_snapshot({"KEY": "val"}, snap_file)
    assert "SECRET" in result.diff.missing_in_compare


def test_compare_detects_new_keys_in_current(tmp_path):
    snap_file = str(tmp_path / "snap.json")
    write_snapshot(snap_file, "prod", {"KEY": "val"})

    result = compare_against_snapshot({"KEY": "val", "NEW": "thing"}, snap_file)
    assert "NEW" in result.diff.missing_in_base


def test_compare_detects_value_mismatch(tmp_path):
    snap_file = str(tmp_path / "snap.json")
    write_snapshot(snap_file, "prod", {"KEY": "old"})

    result = compare_against_snapshot({"KEY": "new"}, snap_file, check_values=True)
    assert "KEY" in result.diff.mismatched


def test_compare_missing_file_raises(tmp_path):
    with pytest.raises(BaselineError):
        compare_against_snapshot({}, str(tmp_path / "nope.json"))


def test_compare_invalid_env_field_raises(tmp_path):
    snap_file = str(tmp_path / "bad.json")
    with open(snap_file, "w") as fh:
        json.dump({"version": 1, "name": "x", "env": "not-a-dict"}, fh)
    with pytest.raises(BaselineError):
        compare_against_snapshot({}, snap_file)


# ---------------------------------------------------------------------------
# compare_against_latest
# ---------------------------------------------------------------------------

def test_compare_latest_returns_none_when_no_history(tmp_path):
    result = compare_against_latest({"A": "1"}, str(tmp_path / "history"))
    assert result is None


def test_compare_latest_uses_most_recent(tmp_path):
    from envdiff.history import SnapshotHistory
    from envdiff.diff import EnvDiffResult

    history = SnapshotHistory(str(tmp_path / "history"))
    snap1 = EnvDiffResult(
        base_name="snap", compare_name="c",
        missing_in_compare=[], missing_in_base=[], mismatched={}
    )
    # Save two snapshots; the second should be used
    history.save(snap1, name="snap-old")
    history.save(snap1, name="snap-new")

    result = compare_against_latest({}, str(tmp_path / "history"))
    assert result is not None
    assert result.snapshot_name == "snap-new"
