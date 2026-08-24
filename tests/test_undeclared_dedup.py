"""Dedup of undeclared_file_touched within a cycle (issue #55).

When an outside file persists across phases, _stage_and_commit re-classifies it
on every invocation and currently emits an identical event row each time.  The
fix records only the first occurrence per cycle (and re-emits when the outside
set changes — a genuinely new path appeared).
"""

from __future__ import annotations

from conftest import run_cli, write_plan

# ---------------------------------------------------------------------------
# Shared plan bodies
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Cycle 1 — an unchanged undeclared file is flagged once per cycle
# ---------------------------------------------------------------------------

def test_unchanged_outside_file_is_flagged_once_per_cycle(repo):
    """An outside file that persists across all three phases records one event, not three."""
    plan = write_plan(repo, SINGLE_CYCLE_PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]

    # Write a file outside the 'backend' root — it classifies as outside on every phase.
    (repo / "notes.md").write_text("scratch notes\n")

    # Drive RED → GREEN → REFACTOR; notes.md is never staged or committed.
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    run_cli(repo, "advance")  # → AWAITING_IMPL
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    run_cli(repo, "advance")  # → AWAITING_REFACTOR
    run_cli(repo, "advance")  # → complete

    events = run_cli(repo, "metrics")["result"]["runs"][0]["integrity_events"]
    assert events.get("undeclared_file_touched", 0) == 1


