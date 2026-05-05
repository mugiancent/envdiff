"""Tests for envdiff.diff."""

import pytest
from envdiff.diff import diff_envs, EnvDiffResult


BASE = {"KEY_A": "1", "KEY_B": "2", "SHARED": "same"}
COMPARE = {"KEY_B": "99", "KEY_C": "3", "SHARED": "same"}


def test_missing_in_compare():
    result = diff_envs(BASE, COMPARE)
    assert "KEY_A" in result.missing_in_compare
    assert "SHARED" not in result.missing_in_compare


def test_missing_in_base():
    result = diff_envs(BASE, COMPARE)
    assert "KEY_C" in result.missing_in_base


def test_mismatched_values():
    result = diff_envs(BASE, COMPARE)
    assert "KEY_B" in result.mismatched
    assert result.mismatched["KEY_B"] == {"base": "2", "compare": "99"}


def test_no_mismatch_when_check_values_false():
    result = diff_envs(BASE, COMPARE, check_values=False)
    assert result.mismatched == {}


def test_identical_envs_no_differences():
    env = {"A": "1", "B": "2"}
    result = diff_envs(env, env.copy())
    assert not result.has_differences


def test_has_differences_flag():
    result = diff_envs(BASE, COMPARE)
    assert result.has_differences


def test_summary_no_differences():
    env = {"X": "1"}
    result = diff_envs(env, env.copy(), base_file=".env", compare_file=".env.prod")
    summary = result.summary()
    assert "No differences" in summary


def test_summary_with_differences():
    result = diff_envs(
        BASE, COMPARE, base_file=".env", compare_file=".env.staging"
    )
    summary = result.summary()
    assert "KEY_A" in summary
    assert "KEY_C" in summary
    assert "KEY_B" in summary
    assert "->." not in summary  # sanity check formatting


def test_none_value_mismatch():
    base = {"KEY": None}
    compare = {"KEY": "set"}
    result = diff_envs(base, compare)
    assert "KEY" in result.mismatched
    assert result.mismatched["KEY"] == {"base": None, "compare": "set"}
