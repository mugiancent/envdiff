"""Tests for envdiff.grouper."""

from __future__ import annotations

import pytest

from envdiff.grouper import GroupResult, _extract_prefix, group_keys


# ---------------------------------------------------------------------------
# _extract_prefix
# ---------------------------------------------------------------------------

def test_extract_prefix_returns_first_segment():
    assert _extract_prefix("DB_HOST") == "DB"


def test_extract_prefix_returns_none_when_no_separator():
    assert _extract_prefix("PORT") is None


def test_extract_prefix_custom_separator():
    assert _extract_prefix("APP.HOST", separator=".") == "APP"


def test_extract_prefix_empty_prefix_returns_none():
    # key starting with separator has no meaningful prefix
    assert _extract_prefix("_HIDDEN") is None


# ---------------------------------------------------------------------------
# group_keys
# ---------------------------------------------------------------------------

SAMPLE_KEYS = [
    "DB_HOST", "DB_PORT", "DB_NAME",
    "REDIS_URL", "REDIS_TTL",
    "PORT",
    "DEBUG",
]


def test_groups_are_created_for_shared_prefixes():
    result = group_keys(SAMPLE_KEYS)
    assert "DB" in result.groups
    assert "REDIS" in result.groups


def test_keys_with_no_prefix_are_ungrouped():
    result = group_keys(SAMPLE_KEYS)
    assert "PORT" in result.ungrouped
    assert "DEBUG" in result.ungrouped


def test_singleton_prefix_falls_into_ungrouped():
    keys = ["ONLY_ONE", "OTHER"]
    result = group_keys(keys, min_group_size=2)
    assert "ONLY_ONE" in result.ungrouped


def test_min_group_size_one_promotes_all_prefixed_keys():
    keys = ["DB_HOST", "SOLO_KEY", "PORT"]
    result = group_keys(keys, min_group_size=1)
    assert "DB" in result.groups
    assert "SOLO" in result.groups


def test_group_names_returns_sorted_list():
    result = group_keys(SAMPLE_KEYS)
    assert result.group_names() == sorted(result.groups.keys())


def test_all_keys_includes_every_key():
    result = group_keys(SAMPLE_KEYS)
    assert set(result.all_keys()) == set(SAMPLE_KEYS)


def test_summary_contains_group_count():
    result = group_keys(SAMPLE_KEYS)
    summary = result.summary()
    assert "Groups: 2" in summary


def test_empty_key_list_returns_empty_result():
    result = group_keys([])
    assert result.groups == {}
    assert result.ungrouped == []


def test_group_members_are_sorted():
    keys = ["DB_PORT", "DB_HOST", "DB_NAME"]
    result = group_keys(keys)
    assert result.groups["DB"] == ["DB_HOST", "DB_NAME", "DB_PORT"]
