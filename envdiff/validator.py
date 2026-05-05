"""Validate .env files against a schema of required keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class ValidationResult:
    """Result of validating an env mapping against a schema."""

    missing_required: List[str] = field(default_factory=list)
    unknown_keys: List[str] = field(default_factory=list)
    type_errors: Dict[str, str] = field(default_factory=dict)  # key -> error message

    @property
    def is_valid(self) -> bool:
        return (
            not self.missing_required
            and not self.type_errors
        )

    def summary(self) -> str:
        parts: List[str] = []
        if self.missing_required:
            parts.append(f"Missing required keys: {', '.join(sorted(self.missing_required))}")
        if self.type_errors:
            errs = "; ".join(f"{k}: {v}" for k, v in sorted(self.type_errors.items()))
            parts.append(f"Type errors: {errs}")
        if self.unknown_keys:
            parts.append(f"Unknown keys: {', '.join(sorted(self.unknown_keys))}")
        return " | ".join(parts) if parts else "OK"


# Supported type validators
_TYPE_VALIDATORS: Dict[str, object] = {
    "int": lambda v: int(v),
    "float": lambda v: float(v),
    "bool": lambda v: _parse_bool(v),
    "str": lambda v: v,
}


def _parse_bool(value: str) -> bool:
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    raise ValueError(f"Cannot parse '{value}' as bool")


def validate_env(
    env: Dict[str, str],
    required_keys: Optional[Set[str]] = None,
    type_hints: Optional[Dict[str, str]] = None,
    allow_unknown: bool = True,
    known_keys: Optional[Set[str]] = None,
) -> ValidationResult:
    """Validate *env* dict against optional schema constraints.

    Args:
        env: Parsed environment mapping.
        required_keys: Keys that must be present.
        type_hints: Mapping of key -> expected type name ('int', 'float', 'bool', 'str').
        allow_unknown: When False, keys not in *known_keys* are reported.
        known_keys: Full set of recognised keys (used when allow_unknown=False).
    """
    result = ValidationResult()

    if required_keys:
        for key in required_keys:
            if key not in env:
                result.missing_required.append(key)

    if type_hints:
        for key, type_name in type_hints.items():
            if key not in env:
                continue  # missing keys handled above
            validator = _TYPE_VALIDATORS.get(type_name)
            if validator is None:
                continue
            try:
                validator(env[key])  # type: ignore[operator]
            except (ValueError, TypeError) as exc:
                result.type_errors[key] = str(exc)

    if not allow_unknown and known_keys is not None:
        for key in env:
            if key not in known_keys:
                result.unknown_keys.append(key)

    return result
