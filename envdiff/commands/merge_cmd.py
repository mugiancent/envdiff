"""CLI command: merge multiple .env files into one."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import List

from envdiff.merger import MergeError, merge_envs, render_merged
from envdiff.parser import EnvParseError, parse_env_file


def cmd_merge(args: Namespace) -> int:
    """Merge two or more .env files and write the result.

    Returns:
        0 on success, 2 on parse/merge error.
    """
    named_envs = []
    for path_str in args.files:
        path = Path(path_str)
        try:
            env = parse_env_file(path)
        except (EnvParseError, OSError) as exc:
            print(f"Error reading {path_str}: {exc}", file=sys.stderr)
            return 2
        named_envs.append((path.name, env))

    restrict_to = None
    if args.restrict_to:
        ref_path = Path(args.restrict_to)
        try:
            restrict_to = parse_env_file(ref_path)
        except (EnvParseError, OSError) as exc:
            print(f"Error reading restrict-to file: {exc}", file=sys.stderr)
            return 2

    try:
        result = merge_envs(named_envs, restrict_to=restrict_to)
    except MergeError as exc:
        print(f"Merge error: {exc}", file=sys.stderr)
        return 2

    output = render_merged(result, include_source_comments=args.comments)

    if args.output:
        out_path = Path(args.output)
        try:
            out_path.write_text(output, encoding="utf-8")
        except OSError as exc:
            print(f"Error writing output: {exc}", file=sys.stderr)
            return 2
        if not args.quiet:
            print(f"Merged {result.key_count} key(s) -> {out_path}")
    else:
        sys.stdout.write(output)

    if not args.quiet and args.output:
        print(result.summary())

    return 0


def register_merge_parser(subparsers) -> None:  # type: ignore[type-arg]
    """Attach the merge sub-command to an existing subparsers group."""
    parser: ArgumentParser = subparsers.add_parser(
        "merge",
        help="Merge multiple .env files (later files take precedence).",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".env files to merge, in priority order (last wins).",
    )
    parser.add_argument(
        "--restrict-to",
        metavar="REF_FILE",
        default=None,
        help="Only include keys present in this reference .env file.",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        default=None,
        help="Write merged output to FILE instead of stdout.",
    )
    parser.add_argument(
        "--comments",
        action="store_true",
        default=False,
        help="Add source-file comments above each key.",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        default=False,
        help="Suppress summary output.",
    )
    parser.set_defaults(func=cmd_merge)
