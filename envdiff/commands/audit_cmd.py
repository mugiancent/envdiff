"""CLI command: envdiff audit  — list or clear the audit log."""

from __future__ import annotations

import argparse
from pathlib import Path

from envdiff.audit import AuditError, clear_entries, load_entries

DEFAULT_AUDIT_DIR = Path(".envdiff") / "audit"


def cmd_audit(args: argparse.Namespace) -> int:
    """Entry point for the ``audit`` sub-command.

    Sub-commands:
      list   – print all audit entries (default)
      clear  – remove all audit entries
    """
    audit_dir = Path(getattr(args, "audit_dir", DEFAULT_AUDIT_DIR))
    sub = getattr(args, "audit_sub", "list")

    if sub == "clear":
        return _do_clear(audit_dir)
    return _do_list(audit_dir)


def _do_list(audit_dir: Path) -> int:
    try:
        entries = load_entries(audit_dir=audit_dir)
    except AuditError as exc:
        print(f"[error] {exc}")
        return 2

    if not entries:
        print("No audit entries found.")
        return 0

    print(f"{'TIMESTAMP':<35} {'ACTION':<12} {'OUTCOME':<14} DETAIL")
    print("-" * 80)
    for e in entries:
        print(f"{e.timestamp:<35} {e.action:<12} {e.outcome:<14} {e.detail}")
    return 0


def _do_clear(audit_dir: Path) -> int:
    try:
        clear_entries(audit_dir=audit_dir)
        print("Audit log cleared.")
        return 0
    except AuditError as exc:
        print(f"[error] {exc}")
        return 2


def register_audit_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach the ``audit`` command to an existing subparsers group."""
    p = subparsers.add_parser("audit", help="View or clear the audit log")
    p.add_argument(
        "audit_sub",
        nargs="?",
        choices=["list", "clear"],
        default="list",
        help="Action to perform (default: list)",
    )
    p.add_argument(
        "--audit-dir",
        default=str(DEFAULT_AUDIT_DIR),
        help="Directory that stores the audit log",
    )
    p.set_defaults(func=cmd_audit)
