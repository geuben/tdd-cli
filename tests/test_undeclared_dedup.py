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


# ---------------------------------------------------------------------------
# Cycle 2 — a newly-appearing undeclared path re-emits
# ---------------------------------------------------------------------------

def test_a_new_undeclared_path_re_emits(repo):
    """When a second undeclared path appears mid-cycle, a new event is emitted."""
    plan = write_plan(repo, SINGLE_CYCLE_PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]

    # Create a.md before RED so it is classified as outside at RED.
    (repo / "a.md").write_text("note A\n")

    # RED: outside == ["a.md"]
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    run_cli(repo, "advance")  # → AWAITING_IMPL

    # Before GREEN, add b.md — now outside == ["a.md", "b.md"] (sorted).
    (repo / "b.md").write_text("note B\n")

    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    run_cli(repo, "advance")  # → AWAITING_REFACTOR
    run_cli(repo, "advance")  # → complete

    events = run_cli(repo, "metrics")["result"]["runs"][0]["integrity_events"]
    assert events.get("undeclared_file_touched", 0) == 2

    # The second event must carry the enlarged set.
    log_path = repo / "friction.md"
    run_cli(repo, "log", "render", "--out", str(log_path))
    log_text = log_path.read_text()
    assert '["a.md", "b.md"]' in log_text


# ---------------------------------------------------------------------------
# Cycle 3 — the dedup is scoped to the cycle, not the run
# ---------------------------------------------------------------------------

TWO_CYCLE_PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    commit_red: "test: adding two numbers"
    commit_green: "feat: add()"
  - n: 2
    project: backend
    title: "subtracting two numbers"
    test: "tests/test_sub.py::test_subtract_two_numbers"
    commit_red: "test: subtracting two numbers"
    commit_green: "feat: subtract()"
---

# Plan
"""

TEST_SUB = """from app.calc import subtract


def test_subtract_two_numbers():
    assert subtract(5, 3) == 2
"""


def test_dedup_is_per_cycle_not_per_run(repo):
    """Each cycle touching the same stray path records its own event."""
    plan = write_plan(repo, TWO_CYCLE_PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]

    # Create shared.md once; it will be outside across both cycles.
    (repo / "shared.md").write_text("shared scratch\n")

    # -- Cycle 1: add --
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    run_cli(repo, "advance")  # RED → AWAITING_IMPL
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    run_cli(repo, "advance")  # GREEN → AWAITING_REFACTOR
    run_cli(repo, "advance")  # REFACTOR → cycle 2

    # -- Cycle 2: subtract --
    (repo / "backend" / "tests" / "test_sub.py").write_text(TEST_SUB)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    return a + b\n\n"
        "def subtract(a, b):\n    raise NotImplementedError\n"
    )
    run_cli(repo, "advance")  # RED → AWAITING_IMPL
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    return a + b\n\n"
        "def subtract(a, b):\n    return a - b\n"
    )
    run_cli(repo, "advance")  # GREEN → AWAITING_REFACTOR
    run_cli(repo, "advance")  # REFACTOR → complete

    events = run_cli(repo, "metrics")["result"]["runs"][0]["integrity_events"]
    # Each cycle touching shared.md must contribute its own event row.
    assert events.get("undeclared_file_touched", 0) == 2
