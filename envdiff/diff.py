"""Core diffing logic for comparing .env files."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class EnvDiffResult:
    """Result of comparing two .env files."""

    base_file: str
    compare_file: str

    # Keys present in base but missing in compare
    missing_in_compare: List[str] = field(default_factory=list)

    # Keys present in compare but missing in base
    missing_in_base: List[str] = field(default_factory=list)

    # Keys present in both but with different values
    mismatched: Dict[str, Dict[str, Optional[str]]] = field(default_factory=dict)

    @property
    def has_differences(self) -> bool:
        return bool(
            self.missing_in_compare or self.missing_in_base or self.mismatched
        )

    def summary(self) -> str:
        lines = [f"Comparing {self.base_file!r} vs {self.compare_file!r}"]
        if not self.has_differences:
            lines.append("  No differences found.")
            return "\n".join(lines)

        if self.missing_in_compare:
            lines.append(f"  Missing in {self.compare_file} ({len(self.missing_in_compare)}):")
            for key in sorted(self.missing_in_compare):
                lines.append(f"    - {key}")

        if self.missing_in_base:
            lines.append(f"  Missing in {self.base_file} ({len(self.missing_in_base)}):")
            for key in sorted(self.missing_in_base):
                lines.append(f"    + {key}")

        if self.mismatched:
            lines.append(f"  Mismatched values ({len(self.mismatched)}):")
            for key in sorted(self.mismatched):
                base_val = self.mismatched[key]["base"]
                cmp_val = self.mismatched[key]["compare"]
                lines.append(f"    ~ {key}: {base_val!r} -> {cmp_val!r}")

        return "\n".join(lines)


def diff_envs(
    base: Dict[str, Optional[str]],
    compare: Dict[str, Optional[str]],
    base_file: str = "base",
    compare_file: str = "compare",
    check_values: bool = True,
) -> EnvDiffResult:
    """Compare two parsed env dicts and return a diff result."""
    base_keys: Set[str] = set(base.keys())
    compare_keys: Set[str] = set(compare.keys())

    result = EnvDiffResult(base_file=base_file, compare_file=compare_file)
    result.missing_in_compare = list(base_keys - compare_keys)
    result.missing_in_base = list(compare_keys - base_keys)

    if check_values:
        for key in base_keys & compare_keys:
            if base[key] != compare[key]:
                result.mismatched[key] = {"base": base[key], "compare": compare[key]}

    return result
