"""Load and parse a simple YAML/JSON schema file for env validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Set

try:
    import yaml  # type: ignore
    _YAML_AVAILABLE = True
except ImportError:  # pragma: no cover
    _YAML_AVAILABLE = False


class SchemaLoadError(Exception):
    """Raised when a schema file cannot be loaded or is malformed."""


def _load_raw(path: Path) -> Dict[str, Any]:
    """Load raw data from a JSON or YAML file."""
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise SchemaLoadError(f"Invalid JSON in {path}: {exc}") from exc
    if suffix in (".yml", ".yaml"):
        if not _YAML_AVAILABLE:
            raise SchemaLoadError(
                "PyYAML is required to load YAML schemas. Install it with: pip install pyyaml"
            )
        try:
            return yaml.safe_load(text) or {}
        except yaml.YAMLError as exc:
            raise SchemaLoadError(f"Invalid YAML in {path}: {exc}") from exc
    raise SchemaLoadError(f"Unsupported schema file format: {suffix!r} (use .json, .yml, or .yaml)")


def load_schema(path: str | Path) -> Dict[str, Any]:
    """Load a schema file and return a normalised dict.

    Expected schema structure (JSON shown, YAML equivalent works too)::

        {
          "required": ["SECRET_KEY", "DATABASE_URL"],
          "types": {
            "PORT": "int",
            "DEBUG": "bool"
          }
        }

    Returns a dict with keys:
        - ``required_keys``: set of required key names
        - ``type_hints``: dict mapping key -> type name
    """
    raw = _load_raw(Path(path))

    if not isinstance(raw, dict):
        raise SchemaLoadError("Schema root must be a mapping/object.")

    required_keys: Set[str] = set()
    if "required" in raw:
        if not isinstance(raw["required"], list):
            raise SchemaLoadError("'required' must be a list of key names.")
        required_keys = set(raw["required"])

    type_hints: Dict[str, str] = {}
    if "types" in raw:
        if not isinstance(raw["types"], dict):
            raise SchemaLoadError("'types' must be a mapping of key -> type name.")
        type_hints = {str(k): str(v) for k, v in raw["types"].items()}

    return {
        "required_keys": required_keys,
        "type_hints": type_hints,
    }
