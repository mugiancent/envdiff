"""Audit log: record every diff/validate/baseline action with timestamp and outcome."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

AUDIT_VERSION = "1"
DEFAULT_AUDIT_DIR = Path(".envdiff") / "audit"


class AuditError(Exception):
    """Raised when the audit log cannot be read or written."""


@dataclass
class AuditEntry:
    action: str          # e.g. "diff", "validate", "baseline"
    outcome: str         # "ok" | "differences" | "invalid" | "error"
    detail: str          # human-readable one-liner
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: str = AUDIT_VERSION


def _audit_path(audit_dir: Path) -> Path:
    return audit_dir / "audit.jsonl"


def append_entry(entry: AuditEntry, audit_dir: Path = DEFAULT_AUDIT_DIR) -> None:
    """Append *entry* to the JSONL audit log, creating the directory if needed."""
    try:
        audit_dir.mkdir(parents=True, exist_ok=True)
        with _audit_path(audit_dir).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(entry)) + "\n")
    except OSError as exc:
        raise AuditError(f"Cannot write audit log: {exc}") from exc


def load_entries(audit_dir: Path = DEFAULT_AUDIT_DIR) -> List[AuditEntry]:
    """Return all audit entries, oldest first."""
    path = _audit_path(audit_dir)
    if not path.exists():
        return []
    entries: List[AuditEntry] = []
    try:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    entries.append(AuditEntry(**{k: v for k, v in data.items() if k in AuditEntry.__dataclass_fields__}))
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        raise AuditError(f"Cannot read audit log: {exc}") from exc
    return entries


def clear_entries(audit_dir: Path = DEFAULT_AUDIT_DIR) -> None:
    """Remove all audit entries."""
    path = _audit_path(audit_dir)
    try:
        if path.exists():
            path.unlink()
    except OSError as exc:
        raise AuditError(f"Cannot clear audit log: {exc}") from exc
