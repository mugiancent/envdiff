"""Tests for envdiff.redactor."""

import pytest

from envdiff.redactor import (
    REDACTED_PLACEHOLDER,
    is_sensitive,
    redact,
)


# ---------------------------------------------------------------------------
# is_sensitive
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", [
    "SECRET",
    "DB_PASSWORD",
    "APP_TOKEN",
    "API_KEY",
    "PRIVATE_KEY",
    "AWS_SECRET_ACCESS_KEY",
    "GITHUB_AUTH",
    "USER_CREDENTIALS",
    "PASSWD",
])
def test_is_sensitive_returns_true_for_known_patterns(key):
    assert is_sensitive(key) is True


@pytest.mark.parametrize("key", [
    "APP_ENV",
    "PORT",
    "DEBUG",
    "DATABASE_URL",
    "LOG_LEVEL",
])
def test_is_sensitive_returns_false_for_safe_keys(key):
    assert is_sensitive(key) is False


def test_is_sensitive_custom_pattern():
    assert is_sensitive("INTERNAL_PIN", patterns=[r".*PIN.*"]) is True
    assert is_sensitive("API_KEY", patterns=[r".*PIN.*"]) is False


# ---------------------------------------------------------------------------
# redact
# ---------------------------------------------------------------------------

def test_redact_replaces_sensitive_values():
    env = {"API_KEY": "abc123", "PORT": "8080"}
    result = redact(env)
    assert result["API_KEY"] == REDACTED_PLACEHOLDER
    assert result["PORT"] == "8080"


def test_redact_does_not_mutate_original():
    env = {"DB_PASSWORD": "secret"}
    redact(env)
    assert env["DB_PASSWORD"] == "secret"


def test_redact_custom_placeholder():
    env = {"APP_TOKEN": "tok_xyz"}
    result = redact(env, placeholder="<hidden>")
    assert result["APP_TOKEN"] == "<hidden>"


def test_redact_empty_env():
    assert redact({}) == {}


def test_redact_all_safe_keys_unchanged():
    env = {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}
    assert redact(env) == env


def test_redact_custom_pattern():
    env = {"INTERNAL_PIN": "1234", "APP_ENV": "prod"}
    result = redact(env, patterns=[r".*PIN.*"])
    assert result["INTERNAL_PIN"] == REDACTED_PLACEHOLDER
    assert result["APP_ENV"] == "prod"
