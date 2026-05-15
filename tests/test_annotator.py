"""Tests for envdiff.annotator."""
import pytest
from envdiff.annotator import annotate_env, AnnotationResult, KeyAnnotation


SAMPLE_ENV = {
    "DATABASE_URL": "postgres://localhost/db",
    "APP_NAME": "myapp",
    "SECRET_KEY": "supersecret",
    "debug": "true",  # lowercase — lint error
    "PORT": "  8080",  # leading whitespace — lint warning
}


def test_returns_annotation_result():
    result = annotate_env({"APP_NAME": "myapp"}, source=".env")
    assert isinstance(result, AnnotationResult)
    assert result.source == ".env"


def test_all_keys_annotated():
    result = annotate_env(SAMPLE_ENV, source=".env")
    assert set(result.keys()) == set(SAMPLE_ENV.keys())


def test_sensitive_key_flagged():
    result = annotate_env({"SECRET_KEY": "abc", "APP_NAME": "x"}, source=".env")
    assert result.annotations["SECRET_KEY"].sensitive is True
    assert result.annotations["APP_NAME"].sensitive is False


def test_sensitive_keys_list():
    result = annotate_env(
        {"DATABASE_URL": "x", "PORT": "8080", "API_TOKEN": "t"}, source=".env"
    )
    sensitive = result.sensitive_keys()
    assert "DATABASE_URL" in sensitive
    assert "API_TOKEN" in sensitive
    assert "PORT" not in sensitive


def test_extra_sensitive_patterns():
    result = annotate_env(
        {"MY_CUSTOM_CRED": "val"}, source=".env", extra_sensitive_patterns=["CRED"]
    )
    assert result.annotations["MY_CUSTOM_CRED"].sensitive is True


def test_lint_issues_attached_to_key():
    result = annotate_env({"debug": "true"}, source=".env")
    annotation = result.annotations["debug"]
    assert annotation.has_lint_issues is True
    codes = [i.code for i in annotation.lint_issues]
    assert "E001" in codes


def test_clean_key_has_no_lint_issues():
    result = annotate_env({"APP_NAME": "myapp"}, source=".env")
    assert result.annotations["APP_NAME"].has_lint_issues is False


def test_keys_with_issues_returns_correct_keys():
    result = annotate_env({"debug": "true", "APP_NAME": "ok"}, source=".env")
    assert "debug" in result.keys_with_issues()
    assert "APP_NAME" not in result.keys_with_issues()


def test_to_dict_structure():
    result = annotate_env({"SECRET_KEY": "s"}, source=".env")
    d = result.annotations["SECRET_KEY"].to_dict()
    assert d["key"] == "SECRET_KEY"
    assert d["source"] == ".env"
    assert d["sensitive"] is True
    assert isinstance(d["lint_issues"], list)


def test_value_preserved_in_annotation():
    result = annotate_env({"APP_NAME": "myapp"}, source=".env")
    assert result.annotations["APP_NAME"].value == "myapp"


def test_allow_lowercase_suppresses_e001():
    result = annotate_env({"debug": "true"}, source=".env", allow_lowercase=True)
    codes = [i.code for i in result.annotations["debug"].lint_issues]
    assert "E001" not in codes
