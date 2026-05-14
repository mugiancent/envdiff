"""Group env keys by prefix for organised reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class GroupResult:
    """Holds keys organised into prefix-based groups."""

    groups: Dict[str, List[str]] = field(default_factory=dict)
    ungrouped: List[str] = field(default_factory=list)

    def group_names(self) -> List[str]:
        """Return sorted list of group names."""
        return sorted(self.groups.keys())

    def all_keys(self) -> List[str]:
        """Return every key, grouped first then ungrouped."""
        result: List[str] = []
        for name in self.group_names():
            result.extend(self.groups[name])
        result.extend(self.ungrouped)
        return result

    def summary(self) -> str:
        lines = [f"Groups: {len(self.groups)}, Ungrouped keys: {len(self.ungrouped)}"]
        for name in self.group_names():
            lines.append(f"  [{name}] {len(self.groups[name])} key(s)")
        return "\n".join(lines)


def _extract_prefix(key: str, separator: str = "_") -> Optional[str]:
    """Return the part of *key* before the first *separator*, or None."""
    if separator not in key:
        return None
    prefix, _, _ = key.partition(separator)
    return prefix if prefix else None


def group_keys(
    keys: List[str],
    separator: str = "_",
    min_group_size: int = 2,
) -> GroupResult:
    """Group *keys* by their common prefix.

    A prefix is only promoted to a group when at least *min_group_size*
    keys share it.  Remaining keys land in :attr:`GroupResult.ungrouped`.
    """
    from collections import defaultdict

    buckets: Dict[str, List[str]] = defaultdict(list)
    no_prefix: List[str] = []

    for key in keys:
        prefix = _extract_prefix(key, separator)
        if prefix is None:
            no_prefix.append(key)
        else:
            buckets[prefix].append(key)

    groups: Dict[str, List[str]] = {}
    ungrouped: List[str] = list(no_prefix)

    for prefix, members in buckets.items():
        if len(members) >= min_group_size:
            groups[prefix] = sorted(members)
        else:
            ungrouped.extend(members)

    return GroupResult(groups=groups, ungrouped=sorted(ungrouped))
