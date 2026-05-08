"""Redact sensitive values from env dicts before display or storage."""

from __future__ import annotations

import re
from typing import Dict, List, Optional

# Default patterns that indicate a key holds a sensitive value
_DEFAULT_SENSITIVE_PATTERNS: List[str] = [
    r".*SECRET.*",
    r".*PASSWORD.*",
    r".*PASSWD.*",
    r".*TOKEN.*",
    r".*API_KEY.*",
    r".*PRIVATE_KEY.*",
    r".*CREDENTIALS.*",
    r".*AUTH.*",
]

REDACTED_PLACEHOLDER = "***REDACTED***"


def _compile_patterns(patterns: List[str]) -> List[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


def is_sensitive(
    key: str,
    patterns: Optional[List[str]] = None,
) -> bool:
    """Return True if *key* matches any sensitive pattern."""
    compiled = _compile_patterns(patterns if patterns is not None else _DEFAULT_SENSITIVE_PATTERNS)
    return any(pat.fullmatch(key) for pat in compiled)


def redact(
    env: Dict[str, str],
    patterns: Optional[List[str]] = None,
    placeholder: str = REDACTED_PLACEHOLDER,
) -> Dict[str, str]:
    """Return a copy of *env* with sensitive values replaced by *placeholder*."""
    return {
        key: (placeholder if is_sensitive(key, patterns) else value)
        for key, value in env.items()
    }
