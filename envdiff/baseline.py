"""Baseline comparison: compare current env against a saved snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envdiff.diff import EnvDiffResult, diff_envs
from envdiff.history import HistoryError, SnapshotHistory
from envdiff.snapshot import SnapshotError, load_snapshot


@dataclass
class BaselineCompareResult:
    """Result of comparing the current env against a baseline snapshot."""

    snapshot_name: str
    diff: EnvDiffResult


class BaselineError(Exception):
    """Raised when a baseline operation fails."""


def compare_against_snapshot(
    current_env: dict[str, str],
    snapshot_path: str,
    check_values: bool = True,
) -> BaselineCompareResult:
    """Load a snapshot and diff *current_env* against it.

    The snapshot is treated as the **base** so that keys present in the
    snapshot but absent from *current_env* appear as ``missing_in_compare``.
    """
    try:
        snap = load_snapshot(snapshot_path)
    except SnapshotError as exc:
        raise BaselineError(f"Cannot load snapshot '{snapshot_path}': {exc}") from exc

    base_env: dict[str, str] = snap.get("env", {})
    if not isinstance(base_env, dict):
        raise BaselineError("Snapshot 'env' field is not a mapping.")

    diff = diff_envs(
        base=base_env,
        compare=current_env,
        base_name=snap.get("name", "snapshot"),
        compare_name="current",
        check_values=check_values,
    )
    return BaselineCompareResult(snapshot_name=snap.get("name", "snapshot"), diff=diff)


def compare_against_latest(
    current_env: dict[str, str],
    history_dir: str,
    check_values: bool = True,
) -> Optional[BaselineCompareResult]:
    """Compare *current_env* against the most-recent snapshot in *history_dir*.

    Returns ``None`` if no snapshots exist yet.
    """
    try:
        history = SnapshotHistory(history_dir)
        entries = history.list()
    except HistoryError as exc:
        raise BaselineError(f"Cannot read history: {exc}") from exc

    if not entries:
        return None

    latest_path = entries[-1]["path"]
    return compare_against_snapshot(current_env, latest_path, check_values=check_values)
