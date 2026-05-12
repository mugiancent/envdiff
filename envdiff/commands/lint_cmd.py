"""CLI command: envdiff lint — lint a .env file for style and safety issues."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envdiff.linter import lint_env, LintIssue
from envdiff.parser import parse_env_file, EnvParseError


def _print_issues(issues: List[LintIssue], *, use_color: bool = True) -> None:
    for issue in issues:
        sev = issue.severity.upper()
        if use_color:
            color = '\033[31m' if issue.severity == 'error' else '\033[33m'
            reset = '\033[0m'
        else:
            color = reset = ''
        print(f"{color}[{sev}] {issue.code}{reset}  {issue.message}")


def cmd_lint(args: argparse.Namespace) -> int:
    """Entry point for the lint sub-command. Returns an exit code."""
    try:
        env = parse_env_file(args.env_file)
    except EnvParseError as exc:
        print(f"Error parsing {args.env_file}: {exc}", file=sys.stderr)
        return 2

    result = lint_env(env, allow_lowercase=args.allow_lowercase)

    no_color = getattr(args, 'no_color', False)
    if result.has_issues:
        _print_issues(result.issues, use_color=not no_color)
        print()
        print(result.summary())
        # Exit 1 if there are errors; 0 if only warnings and --warn-only
        if result.errors and not getattr(args, 'warn_only', False):
            return 1
    else:
        print(result.summary())

    return 0


def register_lint_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        'lint',
        help='Lint a .env file for style and safety issues.',
    )
    p.add_argument('env_file', metavar='ENV_FILE', help='Path to the .env file to lint.')
    p.add_argument(
        '--allow-lowercase',
        action='store_true',
        default=False,
        help='Allow lowercase key names (default: require UPPER_SNAKE_CASE).',
    )
    p.add_argument(
        '--warn-only',
        action='store_true',
        default=False,
        help='Exit 0 even when errors are found (treat all issues as warnings).',
    )
    p.add_argument(
        '--no-color',
        action='store_true',
        default=False,
        help='Disable ANSI colour in output.',
    )
    p.set_defaults(func=cmd_lint)
