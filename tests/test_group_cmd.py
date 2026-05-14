"""Tests for envdiff.commands.group_cmd."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.commands.group_cmd import cmd_group


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def write_env(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def make_args(file: str, **kwargs) -> argparse.Namespace:
    defaults = dict(
        file=file,
        separator="_",
        min_group_size=2,
        summary=False,
        hide_ungrouped=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_missing_file_returns_two(env_dir: Path):
    args = make_args(str(env_dir / "missing.env"))
    assert cmd_group(args) == 2


def test_valid_env_returns_zero(env_dir: Path, capsys):
    f = write_env(env_dir / ".env", "DB_HOST=localhost\nDB_PORT=5432\nPORT=8080\n")
    args = make_args(str(f))
    assert cmd_group(args) == 0


def test_output_contains_group_name(env_dir: Path, capsys):
    f = write_env(env_dir / ".env", "DB_HOST=localhost\nDB_PORT=5432\n")
    args = make_args(str(f))
    cmd_group(args)
    out = capsys.readouterr().out
    assert "[DB]" in out


def test_ungrouped_keys_shown_by_default(env_dir: Path, capsys):
    f = write_env(env_dir / ".env", "DB_HOST=localhost\nDB_PORT=5432\nPORT=8080\n")
    args = make_args(str(f))
    cmd_group(args)
    out = capsys.readouterr().out
    assert "ungrouped" in out
    assert "PORT" in out


def test_hide_ungrouped_suppresses_section(env_dir: Path, capsys):
    f = write_env(env_dir / ".env", "DB_HOST=localhost\nDB_PORT=5432\nPORT=8080\n")
    args = make_args(str(f), hide_ungrouped=True)
    cmd_group(args)
    out = capsys.readouterr().out
    assert "ungrouped" not in out


def test_summary_flag_prints_compact_output(env_dir: Path, capsys):
    f = write_env(env_dir / ".env", "DB_HOST=localhost\nDB_PORT=5432\nPORT=8080\n")
    args = make_args(str(f), summary=True)
    cmd_group(args)
    out = capsys.readouterr().out
    assert "Groups:" in out


def test_custom_separator(env_dir: Path, capsys):
    f = write_env(env_dir / ".env", "APP.HOST=localhost\nAPP.PORT=8080\nDEBUG=true\n")
    args = make_args(str(f), separator=".")
    cmd_group(args)
    out = capsys.readouterr().out
    assert "[APP]" in out
