"""Tests for envdiff.renamer."""
import pytest

from envdiff.renamer import RenameError, RenameResult, rename_keys


SAMPLE_ENV = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "APP_SECRET": "s3cr3t",
}


# ---------------------------------------------------------------------------
# rename_keys – happy-path
# ---------------------------------------------------------------------------

def test_rename_single_key():
    result = rename_keys(SAMPLE_ENV, {"DB_HOST": "DATABASE_HOST"})
    assert "DATABASE_HOST" in result.output
    assert "DB_HOST" not in result.output
    assert result.output["DATABASE_HOST"] == "localhost"


def test_rename_multiple_keys():
    result = rename_keys(SAMPLE_ENV, {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"})
    assert result.rename_count == 2
    assert "DATABASE_HOST" in result.output
    assert "DATABASE_PORT" in result.output


def test_unrenamed_keys_preserved():
    result = rename_keys(SAMPLE_ENV, {"DB_HOST": "DATABASE_HOST"})
    assert result.output["DB_PORT"] == "5432"
    assert result.output["APP_SECRET"] == "s3cr3t"


def test_empty_rename_map_returns_copy():
    result = rename_keys(SAMPLE_ENV, {})
    assert result.output == dict(SAMPLE_ENV)
    assert result.rename_count == 0


def test_values_are_preserved_after_rename():
    result = rename_keys(SAMPLE_ENV, {"APP_SECRET": "APPLICATION_SECRET"})
    assert result.output["APPLICATION_SECRET"] == "s3cr3t"


# ---------------------------------------------------------------------------
# skipped keys
# ---------------------------------------------------------------------------

def test_missing_key_is_skipped_by_default():
    result = rename_keys(SAMPLE_ENV, {"NONEXISTENT": "NEW_KEY"})
    assert "NONEXISTENT" in result.skipped
    assert "NEW_KEY" not in result.output


def test_missing_key_strict_raises():
    with pytest.raises(RenameError, match="strict mode"):
        rename_keys(SAMPLE_ENV, {"NONEXISTENT": "NEW_KEY"}, strict=True)


# ---------------------------------------------------------------------------
# duplicate targets
# ---------------------------------------------------------------------------

def test_duplicate_target_raises():
    with pytest.raises(RenameError, match="Duplicate target"):
        rename_keys(SAMPLE_ENV, {"DB_HOST": "SHARED", "DB_PORT": "SHARED"})


# ---------------------------------------------------------------------------
# RenameResult helpers
# ---------------------------------------------------------------------------

def test_summary_no_skipped():
    result = rename_keys(SAMPLE_ENV, {"DB_HOST": "DATABASE_HOST"})
    assert "1 key(s) renamed" in result.summary
    assert "skipped" not in result.summary


def test_summary_with_skipped():
    result = rename_keys(SAMPLE_ENV, {"MISSING": "NEW"})
    assert "skipped" in result.summary


def test_rename_count_property():
    result = rename_keys(SAMPLE_ENV, {"DB_HOST": "H", "DB_PORT": "P"})
    assert result.rename_count == 2
