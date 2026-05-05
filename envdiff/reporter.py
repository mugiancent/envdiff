"""Reporting utilities for envdiff — format and output diff results."""

from __future__ import annotations

from enum import Enum
from typing import TextIO
import sys

from envdiff.diff import EnvDiffResult


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


def _format_text(result: EnvDiffResult, base_name: str, compare_name: str) -> str:
    lines: list[str] = []
    lines.append(f"Comparing '{base_name}' (base) vs '{compare_name}' (compare)")
    lines.append("-" * 60)

    if result.missing_in_compare:
        lines.append(f"Missing in {compare_name} ({len(result.missing_in_compare)}):")
        for key in sorted(result.missing_in_compare):
            lines.append(f"  - {key}")

    if result.missing_in_base:
        lines.append(f"Missing in {base_name} ({len(result.missing_in_base)}):")
        for key in sorted(result.missing_in_base):
            lines.append(f"  + {key}")

    if result.mismatched_values:
        lines.append(f"Mismatched values ({len(result.mismatched_values)}):")
        for key, (base_val, cmp_val) in sorted(result.mismatched_values.items()):
            lines.append(f"  ~ {key}")
            lines.append(f"      {base_name}: {base_val!r}")
            lines.append(f"      {compare_name}: {cmp_val!r}")

    if not (result.missing_in_compare or result.missing_in_base or result.mismatched_values):
        lines.append("No differences found.")

    return "\n".join(lines)


def _format_json(result: EnvDiffResult, base_name: str, compare_name: str) -> str:
    import json

    data = {
        "base": base_name,
        "compare": compare_name,
        "missing_in_compare": sorted(result.missing_in_compare),
        "missing_in_base": sorted(result.missing_in_base),
        "mismatched_values": {
            k: {"base": v[0], "compare": v[1]}
            for k, v in sorted(result.mismatched_values.items())
        },
    }
    return json.dumps(data, indent=2)


def _format_markdown(result: EnvDiffResult, base_name: str, compare_name: str) -> str:
    lines: list[str] = []
    lines.append(f"## Env Diff: `{base_name}` vs `{compare_name}`\n")

    if result.missing_in_compare:
        lines.append(f"### Missing in `{compare_name}`\n")
        for key in sorted(result.missing_in_compare):
            lines.append(f"- `{key}`")
        lines.append("")

    if result.missing_in_base:
        lines.append(f"### Missing in `{base_name}`\n")
        for key in sorted(result.missing_in_base):
            lines.append(f"- `{key}`")
        lines.append("")

    if result.mismatched_values:
        lines.append("### Mismatched Values\n")
        lines.append(f"| Key | `{base_name}` | `{compare_name}` |")
        lines.append("|-----|--------|---------|")
        for key, (base_val, cmp_val) in sorted(result.mismatched_values.items()):
            lines.append(f"| `{key}` | `{base_val}` | `{cmp_val}` |")
        lines.append("")

    if not (result.missing_in_compare or result.missing_in_base or result.mismatched_values):
        lines.append("_No differences found._")

    return "\n".join(lines)


def render(
    result: EnvDiffResult,
    base_name: str,
    compare_name: str,
    fmt: OutputFormat = OutputFormat.TEXT,
    stream: TextIO | None = None,
) -> str:
    """Render a diff result to a string and optionally write it to *stream*."""
    if stream is None:
        stream = sys.stdout

    formatters = {
        OutputFormat.TEXT: _format_text,
        OutputFormat.JSON: _format_json,
        OutputFormat.MARKDOWN: _format_markdown,
    }
    output = formatters[fmt](result, base_name, compare_name)
    print(output, file=stream)
    return output
