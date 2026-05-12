"""CLI command: envdiff template — generate a .env.example file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.templater import generate_template, TemplateError


def cmd_template(args: argparse.Namespace) -> int:
    """Entry point for the `template` sub-command.

    Returns:
        0 on success, 2 on input/parse error.
    """
    source = Path(args.env_file)
    if not source.exists():
        print(f"error: file not found: {source}", file=sys.stderr)
        return 2

    try:
        env = parse_env_file(source)
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    extra = list(args.extra_patterns) if args.extra_patterns else []

    try:
        result = generate_template(
            env,
            mask_sensitive=not args.no_mask,
            placeholder=args.placeholder,
            extra_patterns=extra,
            header_comment=args.header,
        )
    except TemplateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    rendered = result.render()

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(rendered, encoding="utf-8")
        print(f"Template written to {out_path}")
    else:
        print(rendered, end="")

    return 0


def register_template_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "template",
        help="Generate a .env.example template from an env file.",
    )
    p.add_argument("env_file", help="Path to the source .env file.")
    p.add_argument("-o", "--output", metavar="FILE", help="Write output to FILE instead of stdout.")
    p.add_argument(
        "--no-mask",
        action="store_true",
        default=False,
        help="Do not mask sensitive values.",
    )
    p.add_argument(
        "--placeholder",
        default="",
        metavar="TEXT",
        help="Replacement text for sensitive values (default: empty string).",
    )
    p.add_argument(
        "--extra-patterns",
        nargs="+",
        metavar="PATTERN",
        help="Additional regex patterns to treat as sensitive.",
    )
    p.add_argument("--header", metavar="TEXT", help="Comment line prepended to the template.")
    p.set_defaults(func=cmd_template)
