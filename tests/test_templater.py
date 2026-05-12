"""Tests for envdiff.templater."""

import pytest

from envdiff.templater import generate_template, TemplateResult


SAMPLE_ENV = {
    "APP_NAME": "myapp",
    "DB_PASSWORD": "s3cr3t",
    "DEBUG": "true",
    "SECRET_KEY": "abc123",
    "PORT": "8080",
}


def test_result_contains_all_keys():
    result = generate_template(SAMPLE_ENV)
    assert set(result.keys) == set(SAMPLE_ENV.keys())


def test_sensitive_values_masked_by_default():
    result = generate_template(SAMPLE_ENV)
    rendered = result.render()
    assert "s3cr3t" not in rendered
    assert "abc123" not in rendered


def test_sensitive_keys_present_with_empty_placeholder():
    result = generate_template(SAMPLE_ENV, placeholder="")
    rendered = result.render()
    assert "DB_PASSWORD=" in rendered
    assert "SECRET_KEY=" in rendered


def test_non_sensitive_values_preserved():
    result = generate_template(SAMPLE_ENV)
    rendered = result.render()
    assert "APP_NAME=myapp" in rendered
    assert "DEBUG=true" in rendered
    assert "PORT=8080" in rendered


def test_mask_sensitive_false_keeps_all_values():
    result = generate_template(SAMPLE_ENV, mask_sensitive=False)
    rendered = result.render()
    assert "DB_PASSWORD=s3cr3t" in rendered
    assert "SECRET_KEY=abc123" in rendered


def test_custom_placeholder_used():
    result = generate_template(SAMPLE_ENV, placeholder="CHANGE_ME")
    rendered = result.render()
    assert "DB_PASSWORD=CHANGE_ME" in rendered


def test_header_comment_prepended():
    result = generate_template(SAMPLE_ENV, header_comment="Auto-generated. Do not commit.")
    rendered = result.render()
    assert rendered.startswith("# Auto-generated")


def test_keys_sorted_alphabetically():
    result = generate_template(SAMPLE_ENV)
    assert result.keys == sorted(SAMPLE_ENV.keys())


def test_render_ends_with_newline():
    result = generate_template(SAMPLE_ENV)
    assert result.render().endswith("\n")


def test_empty_env_returns_empty_template():
    result = generate_template({})
    assert result.keys == []
    assert result.render() == ""


def test_extra_patterns_trigger_masking():
    env = {"MY_TOKEN": "tok_live_abc", "SAFE_KEY": "hello"}
    result = generate_template(env, extra_patterns=[r"MY_TOKEN"], placeholder="***")
    rendered = result.render()
    assert "MY_TOKEN=***" in rendered
    assert "SAFE_KEY=hello" in rendered
