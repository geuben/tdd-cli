"""How much of the suite each phase runs (#148, PRD R9.1a–R9.1d).

RED, pin and the sensitivity check run only the target; GREEN runs the whole suite
for every adapter, which is what makes a target-only RED safe.
"""

from __future__ import annotations

import stat

from conftest import git, run_cli, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger

PLAN = """---
cycles:
  - n: 1
    project: {project}
    {kind}title: "t"
    test: "{test}"
    commit_red: "test: t"
    commit_green: "feat: t"
    commit_pin: "test: pin"
---
"""


def _sh(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/bash\n" + body + "\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _exec_repo(repo):
    """`repo`, re-registered as one exec project `gates` whose committed
    check-mode.sh passes while lib/mode.txt says `old`."""
    (repo / "tdd.toml").write_text(
        '[project.gates]\nroot = "gates"\nadapter = "exec"\n'
        'test_paths = ["scripts/check-*.sh"]\nlint = []\ntypecheck = []\n'
    )
    (repo / "gates" / "lib").mkdir(parents=True)
    (repo / "gates" / "lib" / "mode.txt").write_text("old\n")
    _sh(repo / "gates" / "scripts" / "check-mode.sh", 'test "$(cat lib/mode.txt)" = old')
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "exec project")
    return repo


def _start(repo, project, test, kind=""):
    plan = write_plan(repo, PLAN.format(project=project, kind=kind, test=test))
    run_cli(repo, "plan", "register", plan)
    run_cli(repo, "run", "start", "--plan", plan)


def test_an_adopted_target_is_evaluated_in_the_same_advance(repo):
    _exec_repo(repo)
    _start(repo, "gates", "scripts/check-answer.sh")
    # A new script under another name: the declared one is never written.
    _sh(repo / "gates" / "scripts" / "check-reply.sh", 'test "$(cat lib/answer.txt)" = 42')

    out = run_cli(repo, "advance")

    assert out["next_action"]["verb"] == "write_implementation", out


def test_red_is_not_blocked_by_a_failing_test_elsewhere(repo):
    _start(repo, "backend", "tests/test_add.py::test_adding")
    tests = repo / "backend" / "tests"
    (tests / "test_other.py").write_text("def test_other():\n    assert False\n")
    (tests / "test_add.py").write_text("def test_adding():\n    assert False\n")

    out = run_cli(repo, "advance")

    assert out["next_action"]["verb"] == "write_implementation", out


def _observed_by_phase(repo, *phases):
    ledger = Ledger(gitutil.repo_identity(repo))
    marks = ", ".join("?" for _ in phases)
    rows = ledger.all(
        f"SELECT phase_at, others_observed FROM invocation WHERE phase_at IN ({marks}) ORDER BY id",
        phases,
    )
    return [tuple(r) for r in rows]


def test_red_records_others_unobserved_and_green_records_them_observed(repo):
    calc = repo / "backend" / "app" / "calc.py"
    calc.write_text("def add(a, b):\n    raise NotImplementedError\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "calc stub")
    _start(repo, "backend", "tests/test_add.py::test_adding")
    (repo / "backend" / "tests" / "test_add.py").write_text(
        "from app.calc import add\n\n\ndef test_adding():\n    assert add(2, 3) == 5\n"
    )
    run_cli(repo, "advance")
    calc.write_text("def add(a, b):\n    return a + b\n")
    run_cli(repo, "advance")

    observed = _observed_by_phase(repo, "AWAITING_TEST", "AWAITING_IMPL")

    assert observed == [("AWAITING_TEST", 0), ("AWAITING_IMPL", 1)]


PIN = "pin_cycle: true\n    "


def test_a_pin_is_not_blocked_by_a_failing_test_elsewhere(repo):
    _start(repo, "backend", "tests/test_smoke.py::test_smoke", kind=PIN)
    (repo / "backend" / "tests" / "test_other.py").write_text(
        "def test_other():\n    assert False\n"
    )

    out = run_cli(repo, "advance")

    assert out["next_action"]["verb"] == "run_sensitivity_check", out


def test_a_sensitivity_check_runs_only_the_target(repo):
    calc = repo / "backend" / "app" / "calc.py"
    calc.write_text("def add(a, b):\n    return a + b\n")
    (repo / "backend" / "tests" / "test_add.py").write_text(
        "from app.calc import add\n\n\ndef test_adding():\n    assert add(2, 3) == 5\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "add and its test")
    _start(repo, "backend", "tests/test_add.py::test_adding", kind=PIN)
    run_cli(repo, "advance")
    run_cli(repo, "sensitivity", "begin")
    calc.write_text("def add(a, b):\n    return a - b\n")
    run_cli(repo, "sensitivity", "check")

    observed = _observed_by_phase(repo, "SENSITIVITY")

    assert observed == [("SENSITIVITY", 0)]


def test_green_on_an_exec_project_is_blocked_by_a_failing_script_elsewhere(repo):
    """R9.1b for an adapter that can narrow: GREEN is the whole suite, so the
    close-sweep skip after it is sound (#153)."""
    _exec_repo(repo)
    _start(repo, "gates", "scripts/check-answer.sh")
    gates = repo / "gates"
    _sh(gates / "scripts" / "check-answer.sh", 'test "$(cat lib/answer.txt)" = 42')
    run_cli(repo, "advance")
    (gates / "lib" / "answer.txt").write_text("42\n")
    (gates / "lib" / "mode.txt").write_text("new\n")  # breaks the committed check-mode.sh

    out = run_cli(repo, "advance")

    assert out["next_action"]["verb"] == "fix_regression", out
