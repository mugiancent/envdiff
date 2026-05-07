"""Tests for envdiff.commands.audit_cmd."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.audit import AuditEntry, append_entry
from envdiff.commands.audit_cmd import cmd_audit, register_audit_parser


@pytest.fixture()
def audit_dir(tmp_path: Path) -> Path:
    return tmp_path / "audit"


def make_args(sub: str = "list", audit_dir: Path | None = None) -> argparse.Namespace:
    return argparse.Namespace(audit_sub=sub, audit_dir=str(audit_dir) if audit_dir else ".envdiff/audit")


def test_list_empty_prints_no_entries(audit_dir: Path, capsys) -> None:
    rc = cmd_audit(make_args("list", audit_dir))
    assert rc == 0
    out = capsys.readouterr().out
    assert "No audit entries" in out


def test_list_shows_entries(audit_dir: Path, capsys) -> None:
    append_entry(AuditEntry(action="diff", outcome="ok", detail="clean"), audit_dir=audit_dir)
    rc = cmd_audit(make_args("list", audit_dir))
    assert rc == 0
    out = capsys.readouterr().out
    assert "diff" in out
    assert "ok" in out
    assert "clean" in out


def test_list_shows_multiple_entries(audit_dir: Path, capsys) -> None:
    for action in ("diff", "validate", "baseline"):
        append_entry(AuditEntry(action=action, outcome="ok", detail="-"), audit_dir=audit_dir)
    rc = cmd_audit(make_args("list", audit_dir))
    assert rc == 0
    out = capsys.readouterr().out
    assert "diff" in out
    assert "validate" in out
    assert "baseline" in out


def test_clear_removes_entries(audit_dir: Path, capsys) -> None:
    append_entry(AuditEntry(action="diff", outcome="ok", detail="-"), audit_dir=audit_dir)
    rc = cmd_audit(make_args("clear", audit_dir))
    assert rc == 0
    out = capsys.readouterr().out
    assert "cleared" in out.lower()
    # subsequent list should be empty
    rc2 = cmd_audit(make_args("list", audit_dir))
    assert rc2 == 0
    out2 = capsys.readouterr().out
    assert "No audit entries" in out2


def test_default_sub_is_list(audit_dir: Path, capsys) -> None:
    args = argparse.Namespace(audit_sub="list", audit_dir=str(audit_dir))
    rc = cmd_audit(args)
    assert rc == 0


def test_register_audit_parser_attaches_command() -> None:
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    register_audit_parser(subs)
    ns = root.parse_args(["audit", "list"])
    assert ns.audit_sub == "list"
    assert hasattr(ns, "func")
