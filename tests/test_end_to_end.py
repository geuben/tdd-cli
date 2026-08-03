"""End-to-end: a real git repo, a real pytest suite, the real state machine."""

from __future__ import annotations

import json

from conftest import git, run_cli, write_plan

PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    stub_expected: ["app/calc.py"]
    commit_red: "test: adding two numbers"
    commit_green: "feat: add()"
  - n: 2
    project: backend
    title: "subtracting"
    test: "tests/test_sub.py::test_subtract"
---

# Plan
"""

TEST_ADD = """from app.calc import add


def test_add_two_numbers():
    assert add(2, 3) == 5
"""


def start(repo):
    plan = write_plan(repo, PLAN)
    reg = run_cli(repo, "plan", "register", plan)
    assert reg["ok"], reg
    assert reg["result"]["cycles"] == 2
    started = run_cli(repo, "run", "start", "--plan", plan)
    assert started["ok"], started
    return started


def test_run_start_opens_the_first_cycle(repo):
    started = start(repo)
    assert started["run"]["cycle"] == 1
    assert started["run"]["phase"] == "AWAITING_TEST"
    assert started["next_action"]["verb"] == "write_test"
    assert started["next_action"]["terminal"] is False


def test_run_start_refuses_a_dirty_tree(repo):
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    (repo / "backend" / "app" / "stray.py").write_text("x = 1\n")
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"] is False
    assert "dirty" in out["error"]


def test_uncollectable_target_asks_for_a_stub_not_a_human(repo):
    """The prior system reported this as `not_found` and told the agent to ask a human."""
    start(repo)
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "create_stub"
    assert out["result"]["not_collected"] == ["backend::tests/test_add.py::test_add_two_numbers"]


def test_full_red_green_cycle_commits_and_advances(repo):
    start(repo)
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )

    red = run_cli(repo, "advance")
    assert red["next_action"]["verb"] == "write_implementation", red
    assert red["run"]["phase"] == "AWAITING_IMPL"
    # The RED commit carries the test and the declared stub, and nothing else.
    assert set(red["result"]["staged"]) == {
        "backend/tests/test_add.py", "backend/app/calc.py"
    }
    log = git(repo, "log", "-1", "--pretty=%s%n%b")
    assert "test: adding two numbers" in log
    assert "TDD-Cycle: 1" in log
    assert "TDD-Phase: red" in log

    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    green = run_cli(repo, "advance")
    assert green["next_action"]["verb"] == "refactor_or_advance", green
    assert green["run"]["phase"] == "AWAITING_REFACTOR"
    assert "feat: add()" in git(repo, "log", "-1", "--pretty=%s")

    closed = run_cli(repo, "advance")
    assert closed["run"]["cycle"] == 2, closed
    assert closed["next_action"]["verb"] == "write_test"


def test_implementation_written_during_red_is_recorded_and_not_committed(repo):
    """R9.14 — the staged set proves it, with no source parsing."""
    start(repo)
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    (repo / "backend" / "app" / "sneaky.py").write_text("VALUE = 1\n")

    out = run_cli(repo, "advance")
    # add() already works, so this is also a red-first violation; the point here is
    # that the undeclared implementation file was never staged.
    assert "backend/app/sneaky.py" not in (out["result"].get("staged") or [])


def test_no_change_since_last_run_is_refused_but_retry_is_allowed(repo):
    start(repo)
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    run_cli(repo, "advance")  # -> AWAITING_IMPL

    first = run_cli(repo, "advance")
    assert first["next_action"]["verb"] == "write_implementation"
    second = run_cli(repo, "advance")
    assert "no_change_since_last_run" in second["next_action"]["detail"]

    retried = run_cli(repo, "advance", "--retry")
    assert "no_change_since_last_run" not in retried["next_action"]["detail"]


def test_passing_on_arrival_demands_a_sensitivity_check(repo):
    start(repo)
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "run_sensitivity_check", out
    assert out["run"]["phase"] == "AWAITING_TEST"


def test_sensitivity_check_verifies_restore(repo):
    start(repo)
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    run_cli(repo, "advance")

    # The RED test and the stub are both uncommitted here — the tree is legitimately
    # dirty, and restoration must return to *this* state, not to HEAD.
    assert run_cli(repo, "sensitivity", "begin")["ok"]
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return 0\n")
    checked = run_cli(repo, "sensitivity", "check")
    assert checked["ok"], checked
    ended = run_cli(repo, "sensitivity", "end")
    assert ended["ok"] and ended["result"]["restored_ok"] is True
    assert (repo / "backend" / "app" / "calc.py").read_text() == "def add(a, b):\n    return a + b\n"


def test_cycle_skip_is_sanctioned_and_records_a_reason(repo):
    start(repo)
    out = run_cli(repo, "cycle", "skip", "--reason", "plan counted direct raises")
    assert out["ok"], out
    assert out["result"]["skipped"] == 1
    assert out["run"]["cycle"] == 2


def test_blocker_releases_the_run_and_a_human_can_unblock(repo):
    start(repo)
    blocked = run_cli(repo, "blocker", "--kind", "plan_defect", "--detail", "cycle 1 is void")
    assert blocked["next_action"]["verb"] == "blocked"
    assert blocked["next_action"]["terminal"] is True

    assert run_cli(repo, "status")["result"]["active"] is False

    needs_note = run_cli(repo, "resume", "--unblock")
    assert needs_note["ok"] is False

    resumed = run_cli(repo, "resume", "--unblock", "--note", "deleted the stale handler")
    assert resumed["ok"], resumed
    assert resumed["run"]["cycle"] == 1


def test_unknown_blocker_kind_is_rejected(repo):
    start(repo)
    out = run_cli(repo, "blocker", "--kind", "vibes", "--detail", "x")
    assert out["ok"] is False


def test_friction_log_and_metrics_render_from_the_ledger(repo):
    start(repo)
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    run_cli(repo, "advance")
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    run_cli(repo, "advance")

    out = run_cli(repo, "log", "render", "--out", str(repo / "friction.md"))
    assert out["ok"]
    text = (repo / "friction.md").read_text()
    assert "Implementation Friction Log" in text
    assert "Plan fidelity" in text
    assert "Declared cycles: 2" in text
    assert "[red]" in text and "[green]" in text

    metrics = run_cli(repo, "metrics")
    assert metrics["result"]["runs"][0]["cycles_declared"] == 2
    assert "not comparable" in metrics["result"]["note"]


def test_doctor_ignores_nested_checkouts(repo):
    """A worktree under .claude/worktrees/ is a separate checkout with its own work."""
    nested = repo / ".claude" / "worktrees" / "other" / "backend"
    nested.mkdir(parents=True)
    (nested / ".tdd-state.json").write_text("{}")
    (repo / ".claude" / "worktrees" / "other" / ".git").write_text("gitdir: elsewhere\n")

    out = run_cli(repo, "doctor")
    legacy = next(c for c in out["result"]["checks"] if c["check"] == "no legacy state artifacts")
    assert legacy["ok"] is True, legacy

    (repo / "backend" / ".tdd-state.json").write_text("{}")
    out = run_cli(repo, "doctor")
    legacy = next(c for c in out["result"]["checks"] if c["check"] == "no legacy state artifacts")
    assert legacy["ok"] is False
