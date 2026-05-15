"""CLI command: annotate — display per-key metadata for an env file."""
from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace
from typing import List, Optional

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.annotator import annotate_env


def _print_text(result, redact_sensitive: bool) -> None:
    for key, ann in result.annotations.items():
        flags: List[str] = []
        if ann.sensitive:
            flags.append("sensitive")
        if ann.has_lint_issues:
            issue_codes = ", ".join(i.code for i in ann.lint_issues)
            flags.append(f"lint:{issue_codes}")
        flag_str = f"  [{', '.join(flags)}]" if flags else ""
        value = "***" if (ann.sensitive and redact_sensitive) else ann.value
        print(f"  {key}={value}{flag_str}")


def cmd_annotate(args: Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except (EnvParseError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    extra_patterns: Optional[List[str]] = (
        args.sensitive_patterns.split(",") if args.sensitive_patterns else None
    )

    result = annotate_env(
        env,
        source=args.file,
        extra_sensitive_patterns=extra_patterns,
        allow_lowercase=args.allow_lowercase,
    )

    if args.format == "json":
        output = {
            "source": result.source,
            "keys": [a.to_dict() for a in result.annotations.values()],
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Annotations for {result.source}:")
        _print_text(result, redact_sensitive=not args.show_values)
        sensitive_count = len(result.sensitive_keys())
        issues_count = len(result.keys_with_issues())
        print(f"\nSummary: {len(result.keys())} keys, "
              f"{sensitive_count} sensitive, "
              f"{issues_count} with lint issues")

    return 0


def register_annotate_parser(subparsers) -> None:
    p: ArgumentParser = subparsers.add_parser(
        "annotate", help="Show per-key metadata (sensitivity, lint) for an env file"
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format"
    )
    p.add_argument(
        "--show-values",
        action="store_true",
        default=False,
        help="Show sensitive values in plain text (default: redact)",
    )
    p.add_argument(
        "--allow-lowercase",
        action="store_true",
        default=False,
        help="Suppress E001 lint errors for lowercase keys",
    )
    p.add_argument(
        "--sensitive-patterns",
        default="",
        help="Comma-separated extra patterns to treat as sensitive",
    )
    p.set_defaults(func=cmd_annotate)
