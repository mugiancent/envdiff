"""Tests for the validate CLI command."""

from __future__ import annotations

import json
from pathlib import Path
import types

import pytest

from envdiff.commands.validate_cmd import cmd_validate


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def write_env(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def write_schema(path: Path, content: str) -> Path:
    import json as _json
    path.write_text(_json.dumps(content))
    return path


def make_args(env_file: str, schema_file: str, fmt: str = "text") -> types.SimpleNamespace:
    return types.SimpleNamespace(env_file=env_file, schema_file=schema_file, format=fmt)


def test_valid_env_returns_zero(env_dir: Path) -> None:
    env_path = env_dir / ".env"
    schema_path = env_dir / "schema.json"
    write_env(env_path, "PORT=8080\nDEBUG=true\n")
    write_schema(schema_path, {"PORT": {"required": True, "type": "int"}, "DEBUG": {"required": True, "type": "bool"}})
    args = make_args(str(env_path), str(schema_path))
    assert cmd_validate(args) == 0


def test_missing_required_returns_one(env_dir: Path) -> None:
    env_path = env_dir / ".env"
    schema_path = env_dir / "schema.json"
    write_env(env_path, "PORT=8080\n")
    write_schema(schema_path, {"PORT": {"required": True}, "SECRET": {"required": True}})
    args = make_args(str(env_path), str(schema_path))
    assert cmd_validate(args) == 1


def test_missing_env_file_returns_two(env_dir: Path) -> None:
    schema_path = env_dir / "schema.json"
    write_schema(schema_path, {})
    args = make_args(str(env_dir / "nonexistent.env"), str(schema_path))
    assert cmd_validate(args) == 2


def test_missing_schema_file_returns_two(env_dir: Path) -> None:
    env_path = env_dir / ".env"
    write_env(env_path, "PORT=8080\n")
    args = make_args(str(env_path), str(env_dir / "no_schema.json"))
    assert cmd_validate(args) == 2


def test_json_output_valid(env_dir: Path, capsys) -> None:
    env_path = env_dir / ".env"
    schema_path = env_dir / "schema.json"
    write_env(env_path, "PORT=9000\n")
    write_schema(schema_path, {"PORT": {"required": True, "type": "int"}})
    args = make_args(str(env_path), str(schema_path), fmt="json")
    rc = cmd_validate(args)
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["valid"] is True
    assert data["missing_required"] == []


def test_json_output_invalid(env_dir: Path, capsys) -> None:
    env_path = env_dir / ".env"
    schema_path = env_dir / "schema.json"
    write_env(env_path, "PORT=not_a_number\n")
    write_schema(schema_path, {"PORT": {"required": True, "type": "int"}})
    args = make_args(str(env_path), str(schema_path), fmt="json")
    rc = cmd_validate(args)
    assert rc == 1
    data = json.loads(capsys.readouterr().out)
    assert data["valid"] is False
    assert "PORT" in data["type_errors"]


def test_empty_env_with_no_required_keys_returns_zero(env_dir: Path) -> None:
    """An empty .env file should be valid when the schema has no required keys."""
    env_path = env_dir / ".env"
    schema_path = env_dir / "schema.json"
    write_env(env_path, "")
    write_schema(schema_path, {"OPTIONAL_KEY": {"required": False}})
    args = make_args(str(env_path), str(schema_path))
    assert cmd_validate(args) == 0
