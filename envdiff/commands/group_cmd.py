"""CLI command: envdiff group — display env keys organised by prefix."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envdiff.grouper import group_keys
from envdiff.parser import EnvParseError, parse_env_file


def _print_groups(result, *, show_ungrouped: bool = True) -> None:
    for name in result.group_names():
        members = result.groups[name]
        print(f"[{name}] ({len(members)} keys)")
        for key in members:
            print(f"  {key}")

    if show_ungrouped and result.ungrouped:
        print(f"[ungrouped] ({len(result.ungrouped)} keys)")
        for key in result.ungrouped:
            print(f"  {key}")


def cmd_group(args: argparse.Namespace) -> int:
    """Entry point for the *group* sub-command.

    Returns an exit code: 0 on success, 2 on file/parse error.
    """
    try:
        env = parse_env_file(args.file)
    except (EnvParseError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    keys: List[str] = list(env.keys())
    result = group_keys(
        keys,
        separator=args.separator,
        min_group_size=args.min_group_size,
    )

    if args.summary:
        print(result.summary())
    else:
        _print_groups(result, show_ungrouped=not args.hide_ungrouped)

    return 0


def register_group_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "group",
        help="Group env keys by prefix and display them.",
    )
    p.add_argument("file", help="Path to the .env file to inspect.")
    p.add_argument(
        "--separator",
        default="_",
        help="Prefix separator character (default: '_').",
    )
    p.add_argument(
        "--min-group-size",
        type=int,
        default=2,
        dest="min_group_size",
        help="Minimum keys to form a group (default: 2).",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Print a compact summary instead of the full key list.",
    )
    p.add_argument(
        "--hide-ungrouped",
        action="store_true",
        dest="hide_ungrouped",
        help="Suppress the ungrouped keys section.",
    )
    p.set_defaults(func=cmd_group)
