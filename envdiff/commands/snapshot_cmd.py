"""CLI sub-commands for snapshot management (save / list / show / delete)."""

from __future__ import annotations

import argparse
import sys

from envdiff.diff import diff_envs
from envdiff.history import HistoryError, SnapshotHistory
from envdiff.parser import EnvParseError, parse_env_file
from envdiff.reporter import OutputFormat, render


def _get_history(args: argparse.Namespace) -> SnapshotHistory:
    return SnapshotHistory(args.history_dir)


def cmd_snapshot_save(args: argparse.Namespace) -> int:
    """Parse two env files, diff them, and save the result as a named snapshot."""
    try:
        base_env = parse_env_file(args.base)
        compare_env = parse_env_file(args.compare)
    except EnvParseError as exc:
        print(f"Error parsing env file: {exc}", file=sys.stderr)
        return 1

    result = diff_envs(
        base_env, compare_env,
        base_name=args.base,
        compare_name=args.compare,
        check_values=not args.keys_only,
    )
    try:
        path = _get_history(args).save(result, args.name)
        print(f"Snapshot saved: {path}")
    except HistoryError as exc:
        print(f"Snapshot error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_snapshot_list(args: argparse.Namespace) -> int:
    """List all saved snapshots."""
    names = _get_history(args).list_snapshots()
    if not names:
        print("No snapshots found.")
    else:
        for name in names:
            print(name)
    return 0


def cmd_snapshot_show(args: argparse.Namespace) -> int:
    """Render a saved snapshot."""
    try:
        result = _get_history(args).load(args.name)
    except HistoryError as exc:
        print(f"Snapshot error: {exc}", file=sys.stderr)
        return 1

    fmt = OutputFormat[args.format.upper()]
    print(render(result, fmt))
    return 0


def cmd_snapshot_delete(args: argparse.Namespace) -> int:
    """Delete a saved snapshot."""
    try:
        _get_history(args).delete(args.name)
        print(f"Deleted snapshot: {args.name}")
    except HistoryError as exc:
        print(f"Snapshot error: {exc}", file=sys.stderr)
        return 1
    return 0


def register_snapshot_subcommands(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
    history_dir: str = ".envdiff_history",
) -> None:
    """Attach snapshot sub-commands to an existing subparsers group."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--history-dir", default=history_dir, metavar="DIR",
        help="Directory for snapshot storage (default: %(default)s)",
    )

    # save
    p_save = subparsers.add_parser("snapshot-save", parents=[common], help="Save a diff snapshot")
    p_save.add_argument("base")
    p_save.add_argument("compare")
    p_save.add_argument("name", help="Snapshot name")
    p_save.add_argument("--keys-only", action="store_true")
    p_save.set_defaults(func=cmd_snapshot_save)

    # list
    p_list = subparsers.add_parser("snapshot-list", parents=[common], help="List snapshots")
    p_list.set_defaults(func=cmd_snapshot_list)

    # show
    p_show = subparsers.add_parser("snapshot-show", parents=[common], help="Show a snapshot")
    p_show.add_argument("name")
    p_show.add_argument("--format", default="text", choices=["text", "json", "markdown"])
    p_show.set_defaults(func=cmd_snapshot_show)

    # delete
    p_del = subparsers.add_parser("snapshot-delete", parents=[common], help="Delete a snapshot")
    p_del.add_argument("name")
    p_del.set_defaults(func=cmd_snapshot_delete)
