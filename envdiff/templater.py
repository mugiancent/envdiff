"""Generate .env.example templates from parsed env files or schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.redactor import is_sensitive


class TemplateError(Exception):
    """Raised when template generation fails."""


@dataclass
class TemplateResult:
    keys: List[str] = field(default_factory=list)
    lines: List[str] = field(default_factory=list)

    def render(self) -> str:
        return "\n".join(self.lines) + ("\n" if self.lines else "")


def generate_template(
    env: Dict[str, str],
    *,
    mask_sensitive: bool = True,
    placeholder: str = "",
    extra_patterns: Optional[List[str]] = None,
    header_comment: Optional[str] = None,
) -> TemplateResult:
    """Build a .env.example from a parsed env dict.

    Args:
        env: Mapping of key -> value from a parsed .env file.
        mask_sensitive: Replace sensitive values with *placeholder*.
        placeholder: String used in place of sensitive values.
        extra_patterns: Additional regex patterns forwarded to is_sensitive.
        header_comment: Optional comment block prepended to the output.

    Returns:
        A TemplateResult whose .render() produces the file content.
    """
    if extra_patterns is None:
        extra_patterns = []

    lines: List[str] = []

    if header_comment:
        for comment_line in header_comment.splitlines():
            lines.append(f"# {comment_line}" if not comment_line.startswith("#") else comment_line)
        lines.append("")

    keys = sorted(env.keys())
    for key in keys:
        value = env[key]
        if mask_sensitive and is_sensitive(key, extra_patterns=extra_patterns):
            value = placeholder
        lines.append(f"{key}={value}")

    return TemplateResult(keys=keys, lines=lines)
