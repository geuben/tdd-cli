"""Untouched pre-existing failures are rerun before they block (#73, PRD R9.1f).

The flake is a test that counts its own executions in a file outside the repository
and fails on chosen ones: `run start`'s baseline is execution 1, RED's and GREEN's
target-only runs never execute it, GREEN's whole-suite run is execution 2, a close
sweep after a content edit is execution 3, and each rerun is the next one.
"""

from __future__ import annotations

import json
import shutil

from conftest import git, run_cli, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger

ID = "backend::tests/test_legacy.py::test_legacy"

PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding"
    test: "tests/test_add.py::test_adding"
    files: ["app/calc.py"{files}]
{extra}    commit_red: "test: adding"
    commit_green: "feat: add"
    commit_refactor: "refactor: add"
{more}---
"""


def _flaky(counter, rule, name="test_legacy"):
    """A test that counts its executions in `counter` and fails while `rule` holds for `n`."""
    return (
        f"def {name}():\n"
        "    import pathlib\n"
        f"    p = pathlib.Path({str(counter)!r})\n"
        "    n = int(p.read_text()) + 1 if p.exists() else 1\n"
        "    p.write_text(str(n))\n"
        f"    assert not ({rule}), n\n"
    )


def _to_green(
    repo, counter, rule, *, files="", extra="", more="", where="tests/test_legacy.py", toml=""
):
    """Commit the flaky test at `where`, start a run, confirm RED on test_adding and write
    the implementation. Returns the run id; the next `tdd advance` is GREEN."""
    (repo / "backend" / where).write_text(_flaky(counter, rule))
    if toml:  # the fixture's [project.backend] table is the file's last
        with open(repo / "tdd.toml", "a") as f:
            f.write(toml)
    calc = repo / "backend" / "app" / "calc.py"
    calc.write_text("def add(a, b):\n    raise NotImplementedError\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "flaky legacy test")
    plan = write_plan(repo, PLAN.format(files=files, extra=extra, more=more))
    run_cli(repo, "plan", "register", plan)
    run_id = run_cli(repo, "run", "start", "--plan", plan)["run"]["id"]
    add = repo / "backend" / "tests" / "test_add.py"
    head = add.read_text() + "\n\n" if add.exists() else ""
    add.write_text(
        head + "from app.calc import add\n\n\ndef test_adding():\n    assert add(2, 3) == 5\n"
    )
    run_cli(repo, "advance")  # RED
    calc.write_text("def add(a, b):\n    return a + b\n")
    return run_id


def _flaky_events(repo, run_id):
    ledger = Ledger(gitutil.repo_identity(repo))
    return [json.loads(d) for d in ledger.event_details(run_id, "flaky_pre_existing")]


def test_green_passes_when_an_untouched_failure_passes_on_rerun(repo, tmp_path):
    _to_green(repo, tmp_path / "count", "n == 2")
    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "refactor_or_advance"


def test_a_cleared_failure_is_recorded_as_flaky_pre_existing_with_both_outcomes(repo, tmp_path):
    run_id = _to_green(repo, tmp_path / "count", "n == 2")
    run_cli(repo, "advance")
    assert _flaky_events(repo, run_id) == [
        {"test": ID, "phase": "AWAITING_IMPL", "outcomes": ["failed", "passed"]}
    ]


def test_a_green_failure_that_fails_again_carries_its_rerun_outcomes(repo, tmp_path):
    _to_green(repo, tmp_path / "count", "n >= 2")
    out = run_cli(repo, "advance")
    assert (
        out["next_action"]["verb"],
        out["result"]["other_failures"],
        out["result"].get("rerun_outcomes"),
    ) == ("fix_regression", [ID], {ID: ["failed", "failed"]})


def test_the_close_sweep_closes_when_an_untouched_failure_passes_on_rerun(repo, tmp_path):
    run_id = _to_green(repo, tmp_path / "count", "n == 3")
    run_cli(repo, "advance")  # GREEN: execution 2
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    total = a + b\n    return total\n"
    )
    out = run_cli(repo, "advance")  # the close sweep: execution 3
    assert (out["next_action"]["verb"], [e["phase"] for e in _flaky_events(repo, run_id)]) == (
        "complete",
        ["CLOSE_SWEEP"],
    )


def test_a_close_sweep_failure_that_fails_again_carries_its_rerun_outcomes(repo, tmp_path):
    _to_green(repo, tmp_path / "count", "n >= 3")
    run_cli(repo, "advance")  # GREEN: execution 2
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    total = a + b\n    return total\n"
    )
    out = run_cli(repo, "advance")  # the close sweep: execution 3
    assert (
        out["next_action"]["verb"],
        out["result"]["failures"],
        out["result"].get("rerun_outcomes"),
    ) == ("fix_regression", [ID], {ID: ["failed", "failed"]})


def test_a_failure_in_any_file_the_plan_declares_is_not_rerun(repo, tmp_path):
    CASES = {
        "files_project_relative": {"files": ', "tests/test_legacy.py"'},
        "files_repo_relative": {"files": ', "backend/tests/test_legacy.py"'},
        "stub_expected": {"extra": '    stub_expected: ["tests/test_legacy.py"]\n'},
        "modifies_tests": {"extra": '    modifies_tests: ["tests/test_legacy.py::test_legacy"]\n'},
        "target_file": {"where": "tests/test_add.py"},
        "ancillary_files": {"more": 'ancillary_files: ["backend/tests/test_legacy.py"]\n'},
        "later_cycle": {
            "more": (
                "  - n: 2\n    project: backend\n    title: \"later\"\n"
                '    test: "tests/test_later.py::test_later"\n'
                '    files: ["tests/test_legacy.py"]\n'
                '    commit_red: "test: l"\n    commit_green: "feat: l"\n'
            )
        },
    }
    cases = {name: shutil.copytree(repo, tmp_path / name) for name in CASES}
    verbs = {}
    for name, kw in CASES.items():
        _to_green(cases[name], tmp_path / f"{name}-count", "n == 2", **kw)
        verbs[name] = run_cli(cases[name], "advance")["next_action"]["verb"]
    assert verbs == dict.fromkeys(CASES, "fix_regression")
