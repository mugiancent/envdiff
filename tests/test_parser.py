"""Tests for envdiff.parser."""

import pytest
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError


def write_env(tmp_path: Path, content: str) -> Path:
    p = tmp_path / ".env"
    p.write_text(content, encoding="utf-8")
    return p


def test_parse_simple_key_value(tmp_path):
    f = write_env(tmp_path, "KEY=value\nANOTHER=123\n")
    result = parse_env_file(f)
    assert result == {"KEY": "value", "ANOTHER": "123"}


def test_parse_skips_comments_and_blank_lines(tmp_path):
    content = "# comment\n\nKEY=val\n# another comment\n"
    f = write_env(tmp_path, content)
    result = parse_env_file(f)
    assert result == {"KEY": "val"}


def test_parse_quoted_values(tmp_path):
    content = 'A="hello world"\nB=\'single quoted\'\n'
    f = write_env(tmp_path, content)
    result = parse_env_file(f)
    assert result["A"] == "hello world"
    assert result["B"] == "single quoted"


def test_parse_empty_value(tmp_path):
    f = write_env(tmp_path, "EMPTY=\n")
    result = parse_env_file(f)
    assert result["EMPTY"] is None


def test_parse_value_with_equals(tmp_path):
    f = write_env(tmp_path, "URL=http://example.com?a=1&b=2\n")
    result = parse_env_file(f)
    assert result["URL"] == "http://example.com?a=1&b=2"


def test_parse_file_not_found():
    with pytest.raises(EnvParseError, match="File not found"):
        parse_env_file("/nonexistent/.env")


def test_parse_malformed_line(tmp_path):
    f = write_env(tmp_path, "BADLINE\n")
    with pytest.raises(EnvParseError, match="Malformed line"):
        parse_env_file(f)


def test_parse_empty_key(tmp_path):
    f = write_env(tmp_path, "=value\n")
    with pytest.raises(EnvParseError, match="Empty key"):
        parse_env_file(f)
