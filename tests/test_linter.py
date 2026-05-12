"""Tests for envdiff.linter."""
import pytest

from envdiff.linter import lint_env, LintResult, LintIssue


def test_no_issues_for_clean_env():
    env = {"DATABASE_URL": "postgres://localhost/db", "PORT": "8080"}
    result = lint_env(env)
    assert not result.has_issues


def test_lowercase_key_raises_error():
    result = lint_env({"my_key": "value"})
    codes = [i.code for i in result.issues]
    assert 'E001' in codes


def test_allow_lowercase_suppresses_e001():
    result = lint_env({"my_key": "value"}, allow_lowercase=True)
    codes = [i.code for i in result.issues]
    assert 'E001' not in codes


def test_leading_whitespace_in_value_warns():
    result = lint_env({"MY_KEY": "  value"})
    codes = [i.code for i in result.issues]
    assert 'W001' in codes


def test_trailing_whitespace_in_value_warns():
    result = lint_env({"MY_KEY": "value  "})
    codes = [i.code for i in result.issues]
    assert 'W001' in codes


def test_sensitive_empty_value_warns():
    result = lint_env({"SECRET_KEY": ""})
    codes = [i.code for i in result.issues]
    assert 'W002' in codes


def test_non_sensitive_empty_value_no_w002():
    result = lint_env({"APP_NAME": ""})
    codes = [i.code for i in result.issues]
    assert 'W002' not in codes


def test_placeholder_value_warns():
    result = lint_env({"API_KEY": "CHANGEME"})
    codes = [i.code for i in result.issues]
    assert 'W003' in codes


def test_placeholder_case_insensitive():
    result = lint_env({"API_KEY": "changeme"})
    codes = [i.code for i in result.issues]
    assert 'W003' in codes


def test_summary_no_issues():
    result = lint_env({"PORT": "8080"})
    assert result.summary() == 'No lint issues found.'


def test_summary_with_issues():
    result = lint_env({"bad_key": "CHANGEME"})
    summary = result.summary()
    assert 'error' in summary
    assert 'warning' in summary


def test_errors_and_warnings_properties():
    result = lint_env({"bad_key": "CHANGEME"})
    assert len(result.errors) >= 1
    assert len(result.warnings) >= 1


def test_multiple_keys_accumulate_issues():
    env = {
        "good_key": "CHANGEME",
        "another_bad": "  spaces  ",
        "SECRET": "",
    }
    result = lint_env(env)
    assert len(result.issues) >= 3
