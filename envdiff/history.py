"""History management: index multiple snapshots in a directory."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

from envdiff.snapshot import SnapshotError, load_snapshot, save_snapshot
from envdiff.diff import EnvDiffResult


class HistoryError(Exception):
    """Raised when the history store encounters an error."""


class SnapshotHistory:
    """A directory-backed collection of EnvDiffResult snapshots."""

    def __init__(self, directory: str | os.PathLike) -> None:
        self.directory = Path(directory)

    def _ensure_dir(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, result: EnvDiffResult, name: str) -> Path:
        """Save a result snapshot under *name* (without extension)."""
        if not name or "/" in name or "\\" in name:
            raise HistoryError(f"Invalid snapshot name: {name!r}")
        self._ensure_dir()
        path = self.directory / f"{name}.json"
        save_snapshot(result, path)
        return path

    def load(self, name: str) -> EnvDiffResult:
        """Load a snapshot by *name*."""
        path = self.directory / f"{name}.json"
        try:
            return load_snapshot(path)
        except SnapshotError as exc:
            raise HistoryError(str(exc)) from exc

    def list_snapshots(self) -> list[str]:
        """Return sorted snapshot names available in the history directory."""
        if not self.directory.exists():
            return []
        return sorted(
            p.stem for p in self.directory.glob("*.json")
        )

    def delete(self, name: str) -> None:
        """Delete a snapshot by *name*."""
        path = self.directory / f"{name}.json"
        try:
            path.unlink()
        except FileNotFoundError:
            raise HistoryError(f"Snapshot {name!r} not found")
        except OSError as exc:
            raise HistoryError(f"Could not delete snapshot {name!r}: {exc}") from exc

    def iter_all(self) -> Iterator[tuple[str, EnvDiffResult]]:
        """Yield (name, result) for every snapshot in the history."""
        for name in self.list_snapshots():
            yield name, self.load(name)
