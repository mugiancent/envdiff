"""Tests for envdiff.commands.diff_cmd."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.commands.diff_cmd import cmd_diff


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def write_env(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def test_no_differences_returns_zero(env_dir: Path) -> None:
    base = write_env(env_dir / ".env.base", "KEY=value\nFOO=bar\n")
    cmp = write_env(env_dir / ".env.cmp", "KEY=value\nFOO=bar\n")
    assert cmd_diff(str(base), str(cmp)) == 0


def test_differences_return_one(env_dir: Path) -> None:
    base = write_env(env_dir / ".env.base", "KEY=value\nONLY_BASE=x\n")
    cmp = write_env(env_dir / ".env.cmp", "KEY=value\n")
    assert cmd_diff(str(base), str(cmp)) == 1


def test_missing_base_file_returns_two(env_dir: Path) -> None:
    cmp = write_env(env_dir / ".env.cmp", "KEY=value\n")
    assert cmd_diff(str(env_dir / "nonexistent"), str(cmp)) == 2


def test_missing_compare_file_returns_two(env_dir: Path) -> None:
    base = write_env(env_dir / ".env.base", "KEY=value\n")
    assert cmd_diff(str(base), str(env_dir / "nonexistent")) == 2


def test_invalid_format_returns_two(env_dir: Path) -> None:
    base = write_env(env_dir / ".env.base", "KEY=value\n")
    cmp = write_env(env_dir / ".env.cmp", "KEY=value\n")
    assert cmd_diff(str(base), str(cmp), output_format="xml") == 2


def test_json_output_is_valid_json(env_dir: Path, capsys: pytest.CaptureFixture) -> None:
    base = write_env(env_dir / ".env.base", "KEY=value\n")
    cmp = write_env(env_dir / ".env.cmp", "KEY=other\n")
    cmd_diff(str(base), str(cmp), output_format="json")
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "mismatched" in data or "missing_in_compare" in data or "missing_in_base" in data


def test_ignore_keys_excludes_from_diff(env_dir: Path) -> None:
    base = write_env(env_dir / ".env.base", "KEY=value\nSECRET=abc\n")
    cmp = write_env(env_dir / ".env.cmp", "KEY=value\n")
    # Without ignore, SECRET missing → exit 1
    assert cmd_diff(str(base), str(cmp)) == 1
    # With ignore, no differences
    assert cmd_diff(str(base), str(cmp), ignore_keys=["SECRET"]) == 0


def test_save_snapshot_creates_file(env_dir: Path) -> None:
    base = write_env(env_dir / ".env.base", "KEY=value\n")
    cmp = write_env(env_dir / ".env.cmp", "KEY=value\n")
    snap = env_dir / "snap.json"
    cmd_diff(str(base), str(cmp), save=str(snap))
    assert snap.exists()
    data = json.loads(snap.read_text())
    assert "version" in data
