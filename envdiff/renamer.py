"""Rename keys across one or more env file representations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping


class RenameError(Exception):
    """Raised when a rename operation cannot be completed."""


@dataclass
class RenameResult:
    """Outcome of a bulk key-rename operation."""

    renamed: Dict[str, str] = field(default_factory=dict)   # old_key -> new_key
    skipped: List[str] = field(default_factory=list)         # keys not found in env
    output: Dict[str, str] = field(default_factory=dict)     # final env mapping

    @property
    def rename_count(self) -> int:
        return len(self.renamed)

    @property
    def summary(self) -> str:
        parts = [f"{self.rename_count} key(s) renamed"]
        if self.skipped:
            parts.append(f"{len(self.skipped)} key(s) not found (skipped)")
        return ", ".join(parts)


def rename_keys(
    env: Mapping[str, str],
    renames: Mapping[str, str],
    *,
    strict: bool = False,
) -> RenameResult:
    """Return a new env mapping with keys renamed according to *renames*.

    Parameters
    ----------
    env:
        The source key/value pairs (e.g. from ``parse_env_file``).
    renames:
        Mapping of ``{old_key: new_key}``.
    strict:
        When *True*, raise :class:`RenameError` if any *old_key* is absent
        from *env* instead of silently skipping it.
    """
    if not renames:
        return RenameResult(output=dict(env))

    # Detect conflicting targets before mutating anything.
    new_keys = list(renames.values())
    if len(new_keys) != len(set(new_keys)):
        seen: set = set()
        dupes = [k for k in new_keys if k in seen or seen.add(k)]  # type: ignore[func-returns-value]
        raise RenameError(f"Duplicate target key(s) in rename map: {dupes}")

    result = RenameResult()
    output: Dict[str, str] = {}

    for key, value in env.items():
        if key in renames:
            new_key = renames[key]
            output[new_key] = value
            result.renamed[key] = new_key
        else:
            output[key] = value

    for old_key in renames:
        if old_key not in env:
            if strict:
                raise RenameError(f"Key '{old_key}' not found in env (strict mode).")
            result.skipped.append(old_key)

    result.output = output
    return result
