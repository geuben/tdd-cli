"""The cycle-close gate for undeclared file touches (issue #234).

A path flagged `undeclared_file_touched` during a cycle that is still dirty when
that cycle closes holds the close, unless the cycle is the run's last: there the
run-close gate (#69) stays the final backstop.
"""

from __future__ import annotations

import shutil

from conftest import git, run_cli, write_plan

ONE = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    stub_expected: ["app/calc.py"]
---

# Plan
"""

TWO = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    stub_expected: ["app/calc.py"]
  - n: 2
    project: backend
    title: "subtracting two numbers"
    test: "tests/test_sub.py::test_subtract_two_numbers"
    stub_expected: ["app/sub.py"]
---

# Plan
"""

TEST_ADD = """from app.calc import add


def test_add_two_numbers():
    assert add(2, 3) == 5
"""


def _start(repo, body):
    plan = write_plan(repo, body)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]


def _close_cycle_one(repo):
    """Drive the `add` cycle with a stray `notes.md`; return the closing advance's envelope."""
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    run_cli(repo, "advance")  # RED
    (repo / "notes.md").write_text("scratch notes\n")
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    run_cli(repo, "advance")  # GREEN, flags notes.md
    return run_cli(repo, "advance")


def test_the_last_cycle_keeps_the_run_close_gate(repo):
    """At the last cycle the run-close gate blocks, and an unblock completes the run."""
    _start(repo, ONE)
    close = _close_cycle_one(repo)
    resumed = run_cli(repo, "resume", "--unblock", "--note", "discarding scratch notes")

    assert (close["next_action"]["verb"], resumed["next_action"]["verb"]) == ("blocked", "complete")


def _metrics(repo):
    return run_cli(repo, "metrics")["result"]["runs"][0]


def test_a_dirty_flagged_path_holds_the_cycle_close(repo):
    """An earlier cycle's close is held while a path it flagged is still dirty."""
    _start(repo, TWO)
    close = _close_cycle_one(repo)
    run = _metrics(repo)

    assert (
        close["next_action"]["verb"],
        close["result"].get("kind"),
        close["result"].get("paths"),
        run["outcome"],
        run["cycles_closed"],
    ) == ("blocked", "undeclared_file_uncommitted", ["notes.md"], "blocked", 0)


def test_committing_or_discarding_the_held_path_lets_the_cycle_close(repo, tmp_path):
    """Once the held path is clean and the run unblocked, the next advance closes the cycle."""
    copies = {case: tmp_path / case for case in ("commit", "discard")}
    for r in copies.values():
        shutil.copytree(repo, r, symlinks=True)

    outcomes = {}
    for case, r in copies.items():
        _start(r, TWO)
        _close_cycle_one(r)
        if case == "commit":
            git(r, "add", "notes.md")
            git(r, "commit", "-q", "-m", "docs: scratch notes")
        else:
            (r / "notes.md").unlink()
        run_cli(r, "resume", "--unblock", "--note", f"{case} notes.md")
        after = run_cli(r, "advance")
        outcomes[case] = (
            after["run"]["cycle"],
            after["next_action"]["verb"],
            after["next_action"]["detail"].startswith("Cycle 1 closed."),
        )

    assert outcomes == {"commit": (2, "write_test", True), "discard": (2, "write_test", True)}
