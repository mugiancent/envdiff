"""Snapshot support: save and load env diff results for later comparison."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from envdiff.diff import EnvDiffResult


class SnapshotError(Exception):
    """Raised when a snapshot cannot be saved or loaded."""


_SNAPSHOT_VERSION = 1


def save_snapshot(result: EnvDiffResult, path: str | os.PathLike) -> None:
    """Persist an EnvDiffResult to a JSON snapshot file."""
    payload: dict[str, Any] = {
        "version": _SNAPSHOT_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base": result.base,
        "compare": result.compare,
        "missing_in_compare": list(result.missing_in_compare),
        "missing_in_base": list(result.missing_in_base),
        "mismatched": result.mismatched,
    }
    try:
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        raise SnapshotError(f"Could not write snapshot to {path!r}: {exc}") from exc


def load_snapshot(path: str | os.PathLike) -> EnvDiffResult:
    """Load an EnvDiffResult from a previously saved snapshot file."""
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise SnapshotError(f"Could not read snapshot from {path!r}: {exc}") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"Invalid JSON in snapshot {path!r}: {exc}") from exc

    version = payload.get("version")
    if version != _SNAPSHOT_VERSION:
        raise SnapshotError(
            f"Unsupported snapshot version {version!r} (expected {_SNAPSHOT_VERSION})"
        )

    try:
        return EnvDiffResult(
            base=payload["base"],
            compare=payload["compare"],
            missing_in_compare=set(payload["missing_in_compare"]),
            missing_in_base=set(payload["missing_in_base"]),
            mismatched=payload["mismatched"],
        )
    except KeyError as exc:
        raise SnapshotError(f"Snapshot is missing required field: {exc}") from exc
