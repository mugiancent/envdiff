"""Parser for .env files."""

from pathlib import Path
from typing import Dict, Optional


class EnvParseError(Exception):
    """Raised when a .env file cannot be parsed."""
    pass


def parse_env_file(filepath: str | Path) -> Dict[str, Optional[str]]:
    """Parse a .env file and return a dict of key-value pairs.

    Handles:
    - KEY=VALUE
    - KEY="VALUE" or KEY='VALUE'
    - Comments (#)
    - Empty lines
    - Keys with no value (KEY=)

    Args:
        filepath: Path to the .env file.

    Returns:
        A dictionary mapping env var names to their values.

    Raises:
        EnvParseError: If the file cannot be read or a line is malformed.
    """
    path = Path(filepath)
    if not path.exists():
        raise EnvParseError(f"File not found: {filepath}")

    env_vars: Dict[str, Optional[str]] = {}

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise EnvParseError(f"Could not read file: {filepath}") from exc

    for lineno, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        # Skip blank lines and comments
        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            raise EnvParseError(
                f"Malformed line {lineno} in {filepath!r}: {raw_line!r}"
            )

        key, _, value = line.partition("=")
        key = key.strip()

        if not key:
            raise EnvParseError(
                f"Empty key on line {lineno} in {filepath!r}: {raw_line!r}"
            )

        value = value.strip()

        # Strip surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]

        env_vars[key] = value if value else None

    return env_vars
