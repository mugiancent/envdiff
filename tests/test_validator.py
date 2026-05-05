"""Tests for envdiff.validator."""

import pytest

from envdiff.validator import ValidationResult, validate_env


# ---------------------------------------------------------------------------
# ValidationResult helpers
# ---------------------------------------------------------------------------

def test_is_valid_when_no_issues():
    result = ValidationResult()
    assert result.is_valid is True


def test_is_invalid_when_missing_required():
    result = ValidationResult(missing_required=["SECRET_KEY"])
    assert result.is_valid is False


def test_is_invalid_when_type_errors():
    result = ValidationResult(type_errors={"PORT": "invalid literal"})
    assert result.is_valid is False


def test_summary_ok():
    assert ValidationResult().summary() == "OK"


def test_summary_contains_missing_keys():
    result = ValidationResult(missing_required=["FOO", "BAR"])
    assert "BAR" in result.summary()
    assert "FOO" in result.summary()


# ---------------------------------------------------------------------------
# validate_env
# ---------------------------------------------------------------------------

def test_missing_required_key_reported():
    env = {"PORT": "8080"}
    result = validate_env(env, required_keys={"PORT", "SECRET_KEY"})
    assert "SECRET_KEY" in result.missing_required
    assert "PORT" not in result.missing_required


def test_all_required_keys_present():
    env = {"PORT": "8080", "SECRET_KEY": "abc"}
    result = validate_env(env, required_keys={"PORT", "SECRET_KEY"})
    assert result.missing_required == []


def test_valid_int_type_hint():
    env = {"PORT": "8080"}
    result = validate_env(env, type_hints={"PORT": "int"})
    assert "PORT" not in result.type_errors


def test_invalid_int_type_hint():
    env = {"PORT": "not_a_number"}
    result = validate_env(env, type_hints={"PORT": "int"})
    assert "PORT" in result.type_errors


def test_valid_bool_type_hint():
    for value in ("true", "false", "1", "0", "yes", "no"):
        env = {"DEBUG": value}
        result = validate_env(env, type_hints={"DEBUG": "bool"})
        assert "DEBUG" not in result.type_errors, f"Failed for value: {value}"


def test_invalid_bool_type_hint():
    env = {"DEBUG": "maybe"}
    result = validate_env(env, type_hints={"DEBUG": "bool"})
    assert "DEBUG" in result.type_errors


def test_unknown_keys_reported_when_disallowed():
    env = {"PORT": "8080", "EXTRA": "value"}
    result = validate_env(
        env,
        allow_unknown=False,
        known_keys={"PORT"},
    )
    assert "EXTRA" in result.unknown_keys


def test_unknown_keys_allowed_by_default():
    env = {"PORT": "8080", "EXTRA": "value"}
    result = validate_env(env)
    assert result.unknown_keys == []


def test_type_hint_skipped_for_missing_key():
    """No type error should be raised for a key that isn't present."""
    env = {}
    result = validate_env(env, type_hints={"PORT": "int"})
    assert result.type_errors == {}
