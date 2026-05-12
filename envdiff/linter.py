"""Lint .env files for common style and safety issues."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.redactor import is_sensitive

_UPPER_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')
_WHITESPACE_VAL_RE = re.compile(r'^\s+|\s+$')


@dataclass
class LintIssue:
    key: str
    code: str
    message: str
    severity: str  # 'warning' | 'error'


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == 'error']

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == 'warning']

    def summary(self) -> str:
        if not self.has_issues:
            return 'No lint issues found.'
        parts = []
        if self.errors:
            parts.append(f"{len(self.errors)} error(s)")
        if self.warnings:
            parts.append(f"{len(self.warnings)} warning(s)")
        return 'Lint issues: ' + ', '.join(parts) + '.'


def lint_env(env: Dict[str, str], *, allow_lowercase: bool = False) -> LintResult:
    """Run lint checks on a parsed env dictionary."""
    result = LintResult()

    for key, value in env.items():
        # Check naming convention
        if not allow_lowercase and not _UPPER_RE.match(key):
            result.issues.append(LintIssue(
                key=key,
                code='E001',
                message=f"Key '{key}' should be UPPER_SNAKE_CASE.",
                severity='error',
            ))

        # Check for leading/trailing whitespace in values
        if _WHITESPACE_VAL_RE.search(value):
            result.issues.append(LintIssue(
                key=key,
                code='W001',
                message=f"Value for '{key}' has leading or trailing whitespace.",
                severity='warning',
            ))

        # Warn if sensitive key has an empty value
        if is_sensitive(key) and value == '':
            result.issues.append(LintIssue(
                key=key,
                code='W002',
                message=f"Sensitive key '{key}' has an empty value.",
                severity='warning',
            ))

        # Warn about keys that look like placeholders
        if re.search(r'(CHANGEME|TODO|FIXME|PLACEHOLDER)', value, re.IGNORECASE):
            result.issues.append(LintIssue(
                key=key,
                code='W003',
                message=f"Value for '{key}' appears to be a placeholder.",
                severity='warning',
            ))

    return result
