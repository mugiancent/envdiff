"""Tests for envdiff.commands.baseline_cmd."""

from __future__ import annotations

import json
import os
from argparse import Namespace

import pytest

from envdiff.commands.baseline_cmd import cmd_baseline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_env(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


def write_snapshot(path: str, name: str, env: dict) -> None:
    data = {"version": 1, "name": name, "env": env, "created_at": "2024-01-01T00:00:00"}
    with open(path, "w") as fh:
        json.dump(data, fh)


def make_args(env_file: str, snapshot: str | None = None, **kwargs) -> Namespace:
    defaults = {
        "env_file": env_file,
        "snapshot": snapshot,
        "format": "text",
        "ignore_values": False,
        "history_dir": ".envdiff_history",
    }
    defaults.update(kwargs)
    return Namespace(**defaults)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_differences_returns_zero(tmp_path):
    env_file = str(tmp_path / ".env")
    snap_file = str(tmp_path / "snap.json")
    write_env(env_file, "KEY=value\nPORT=8080\n")
    write_snapshot(snap_file, "prod", {"KEY": "value", "PORT": "8080"})

    args = make_args(env_file, snapshot=snap_file)
    assert cmd_baseline(args) == 0


def test_differences_return_one(tmp_path):
    env_file = str(tmp_path / ".env")
    snap_file = str(tmp_path / "snap.json")
    write_env(env_file, "KEY=value\n")
    write_snapshot(snap_file, "prod", {"KEY": "value", "MISSING": "x"})

    args = make_args(env_file, snapshot=snap_file)
    assert cmd_baseline(args) == 1


def test_missing_env_file_returns_two(tmp_path):
    snap_file = str(tmp_path / "snap.json")
    write_snapshot(snap_file, "prod", {})

    args = make_args(str(tmp_path / "nope.env"), snapshot=snap_file)
    assert cmd_baseline(args) == 2


def test_missing_snapshot_returns_two(tmp_path):
    env_file = str(tmp_path / ".env")
    write_env(env_file, "KEY=val\n")

    args = make_args(env_file, snapshot=str(tmp_path / "nope.json"))
    assert cmd_baseline(args) == 2


def test_no_history_returns_two(tmp_path):
    env_file = str(tmp_path / ".env")
    write_env(env_file, "KEY=val\n")

    args = make_args(env_file, snapshot=None, history_dir=str(tmp_path / "empty_hist"))
    assert cmd_baseline(args) == 2


def test_uses_latest_snapshot_from_history(tmp_path):
    from envdiff.history import SnapshotHistory
    from envdiff.diff import EnvDiffResult

    env_file = str(tmp_path / ".env")
    write_env(env_file, "KEY=val\n")

    history = SnapshotHistory(str(tmp_path / "hist"))
    snap = EnvDiffResult(
        base_name="s", compare_name="c",
        missing_in_compare=[], missing_in_base=[], mismatched={}
    )
    history.save(snap, name="latest")

    args = make_args(env_file, snapshot=None, history_dir=str(tmp_path / "hist"))
    # Should not return 2 (history exists)
    rc = cmd_baseline(args)
    assert rc in (0, 1)
