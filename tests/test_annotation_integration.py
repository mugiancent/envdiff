"""Integration tests: annotate_env feeds correctly into annotate_cmd output."""
import json
from pathlib import Path
from argparse import Namespace

import pytest

from envdiff.annotator import annotate_env
from envdiff.commands.annotate_cmd import cmd_annotate


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "DATABASE_URL=postgres://localhost/mydb\n"
        "APP_ENV=production\n"
        "debug=false\n"
        "PORT=  9000\n"
        "API_SECRET=hunter2\n"
    )
    return p


def test_annotator_sensitive_and_lint_counts(env_file):
    from envdiff.parser import parse_env_file
    env = parse_env_file(str(env_file))
    result = annotate_env(env, source=str(env_file))
    assert len(result.sensitive_keys()) >= 2  # DATABASE_URL, API_SECRET
    assert len(result.keys_with_issues()) >= 1  # debug (lowercase)


def test_cmd_json_matches_annotator(env_file, capsys):
    from envdiff.parser import parse_env_file
    env = parse_env_file(str(env_file))
    library_result = annotate_env(env, source=str(env_file))

    args = Namespace(
        file=str(env_file),
        format="json",
        show_values=True,
        allow_lowercase=False,
        sensitive_patterns="",
    )
    rc = cmd_annotate(args)
    assert rc == 0

    data = json.loads(capsys.readouterr().out)
    cmd_keys = {k["key"] for k in data["keys"]}
    lib_keys = set(library_result.keys())
    assert cmd_keys == lib_keys


def test_allow_lowercase_flag_suppresses_e001(env_file, capsys):
    args = Namespace(
        file=str(env_file),
        format="json",
        show_values=True,
        allow_lowercase=True,
        sensitive_patterns="",
    )
    cmd_annotate(args)
    data = json.loads(capsys.readouterr().out)
    debug_entry = next(k for k in data["keys"] if k["key"] == "debug")
    codes = [i["code"] for i in debug_entry["lint_issues"]]
    assert "E001" not in codes
