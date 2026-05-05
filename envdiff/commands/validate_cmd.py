"""CLI command for validating a .env file against a schema."""

from __future__ import annotations

import sys
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.schema import load_schema, SchemaLoadError
from envdiff.validator import validate_env
from envdiff.reporter import OutputFormat


def cmd_validate(args) -> int:
    """Validate a .env file against a schema file.

    Returns:
        0 – valid
        1 – validation errors found
        2 – file / parse error
    """
    env_path = Path(args.env_file)
    schema_path = Path(args.schema_file)

    try:
        env = parse_env_file(env_path)
    except EnvParseError as exc:
        print(f"Error parsing env file: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError:
        print(f"Env file not found: {env_path}", file=sys.stderr)
        return 2

    try:
        schema = load_schema(schema_path)
    except SchemaLoadError as exc:
        print(f"Error loading schema: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError:
        print(f"Schema file not found: {schema_path}", file=sys.stderr)
        return 2

    result = validate_env(env, schema)

    fmt = OutputFormat(getattr(args, "format", "text"))

    if fmt == OutputFormat.JSON:
        import json
        payload = {
            "valid": result.is_valid(),
            "missing_required": result.missing_required,
            "type_errors": result.type_errors,
            "unknown_keys": result.unknown_keys,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(result.summary())

    return 0 if result.is_valid() else 1
