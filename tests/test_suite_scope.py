"""How much of the suite each phase runs (#148, PRD R9.1a–R9.1d).

RED, pin and the sensitivity check run only the target; GREEN runs the whole suite
for every adapter, which is what makes a target-only RED safe.
"""

from __future__ import annotations

import stat

from conftest import git, run_cli, write_plan

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
