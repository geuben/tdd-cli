"""Run-close gate: undeclared_file_touched paths that are uncommitted at close block the run.

Issue #69.
"""

from __future__ import annotations

from conftest import run_cli, write_plan

SINGLE_CYCLE_PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    commit_red: "test: adding two numbers"
    commit_green: "feat: add()"
---

# Plan
"""

TEST_ADD = """from app.calc import add


def test_add_two_numbers():
    assert add(2, 3) == 5
"""


def test_uncommitted_flagged_file_blocks_at_close(repo):
    """An uncommitted outside file present at run close blocks the run with a typed blocker."""
    plan = write_plan(repo, SINGLE_CYCLE_PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]

    # Write an outside file (repo root is outside the 'backend' project root).
    # This causes undeclared_file_touched to fire on the first advance.
    (repo / "notes.md").write_text("scratch notes\n")

    # Drive RED → GREEN → REFACTOR, leaving notes.md uncommitted throughout.
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    run_cli(repo, "advance")  # → AWAITING_IMPL
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    run_cli(repo, "advance")  # → AWAITING_REFACTOR
    final = run_cli(repo, "advance")  # → blocked (gate fires at close)

    assert final["next_action"]["verb"] == "blocked"
    assert final["next_action"]["terminal"] is True


