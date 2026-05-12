"""Watch .env files for changes and report diffs on modification."""

from __future__ import annotations

import time
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Optional

from envdiff.parser import parse_env_file
from envdiff.diff import diff_envs, EnvDiffResult


class WatcherError(Exception):
    """Raised when the watcher encounters an unrecoverable error."""


@dataclass
class WatchState:
    """Tracks the last-seen mtime and parsed contents of a watched file."""

    path: Path
    mtime: float
    contents: Dict[str, str] = field(default_factory=dict)


def _snapshot_file(path: Path) -> WatchState:
    """Read a file and return a WatchState capturing its current state."""
    mtime = path.stat().st_mtime
    contents = parse_env_file(path)
    return WatchState(path=path, mtime=mtime, contents=contents)


def watch(
    base_path: Path,
    compare_path: Path,
    on_change: Callable[[EnvDiffResult], None],
    *,
    poll_interval: float = 1.0,
    check_values: bool = True,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *base_path* and *compare_path* for changes.

    Calls *on_change* with an :class:`EnvDiffResult` whenever either file is
    modified.  Runs indefinitely unless *max_iterations* is set (useful for
    testing).

    Raises :class:`WatcherError` if either path does not exist on startup.
    """
    for p in (base_path, compare_path):
        if not p.exists():
            raise WatcherError(f"File not found: {p}")

    states: Dict[str, WatchState] = {
        "base": _snapshot_file(base_path),
        "compare": _snapshot_file(compare_path),
    }

    iterations = 0
    while max_iterations is None or iterations < max_iterations:
        time.sleep(poll_interval)
        changed = False

        for key, path in (("base", base_path), ("compare", compare_path)):
            try:
                current_mtime = path.stat().st_mtime
            except FileNotFoundError:
                raise WatcherError(f"Watched file disappeared: {path}")

            if current_mtime != states[key].mtime:
                states[key] = _snapshot_file(path)
                changed = True

        if changed:
            result = diff_envs(
                states["base"].contents,
                states["compare"].contents,
                base_name=str(base_path),
                compare_name=str(compare_path),
                check_values=check_values,
            )
            on_change(result)

        iterations += 1
