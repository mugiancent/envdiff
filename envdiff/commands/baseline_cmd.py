"""CLI command: envdiff baseline — compare current env against a saved snapshot."""

from __future__ import annotations

import sys
from argparse import Namespace
from typing import Optional

from envdiff.baseline import BaselineError, compare_against_latest, compare_against_snapshot
from envdiff.diff import has_differences
from envdiff.parser import EnvParseError, parse_env_file
from envdiff.reporter import OutputFormat, render


def cmd_baseline(args: Namespace) -> int:
    """Compare *args.env_file* against a baseline snapshot.

    Exit codes:
      0 — no differences
      1 — differences found
      2 — usage / IO error
    """
    # Parse the current env file
    try:
        current_env = parse_env_file(args.env_file)
    except (EnvParseError, OSError) as exc:
        print(f"Error reading env file: {exc}", file=sys.stderr)
        return 2

    # Determine output format
    try:
        fmt = OutputFormat(args.format) if hasattr(args, "format") and args.format else OutputFormat.TEXT
    except ValueError:
        fmt = OutputFormat.TEXT

    check_values: bool = not getattr(args, "ignore_values", False)

    # Resolve snapshot
    try:
        if getattr(args, "snapshot", None):
            result = compare_against_snapshot(
                current_env, args.snapshot, check_values=check_values
            )
        else:
            history_dir: str = getattr(args, "history_dir", ".envdiff_history")
            maybe = compare_against_latest(
                current_env, history_dir, check_values=check_values
            )
            if maybe is None:
                print("No snapshots found — nothing to compare against.", file=sys.stderr)
                return 2
            result = maybe
    except BaselineError as exc:
        print(f"Baseline error: {exc}", file=sys.stderr)
        return 2

    print(render(result.diff, fmt))

    return 1 if has_differences(result.diff) else 0
