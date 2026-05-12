"""CLI command: watch two .env files and print diffs as they change."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.watcher import watch, WatcherError
from envdiff.reporter import render, OutputFormat
from envdiff.diff import has_differences


def cmd_watch(args: argparse.Namespace) -> int:
    """Entry point for the ``envdiff watch`` sub-command.

    Returns 0 on clean exit (KeyboardInterrupt) or 2 on error.
    """
    base_path = Path(args.base)
    compare_path = Path(args.compare)

    try:
        fmt = OutputFormat(args.format)
    except ValueError:
        print(f"Unknown format: {args.format}", file=sys.stderr)
        return 2

    def on_change(result):
        print("\n--- Change detected ---")
        print(render(result, fmt))
        if has_differences(result):
            print("[!] Differences found.")
        else:
            print("[✓] Files are in sync.")

    print(f"Watching {base_path} vs {compare_path} (Ctrl-C to stop)…")
    try:
        watch(
            base_path,
            compare_path,
            on_change,
            poll_interval=args.interval,
            check_values=not args.ignore_values,
        )
    except WatcherError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nWatcher stopped.")
        return 0

    return 0


def register_watch_parser(subparsers) -> None:
    """Attach the ``watch`` sub-command to *subparsers*."""
    p = subparsers.add_parser(
        "watch",
        help="Watch two .env files and print diffs whenever they change.",
    )
    p.add_argument("base", help="Base .env file path.")
    p.add_argument("compare", help="Compare .env file path.")
    p.add_argument(
        "--format",
        default="text",
        choices=[f.value for f in OutputFormat],
        help="Output format (default: text).",
    )
    p.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Poll interval in seconds (default: 1.0).",
    )
    p.add_argument(
        "--ignore-values",
        action="store_true",
        help="Report only missing keys, not value mismatches.",
    )
    p.set_defaults(func=cmd_watch)
