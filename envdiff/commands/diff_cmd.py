"""CLI command handlers for diff operations."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from envdiff.diff import diff_envs
from envdiff.parser import parse_env_file, EnvParseError
from envdiff.reporter import render, OutputFormat
from envdiff.snapshot import save_snapshot, SnapshotError


def cmd_diff(
    base_path: str,
    compare_path: str,
    check_values: bool = True,
    output_format: str = "text",
    save: Optional[str] = None,
    ignore_keys: Optional[list[str]] = None,
) -> int:
    """Run a diff between two .env files and render the result.

    Returns an exit code: 0 if no differences, 1 if differences found, 2 on error.
    """
    try:
        base_env = parse_env_file(Path(base_path))
    except (EnvParseError, FileNotFoundError) as exc:
        print(f"Error reading base file '{base_path}': {exc}", file=sys.stderr)
        return 2

    try:
        compare_env = parse_env_file(Path(compare_path))
    except (EnvParseError, FileNotFoundError) as exc:
        print(f"Error reading compare file '{compare_path}': {exc}", file=sys.stderr)
        return 2

    if ignore_keys:
        for key in ignore_keys:
            base_env.pop(key, None)
            compare_env.pop(key, None)

    try:
        fmt = OutputFormat(output_format)
    except ValueError:
        print(
            f"Unknown output format '{output_format}'. "
            f"Choose from: {', '.join(f.value for f in OutputFormat)}",
            file=sys.stderr,
        )
        return 2

    result = diff_envs(
        base_env,
        compare_env,
        base_name=base_path,
        compare_name=compare_path,
        check_values=check_values,
    )

    print(render(result, fmt))

    if save:
        try:
            out_path = save_snapshot(result, Path(save))
            print(f"Snapshot saved to {out_path}", file=sys.stderr)
        except SnapshotError as exc:
            print(f"Warning: could not save snapshot: {exc}", file=sys.stderr)

    return 1 if result.has_differences() else 0
