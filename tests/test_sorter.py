"""Tests for envdiff.sorter."""
import pytest

from envdiff.sorter import SortResult, sort_keys, _extract_prefix


SAMPLE_ENV = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "APP_DEBUG": "true",
    "APP_NAME": "envdiff",
    "SECRET_KEY": "abc",
    "PORT": "8080",
}


# ---------------------------------------------------------------------------
# _extract_prefix
# ---------------------------------------------------------------------------

def test_extract_prefix_returns_first_segment():
    assert _extract_prefix("DB_HOST") == "DB"


def test_extract_prefix_returns_none_for_no_separator():
    assert _extract_prefix("PORT") is None


def test_extract_prefix_custom_separator():
    assert _extract_prefix("app.debug", separator=".") == "app"


# ---------------------------------------------------------------------------
# sort_keys — flat / alphabetical
# ---------------------------------------------------------------------------

def test_sort_alphabetical_returns_sorted_keys():
    result = sort_keys(SAMPLE_ENV)
    assert result.all_keys == sorted(SAMPLE_ENV.keys())


def test_sort_no_alphabetical_preserves_insertion_order():
    result = sort_keys(SAMPLE_ENV, alphabetical=False)
    assert result.all_keys == list(SAMPLE_ENV.keys())


def test_flat_sort_has_no_groups():
    result = sort_keys(SAMPLE_ENV)
    assert result.groups == {}
    assert len(result.ungrouped) == len(SAMPLE_ENV)


# ---------------------------------------------------------------------------
# sort_keys — group_by_prefix
# ---------------------------------------------------------------------------

def test_group_by_prefix_creates_expected_groups():
    result = sort_keys(SAMPLE_ENV, group_by_prefix=True)
    assert set(result.groups.keys()) == {"APP", "DB", "SECRET"}


def test_group_by_prefix_ungrouped_contains_no_prefix_keys():
    result = sort_keys(SAMPLE_ENV, group_by_prefix=True)
    assert result.ungrouped == ["PORT"]


def test_group_keys_are_sorted_within_group():
    result = sort_keys(SAMPLE_ENV, group_by_prefix=True, alphabetical=True)
    assert result.groups["DB"] == ["DB_HOST", "DB_PORT"]
    assert result.groups["APP"] == ["APP_DEBUG", "APP_NAME"]


def test_groups_are_sorted_alphabetically():
    result = sort_keys(SAMPLE_ENV, group_by_prefix=True, alphabetical=True)
    assert list(result.groups.keys()) == ["APP", "DB", "SECRET"]


# ---------------------------------------------------------------------------
# sort_keys — prefix_order
# ---------------------------------------------------------------------------

def test_prefix_order_respected():
    result = sort_keys(
        SAMPLE_ENV,
        group_by_prefix=True,
        prefix_order=["DB", "APP"],
    )
    group_names = list(result.groups.keys())
    assert group_names[0] == "DB"
    assert group_names[1] == "APP"


def test_unknown_prefixes_appended_after_prefix_order():
    result = sort_keys(
        SAMPLE_ENV,
        group_by_prefix=True,
        prefix_order=["DB"],
    )
    group_names = list(result.groups.keys())
    assert group_names[0] == "DB"
    assert "APP" in group_names
    assert "SECRET" in group_names


# ---------------------------------------------------------------------------
# SortResult.all_keys
# ---------------------------------------------------------------------------

def test_all_keys_combines_groups_then_ungrouped():
    result = sort_keys(SAMPLE_ENV, group_by_prefix=True, alphabetical=True)
    all_keys = result.all_keys
    # groups come before ungrouped
    assert all_keys.index("APP_DEBUG") < all_keys.index("PORT")
    assert all_keys.index("DB_HOST") < all_keys.index("PORT")
