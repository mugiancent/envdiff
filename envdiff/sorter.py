"""Sort and group .env keys by prefix, alphabetical order, or custom rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SortResult:
    """Holds sorted keys grouped by prefix."""

    groups: Dict[str, List[str]] = field(default_factory=dict)
    ungrouped: List[str] = field(default_factory=list)

    @property
    def all_keys(self) -> List[str]:
        """Return all keys in group order, then ungrouped."""
        keys: List[str] = []
        for group_keys in self.groups.values():
            keys.extend(group_keys)
        keys.extend(self.ungrouped)
        return keys


def _extract_prefix(key: str, separator: str = "_") -> Optional[str]:
    """Return the first segment of a key before *separator*, or None."""
    if separator in key:
        return key.split(separator, 1)[0]
    return None


def sort_keys(
    env: Dict[str, str],
    *,
    alphabetical: bool = True,
    group_by_prefix: bool = False,
    separator: str = "_",
    prefix_order: Optional[List[str]] = None,
) -> SortResult:
    """Sort *env* keys according to the requested strategy.

    Parameters
    ----------
    env:
        Mapping of key -> value from a parsed .env file.
    alphabetical:
        Sort keys (and group names) alphabetically when True.
    group_by_prefix:
        When True, group keys by their first ``separator``-delimited segment.
    separator:
        Delimiter used to detect prefixes (default ``"_"``).
    prefix_order:
        Explicit ordering for group names; unrecognised prefixes are appended.
    """
    keys = list(env.keys())
    if alphabetical:
        keys = sorted(keys)

    if not group_by_prefix:
        return SortResult(ungrouped=keys)

    groups: Dict[str, List[str]] = {}
    ungrouped: List[str] = []

    for key in keys:
        prefix = _extract_prefix(key, separator)
        if prefix is None:
            ungrouped.append(key)
        else:
            groups.setdefault(prefix, []).append(key)

    # Apply explicit prefix ordering if provided
    if prefix_order:
        ordered: Dict[str, List[str]] = {}
        for p in prefix_order:
            if p in groups:
                ordered[p] = groups.pop(p)
        # Append remaining groups (already alphabetical if alphabetical=True)
        remaining = sorted(groups.keys()) if alphabetical else list(groups.keys())
        for p in remaining:
            ordered[p] = groups[p]
        groups = ordered
    elif alphabetical:
        groups = dict(sorted(groups.items()))

    return SortResult(groups=groups, ungrouped=ungrouped)
