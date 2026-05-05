"""Command-line interface for envdiff."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.diff import diff_envs, has_differences
from envdiff.parser import EnvParseError, parse_env_file
from envdiff.reporter import OutputFormat, render


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff",
        description="Compare .env files across environments and surface missing or mismatched keys.",
    )
    p.add_argument("base", type=Path, help="Base .env file (reference).")
    p.add_argument("compare", type=Path, help=".env file to compare against the base.")
    p.add_argument(
        "--no-check-values",
        action="store_true",
        default=False,
        help="Only check for missing keys; ignore value differences.",
    )
    p.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        dest="fmt",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 if differences are found.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        base_env = parse_env_file(args.base)
    except (EnvParseError, OSError) as exc:
        print(f"envdiff: error reading base file '{args.base}': {exc}", file=sys.stderr)
        return 2

    try:
        compare_env = parse_env_file(args.compare)
    except (EnvParseError, OSError) as exc:
        print(f"envdiff: error reading compare file '{args.compare}': {exc}", file=sys.stderr)
        return 2

    result = diff_envs(
        base_env,
        compare_env,
        check_values=not args.no_check_values,
    )

    render(
        result,
        base_name=str(args.base),
        compare_name=str(args.compare),
        fmt=OutputFormat(args.fmt),
    )

    if args.exit_code and has_differences(result):
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
