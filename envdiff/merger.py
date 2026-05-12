"""Merge multiple .env files into a single unified output.

Later files take precedence over earlier ones for duplicate keys.
Optionally, only keys present in a reference (base) file are included.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class MergeError(Exception):
    """Raised when merging fails."""


@dataclass
class MergeResult:
    """Result of merging multiple env dicts."""

    merged: Dict[str, str]
    sources: Dict[str, str] = field(default_factory=dict)  # key -> filename that won
    overridden: Dict[str, List[str]] = field(default_factory=dict)  # key -> files that lost

    @property
    def key_count(self) -> int:
        return len(self.merged)

    def summary(self) -> str:
        lines = [f"Merged {self.key_count} key(s)."]
        if self.overridden:
            lines.append(f"{len(self.overridden)} key(s) had overrides.")
        return " ".join(lines)


def merge_envs(
    named_envs: List[tuple[str, Dict[str, str]]],
    restrict_to: Optional[Dict[str, str]] = None,
) -> MergeResult:
    """Merge a list of (name, env_dict) pairs left-to-right.

    Args:
        named_envs: Ordered list of (label, env_dict). Later entries win.
        restrict_to: If provided, only keys present in this dict are kept.

    Returns:
        MergeResult with merged values and provenance metadata.

    Raises:
        MergeError: If named_envs is empty.
    """
    if not named_envs:
        raise MergeError("At least one environment must be provided for merging.")

    merged: Dict[str, str] = {}
    sources: Dict[str, str] = {}
    overridden: Dict[str, List[str]] = {}

    for name, env in named_envs:
        for key, value in env.items():
            if key in sources:
                overridden.setdefault(key, []).append(sources[key])
            merged[key] = value
            sources[key] = name

    if restrict_to is not None:
        allowed = set(restrict_to.keys())
        merged = {k: v for k, v in merged.items() if k in allowed}
        sources = {k: v for k, v in sources.items() if k in allowed}
        overridden = {k: v for k, v in overridden.items() if k in allowed}

    return MergeResult(merged=merged, sources=sources, overridden=overridden)


def render_merged(result: MergeResult, include_source_comments: bool = False) -> str:
    """Render a MergeResult back to .env file format."""
    lines: List[str] = []
    for key, value in sorted(result.merged.items()):
        if include_source_comments:
            lines.append(f"# source: {result.sources.get(key, 'unknown')}")
        lines.append(f"{key}={value}")
    return "\n".join(lines) + ("\n" if lines else "")
