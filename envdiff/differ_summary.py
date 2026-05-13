"""Produce a human-readable summary report comparing multiple env files at once."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.diff import diff_envs, EnvDiffResult
from envdiff.parser import parse_env_file


@dataclass
class MultiDiffEntry:
    """Diff result between the base env and one compare env."""

    compare_name: str
    result: EnvDiffResult


@dataclass
class MultiDiffReport:
    """Aggregated diff report across several compare files."""

    base_name: str
    entries: List[MultiDiffEntry] = field(default_factory=list)

    @property
    def total_issues(self) -> int:
        return sum(
            len(e.result.missing_in_compare)
            + len(e.result.missing_in_base)
            + len(e.result.mismatched)
            for e in self.entries
        )

    @property
    def clean(self) -> bool:
        return self.total_issues == 0

    def per_file_summary(self) -> Dict[str, str]:
        """Return a dict mapping compare_name -> one-line summary string."""
        out: Dict[str, str] = {}
        for entry in self.entries:
            r = entry.result
            parts = []
            if r.missing_in_compare:
                parts.append(f"{len(r.missing_in_compare)} missing in compare")
            if r.missing_in_base:
                parts.append(f"{len(r.missing_in_base)} missing in base")
            if r.mismatched:
                parts.append(f"{len(r.mismatched)} mismatched")
            out[entry.compare_name] = ", ".join(parts) if parts else "OK"
        return out


def multi_diff(
    base_path: str,
    compare_paths: List[str],
    check_values: bool = True,
) -> MultiDiffReport:
    """Diff *base_path* against each path in *compare_paths*.

    Parameters
    ----------
    base_path:
        Path to the reference .env file.
    compare_paths:
        One or more .env files to compare against the base.
    check_values:
        When *False* only key presence is checked (values are ignored).

    Returns
    -------
    MultiDiffReport
        Aggregated results for all comparisons.
    """
    import os

    base_env = parse_env_file(base_path)
    base_name = os.path.basename(base_path)
    report = MultiDiffReport(base_name=base_name)

    for cp in compare_paths:
        compare_env = parse_env_file(cp)
        result = diff_envs(base_env, compare_env, check_values=check_values)
        report.entries.append(
            MultiDiffEntry(compare_name=os.path.basename(cp), result=result)
        )

    return report
