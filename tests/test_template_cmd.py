"""Tests for envdiff.commands.template_cmd."""

import argparse
from pathlib import Path

import pytest

from envdiff.commands.template_cmd import cmd_template


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def write_env(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def make_args(env_file, output=None, no_mask=False, placeholder="", extra_patterns=None, header=None):
    ns = argparse.Namespace(
        env_file=str(env_file),
        output=output,
        no_mask=no_mask,
        placeholder=placeholder,
        extra_patterns=extra_patterns,
        header=header,
    )
    return ns


def test_missing_file_returns_two(env_dir):
    args = make_args(env_dir / "nonexistent.env")
    assert cmd_template(args) == 2


def test_valid_env_returns_zero(env_dir, capsys):
    f = write_env(env_dir / ".env", "APP=hello\nDEBUG=true\n")
    args = make_args(f)
    assert cmd_template(args) == 0


def test_stdout_contains_keys(env_dir, capsys):
    f = write_env(env_dir / ".env", "APP=hello\nPORT=9000\n")
    args = make_args(f)
    cmd_template(args)
    out = capsys.readouterr().out
    assert "APP=hello" in out
    assert "PORT=9000" in out


def test_sensitive_values_masked(env_dir, capsys):
    f = write_env(env_dir / ".env", "DB_PASSWORD=secret\nAPP=ok\n")
    args = make_args(f, placeholder="REDACTED")
    cmd_template(args)
    out = capsys.readouterr().out
    assert "DB_PASSWORD=REDACTED" in out
    assert "secret" not in out


def test_no_mask_exposes_values(env_dir, capsys):
    f = write_env(env_dir / ".env", "SECRET_KEY=abc123\n")
    args = make_args(f, no_mask=True)
    cmd_template(args)
    out = capsys.readouterr().out
    assert "SECRET_KEY=abc123" in out


def test_output_written_to_file(env_dir):
    f = write_env(env_dir / ".env", "APP=hello\n")
    out_file = env_dir / ".env.example"
    args = make_args(f, output=str(out_file))
    rc = cmd_template(args)
    assert rc == 0
    assert out_file.exists()
    assert "APP=hello" in out_file.read_text()


def test_header_appears_in_output(env_dir, capsys):
    f = write_env(env_dir / ".env", "APP=x\n")
    args = make_args(f, header="Do not commit this file")
    cmd_template(args)
    out = capsys.readouterr().out
    assert "# Do not commit this file" in out
