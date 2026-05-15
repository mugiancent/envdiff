"""Annotate env keys with metadata: source file, sensitive flag, lint status."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.redactor import is_sensitive
from envdiff.linter import lint_env, LintIssue


@dataclass
class KeyAnnotation:
    key: str
    value: str
    source: str
    sensitive: bool
    lint_issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_lint_issues(self) -> bool:
        return len(self.lint_issues) > 0

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "source": self.source,
            "sensitive": self.sensitive,
            "lint_issues": [
                {"code": i.code, "message": i.message, "severity": i.severity}
                for i in self.lint_issues
            ],
        }


@dataclass
class AnnotationResult:
    source: str
    annotations: Dict[str, KeyAnnotation] = field(default_factory=dict)

    def keys(self) -> List[str]:
        return list(self.annotations.keys())

    def sensitive_keys(self) -> List[str]:
        return [k for k, a in self.annotations.items() if a.sensitive]

    def keys_with_issues(self) -> List[str]:
        return [k for k, a in self.annotations.items() if a.has_lint_issues]


def annotate_env(
    env: Dict[str, str],
    source: str,
    extra_sensitive_patterns: Optional[List[str]] = None,
    allow_lowercase: bool = False,
) -> AnnotationResult:
    """Annotate each key in *env* with sensitivity and lint metadata."""
    lint_result = lint_env(env, allow_lowercase=allow_lowercase)
    issues_by_key: Dict[str, List[LintIssue]] = {}
    for issue in lint_result.issues:
        issues_by_key.setdefault(issue.key, []).append(issue)

    result = AnnotationResult(source=source)
    for key, value in env.items():
        sensitive = is_sensitive(key, extra_patterns=extra_sensitive_patterns)
        result.annotations[key] = KeyAnnotation(
            key=key,
            value=value,
            source=source,
            sensitive=sensitive,
            lint_issues=issues_by_key.get(key, []),
        )
    return result
