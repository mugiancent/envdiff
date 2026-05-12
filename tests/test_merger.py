"""Tests for envdiff.merger."""

import pytest

from envdiff.merger import MergeError, MergeResult, merge_envs, render_merged


# ---------------------------------------------------------------------------
# merge_envs
# ---------------------------------------------------------------------------

def test_merge_single_env_returns_all_keys():
    result = merge_envs([("a", {"FOO": "1", "BAR": "2"})])
    assert result.merged == {"FOO": "1", "BAR": "2"}


def test_later_env_wins_on_duplicate_key():
    result = merge_envs([
        ("base", {"FOO": "old", "BAR": "keep"}),
        ("override", {"FOO": "new"}),
    ])
    assert result.merged["FOO"] == "new"
    assert result.merged["BAR"] == "keep"


def test_sources_track_winning_file():
    result = merge_envs([
        ("base", {"FOO": "1"}),
        ("prod", {"FOO": "2"}),
    ])
    assert result.sources["FOO"] == "prod"


def test_overridden_records_losing_files():
    result = merge_envs([
        ("a", {"KEY": "1"}),
        ("b", {"KEY": "2"}),
        ("c", {"KEY": "3"}),
    ])
    assert "a" in result.overridden["KEY"]
    assert "b" in result.overridden["KEY"]


def test_restrict_to_filters_keys():
    result = merge_envs(
        [("env", {"FOO": "1", "BAR": "2", "BAZ": "3"})],
        restrict_to={"FOO": "", "BAZ": ""},
    )
    assert set(result.merged.keys()) == {"FOO", "BAZ"}
    assert "BAR" not in result.merged


def test_empty_named_envs_raises():
    with pytest.raises(MergeError):
        merge_envs([])


def test_key_count_property():
    result = merge_envs([("e", {"A": "1", "B": "2"})])
    assert result.key_count == 2


def test_summary_no_overrides():
    result = merge_envs([("e", {"A": "1"})])
    assert "1 key" in result.summary()
    assert "override" not in result.summary()


def test_summary_with_overrides():
    result = merge_envs([
        ("a", {"X": "1"}),
        ("b", {"X": "2"}),
    ])
    assert "override" in result.summary()


# ---------------------------------------------------------------------------
# render_merged
# ---------------------------------------------------------------------------

def test_render_merged_basic():
    result = merge_envs([("e", {"FOO": "bar"})])
    output = render_merged(result)
    assert "FOO=bar" in output


def test_render_merged_with_source_comments():
    result = merge_envs([("prod", {"DB": "postgres"})])
    output = render_merged(result, include_source_comments=True)
    assert "# source: prod" in output
    assert "DB=postgres" in output


def test_render_merged_empty_result():
    result = MergeResult(merged={}, sources={}, overridden={})
    assert render_merged(result) == ""


def test_render_merged_sorted_keys():
    result = merge_envs([("e", {"ZEBRA": "z", "APPLE": "a"})])
    output = render_merged(result)
    lines = [l for l in output.splitlines() if "=" in l]
    assert lines[0].startswith("APPLE")
    assert lines[1].startswith("ZEBRA")
