"""Tests for envdiff.watcher."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envdiff.watcher import watch, WatcherError, _snapshot_file


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_env(path: Path, content: str) -> None:
    path.write_text(content)


# ---------------------------------------------------------------------------
# _snapshot_file
# ---------------------------------------------------------------------------

def test_snapshot_file_reads_contents(tmp_path):
    f = tmp_path / ".env"
    write_env(f, "KEY=value\nOTHER=123\n")
    state = _snapshot_file(f)
    assert state.contents == {"KEY": "value", "OTHER": "123"}
    assert state.mtime == f.stat().st_mtime


# ---------------------------------------------------------------------------
# watch – startup errors
# ---------------------------------------------------------------------------

def test_watch_raises_if_base_missing(tmp_path):
    compare = tmp_path / "compare.env"
    write_env(compare, "A=1\n")
    with pytest.raises(WatcherError, match="not found"):
        watch(tmp_path / "missing.env", compare, lambda r: None, max_iterations=0)


def test_watch_raises_if_compare_missing(tmp_path):
    base = tmp_path / "base.env"
    write_env(base, "A=1\n")
    with pytest.raises(WatcherError, match="not found"):
        watch(base, tmp_path / "missing.env", lambda r: None, max_iterations=0)


# ---------------------------------------------------------------------------
# watch – no change within iterations
# ---------------------------------------------------------------------------

def test_watch_no_change_callback_not_called(tmp_path):
    base = tmp_path / "base.env"
    compare = tmp_path / "compare.env"
    write_env(base, "A=1\n")
    write_env(compare, "A=1\n")

    calls = []
    watch(base, compare, calls.append, poll_interval=0, max_iterations=2)
    assert calls == []


# ---------------------------------------------------------------------------
# watch – detects change
# ---------------------------------------------------------------------------

def test_watch_detects_modification(tmp_path):
    base = tmp_path / "base.env"
    compare = tmp_path / "compare.env"
    write_env(base, "A=1\n")
    write_env(compare, "A=1\n")

    results = []
    iteration = [0]

    original_watch = watch

    # Simulate a change by patching mtime after first iteration.
    # We use a small wrapper that mutates the file on iteration 1.
    def on_change(result):
        results.append(result)

    def side_effect_watch():
        import envdiff.watcher as _w
        import unittest.mock as mock

        orig_sleep = _w.time.sleep

        call_count = [0]

        def fake_sleep(_):
            call_count[0] += 1
            if call_count[0] == 1:
                # Modify compare file to trigger change detection
                write_env(compare, "A=1\nB=2\n")

        with mock.patch.object(_w.time, "sleep", fake_sleep):
            original_watch(base, compare, on_change, poll_interval=0, max_iterations=2)

    side_effect_watch()

    assert len(results) == 1
    result = results[0]
    assert "B" in result.missing_in_base
