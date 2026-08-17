"""exec adapter — exit-code oracles as first-class tests.

Each file matching test_paths is one test; exit 0 → passed, non-zero → failed.
Non-executable files without a test_command map to not_collected, not failed.
"""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

from tddcli import config as config_mod
from tddcli.adapters.base import FAILED, NOT_COLLECTED, NOT_FOUND, PASSED
from tddcli.adapters.exec_adapter import ExecAdapter

TOML = """
[project.gates]
root       = "gates"
adapter    = "exec"
test_paths = ["scripts/check-*.sh"]
"""

TOML_WITH_CMD = """
[project.gates]
root         = "gates"
adapter      = "exec"
test_paths   = ["scripts/check-*.sh"]
test_command = "bash {file}"
"""

TOML_ROOT_DOT = """
[project.gates]
root       = "."
adapter    = "exec"
test_paths = ["scripts/check-*.sh"]
"""


def make_adapter(tmp_path: Path, toml: str = TOML) -> ExecAdapter:
    (tmp_path / "tdd.toml").write_text(toml)
    (tmp_path / "gates").mkdir(exist_ok=True)
    cfg = config_mod.load(tmp_path)
    return ExecAdapter(cfg.project("gates"), tmp_path)


def write_script(path: Path, body: str, executable: bool = True) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"#!/bin/bash\n{body}\n")
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return path


# ------------------------------------------------------------------
# Discovery
# ------------------------------------------------------------------


def test_matching_files_are_discovered_as_tests(tmp_path):
    adapter = make_adapter(tmp_path)
    write_script(tmp_path / "gates" / "scripts" / "check-a.sh", "exit 0")
    write_script(tmp_path / "gates" / "scripts" / "check-b.sh", "exit 0")

    collection = adapter.collect()

    assert "gates::scripts/check-a.sh" in collection.tests
    assert "gates::scripts/check-b.sh" in collection.tests


def test_non_matching_files_are_ignored(tmp_path):
    adapter = make_adapter(tmp_path)
    scripts = tmp_path / "gates" / "scripts"
    write_script(scripts / "check-a.sh", "exit 0")
    write_script(scripts / "run.sh", "exit 0")   # does not match check-*.sh

    collection = adapter.collect()

    ids = {t for t in collection.tests}
    assert all("check-a.sh" in t or "check-" in t for t in ids)
    assert not any("run.sh" in t for t in ids)


def test_ids_are_project_namespaced_and_root_relative(tmp_path):
    adapter = make_adapter(tmp_path)
    write_script(tmp_path / "gates" / "scripts" / "check-a.sh", "exit 0")

    collection = adapter.collect()

    assert len(collection.tests) == 1
    (id_,) = collection.tests
    assert id_.startswith("gates::scripts/check-a.sh")


def test_dot_root_project_ids_use_path_relative_to_worktree(tmp_path):
    (tmp_path / "tdd.toml").write_text(TOML_ROOT_DOT)
    cfg = config_mod.load(tmp_path)
    adapter = ExecAdapter(cfg.project("gates"), tmp_path)

    write_script(tmp_path / "scripts" / "check-a.sh", "exit 0")

    collection = adapter.collect()
    assert "gates::scripts/check-a.sh" in collection.tests


def test_no_test_paths_yields_empty_collection(tmp_path):
    toml = "[project.gates]\nroot = 'gates'\nadapter = 'exec'\n"
    (tmp_path / "tdd.toml").write_text(toml)
    (tmp_path / "gates").mkdir()
    cfg = config_mod.load(tmp_path)
    adapter = ExecAdapter(cfg.project("gates"), tmp_path)

    assert adapter.collect().tests == set()


# ------------------------------------------------------------------
# Non-executable files
# ------------------------------------------------------------------


def test_non_executable_file_without_test_command_maps_to_not_collected(tmp_path):
    adapter = make_adapter(tmp_path)
    write_script(tmp_path / "gates" / "scripts" / "check-a.sh", "exit 0", executable=False)

    collection = adapter.collect()

    assert "gates::scripts/check-a.sh" not in collection.tests
    assert "scripts/check-a.sh" in collection.failed_files


def test_non_executable_file_with_test_command_is_collected(tmp_path):
    adapter = make_adapter(tmp_path, TOML_WITH_CMD)
    write_script(tmp_path / "gates" / "scripts" / "check-a.sh", "exit 0", executable=False)

    collection = adapter.collect()

    assert "gates::scripts/check-a.sh" in collection.tests


# ------------------------------------------------------------------
# Verdicts
# ------------------------------------------------------------------


def test_exit_zero_yields_passed(tmp_path):
    adapter = make_adapter(tmp_path)
    write_script(tmp_path / "gates" / "scripts" / "check-ok.sh", "exit 0")

    verdict = adapter.run()

    assert "gates::scripts/check-ok.sh" in verdict.passed
    assert verdict.failed == []


def test_nonzero_exit_yields_failed(tmp_path):
    adapter = make_adapter(tmp_path)
    write_script(tmp_path / "gates" / "scripts" / "check-bad.sh", 'echo "FAIL: something wrong"; exit 1')

    verdict = adapter.run()

    assert "gates::scripts/check-bad.sh" in verdict.failed
    assert verdict.passed == []


def test_failure_output_is_captured(tmp_path):
    adapter = make_adapter(tmp_path)
    write_script(tmp_path / "gates" / "scripts" / "check-bad.sh", 'echo "FAIL: missing migration"; exit 1')

    verdict = adapter.run()
    target = "gates::scripts/check-bad.sh"
    assert target in verdict.failed

    targeted = adapter.run(target)
    assert targeted.target_outcome == FAILED
    assert "FAIL: missing migration" in targeted.target_failure


def test_targeting_runs_only_that_script(tmp_path):
    adapter = make_adapter(tmp_path)
    scripts = tmp_path / "gates" / "scripts"
    write_script(scripts / "check-a.sh", "exit 0")
    write_script(scripts / "check-b.sh", 'echo "FAIL"; exit 1')

    verdict = adapter.run("gates::scripts/check-a.sh")

    assert verdict.target_outcome == PASSED
    # check-b was skipped — not in passed or failed
    assert "gates::scripts/check-b.sh" not in verdict.passed
    assert "gates::scripts/check-b.sh" not in verdict.failed


def test_targeting_absent_id_returns_not_found(tmp_path):
    adapter = make_adapter(tmp_path)
    write_script(tmp_path / "gates" / "scripts" / "check-a.sh", "exit 0")

    verdict = adapter.run("gates::scripts/check-does-not-exist.sh")

    assert verdict.target_outcome == NOT_FOUND


def test_targeting_non_executable_returns_not_collected(tmp_path):
    adapter = make_adapter(tmp_path)
    write_script(tmp_path / "gates" / "scripts" / "check-a.sh", "exit 0", executable=False)

    verdict = adapter.run("gates::scripts/check-a.sh")

    assert verdict.target_outcome == NOT_COLLECTED


# ------------------------------------------------------------------
# test_command template
# ------------------------------------------------------------------


def test_test_command_template_runs_non_executable_file(tmp_path):
    adapter = make_adapter(tmp_path, TOML_WITH_CMD)
    # No executable bit — test_command = "bash {file}" must handle it
    write_script(tmp_path / "gates" / "scripts" / "check-ok.sh", "exit 0", executable=False)

    verdict = adapter.run()

    assert "gates::scripts/check-ok.sh" in verdict.passed


def test_test_command_template_file_placeholder_is_shell_quoted(tmp_path):
    """A path with a space must not be split into two shell words."""
    adapter = make_adapter(tmp_path, TOML_WITH_CMD)
    (tmp_path / "gates" / "scripts").mkdir(parents=True, exist_ok=True)
    weird = tmp_path / "gates" / "scripts" / "check-has space.sh"
    weird.write_text("#!/bin/bash\nexit 0\n")
    # No executable bit — relies on bash {file}

    verdict = adapter.run()
    assert "gates::scripts/check-has space.sh" in verdict.passed


# ------------------------------------------------------------------
# Doctor gate — collectable()
# ------------------------------------------------------------------


def test_collectable_ok_when_all_files_are_executable(tmp_path):
    adapter = make_adapter(tmp_path)
    write_script(tmp_path / "gates" / "scripts" / "check-a.sh", "exit 0")

    result = adapter.collectable()

    assert result.ok is True


def test_collectable_ok_when_no_files_match(tmp_path):
    adapter = make_adapter(tmp_path)

    result = adapter.collectable()

    assert result.ok is True


def test_collectable_fails_for_non_executable_without_test_command(tmp_path):
    adapter = make_adapter(tmp_path)
    write_script(tmp_path / "gates" / "scripts" / "check-a.sh", "exit 0", executable=False)

    result = adapter.collectable()

    assert result.ok is False
    assert "check-a.sh" in result.output
    assert "chmod +x" in result.output


def test_collectable_ok_when_test_command_set_regardless_of_exec_bit(tmp_path):
    adapter = make_adapter(tmp_path, TOML_WITH_CMD)
    write_script(tmp_path / "gates" / "scripts" / "check-a.sh", "exit 0", executable=False)

    result = adapter.collectable()

    assert result.ok is True


# ------------------------------------------------------------------
# Miscellaneous
# ------------------------------------------------------------------


def test_stub_hint_mentions_exit(tmp_path):
    adapter = make_adapter(tmp_path)
    hint = adapter.stub_hint()
    assert "exit" in hint


def test_duration_is_tracked(tmp_path):
    adapter = make_adapter(tmp_path)
    write_script(tmp_path / "gates" / "scripts" / "check-a.sh", "exit 0")

    verdict = adapter.run()

    assert verdict.duration_ms >= 0


def test_mixed_pass_and_fail(tmp_path):
    adapter = make_adapter(tmp_path)
    scripts = tmp_path / "gates" / "scripts"
    write_script(scripts / "check-a.sh", "exit 0")
    write_script(scripts / "check-b.sh", "exit 1")
    write_script(scripts / "check-c.sh", "exit 0")

    verdict = adapter.run()

    assert len(verdict.passed) == 2
    assert len(verdict.failed) == 1
    assert "gates::scripts/check-b.sh" in verdict.failed
