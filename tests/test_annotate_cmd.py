"""Tests for envdiff.commands.annotate_cmd."""
import json
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.commands.annotate_cmd import cmd_annotate


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def write_env(path: Path, contents: str) -> str:
    path.write_text(contents)
    return str(path)


def make_args(file, fmt="text", show_values=False, allow_lowercase=False, sensitive_patterns=""):
    return Namespace(
        file=file,
        format=fmt,
        show_values=show_values,
        allow_lowercase=allow_lowercase,
        sensitive_patterns=sensitive_patterns,
    )


def test_missing_file_returns_two(env_dir):
    args = make_args(str(env_dir / "missing.env"))
    assert cmd_annotate(args) == 2


def test_valid_env_returns_zero(env_dir):
    f = write_env(env_dir / ".env", "APP_NAME=myapp\n")
    args = make_args(f)
    assert cmd_annotate(args) == 0


def test_json_output_structure(env_dir, capsys):
    f = write_env(env_dir / ".env", "APP_NAME=myapp\nSECRET_KEY=s3cr3t\n")
    args = make_args(f, fmt="json")
    rc = cmd_annotate(args)
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "source" in data
    assert "keys" in data
    keys_by_name = {k["key"]: k for k in data["keys"]}
    assert "APP_NAME" in keys_by_name
    assert "SECRET_KEY" in keys_by_name
    assert keys_by_name["SECRET_KEY"]["sensitive"] is True


def test_sensitive_value_redacted_by_default(env_dir, capsys):
    f = write_env(env_dir / ".env", "SECRET_KEY=topsecret\n")
    args = make_args(f, show_values=False)
    cmd_annotate(args)
    out = capsys.readouterr().out
    assert "topsecret" not in out
    assert "***" in out


def test_show_values_reveals_sensitive(env_dir, capsys):
    f = write_env(env_dir / ".env", "SECRET_KEY=topsecret\n")
    args = make_args(f, show_values=True)
    cmd_annotate(args)
    out = capsys.readouterr().out
    assert "topsecret" in out


def test_text_output_summary_line(env_dir, capsys):
    f = write_env(env_dir / ".env", "APP_NAME=x\nSECRET_KEY=s\n")
    args = make_args(f)
    cmd_annotate(args)
    out = capsys.readouterr().out
    assert "2 keys" in out
    assert "1 sensitive" in out


def test_extra_sensitive_patterns(env_dir, capsys):
    f = write_env(env_dir / ".env", "MY_CRED=abc\n")
    args = make_args(f, fmt="json", sensitive_patterns="CRED")
    cmd_annotate(args)
    data = json.loads(capsys.readouterr().out)
    assert data["keys"][0]["sensitive"] is True
