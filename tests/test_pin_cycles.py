"""Pin cycles: characterisation before refactor (§6.2).

Nine of seventeen cycles in the motivating run passed on arrival, five of them
deliberate pins. Without a declared kind, every one is logged as a discipline failure
and the RED-first violation rate becomes useless on refactoring plans.
"""

from __future__ import annotations

from conftest import git, run_cli, write_plan

PIN_PLAN = """---
cycles:
  - n: 1
    project: backend
    pin_cycle: true
    title: "existing behaviour of greet()"
    test: "tests/test_greet.py::test_greet_returns_hello"
---

# Plan
"""

PIN_TEST = """from app.greet import greet


def test_greet_returns_hello():
    assert greet("world") == "hello world"
"""


def setup_pin(repo):
    (repo / "backend" / "app" / "greet.py").write_text(
        'def greet(name):\n    return f"hello {name}"\n'
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "existing behaviour")
    plan = write_plan(repo, PIN_PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    started = run_cli(repo, "run", "start", "--plan", plan)
    assert started["ok"], started
    return started


def test_pin_cycle_opens_in_its_own_phase(repo):
    started = setup_pin(repo)
    assert started["run"]["phase"] == "AWAITING_PIN"
    assert started["run"]["kind"] == "pin"
    assert "passes on arrival" in started["next_action"]["detail"]


def test_pin_that_passes_demands_a_sensitivity_check_not_a_violation(repo):
    setup_pin(repo)
    (repo / "backend" / "tests" / "test_greet.py").write_text(PIN_TEST)

    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "run_sensitivity_check", out
    assert out["run"]["phase"] == "SENSITIVITY_REQUIRED"

    metrics = run_cli(repo, "metrics")["result"]["runs"][0]
    # R6.2 — a pin passing on arrival is its defined behaviour.
    assert metrics["red_first_violation_rate"] is None
    assert "red_first_violation" not in metrics["integrity_events"]


def test_a_pin_that_fails_is_rejected(repo):
    setup_pin(repo)
    (repo / "backend" / "tests" / "test_greet.py").write_text(
        "from app.greet import greet\n\n\n"
        "def test_greet_returns_hello():\n    assert greet('x') == 'nope'\n"
    )
    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "write_test"
    assert "must pass on arrival" in out["next_action"]["detail"]


def test_pin_cannot_reach_refactor_without_a_verified_sensitivity_check(repo):
    setup_pin(repo)
    (repo / "backend" / "tests" / "test_greet.py").write_text(PIN_TEST)
    run_cli(repo, "advance")

    blocked = run_cli(repo, "advance")
    assert blocked["next_action"]["verb"] == "run_sensitivity_check"
    assert blocked["run"]["phase"] == "SENSITIVITY_REQUIRED"

    run_cli(repo, "sensitivity", "begin")
    (repo / "backend" / "app" / "greet.py").write_text(
        'def greet(name):\n    return "goodbye"\n'
    )
    assert run_cli(repo, "sensitivity", "check")["ok"]
    assert run_cli(repo, "sensitivity", "end")["result"]["restored_ok"] is True

    moved = run_cli(repo, "advance")
    assert moved["run"]["phase"] == "AWAITING_REFACTOR", moved


def test_advance_is_refused_while_a_sensitivity_check_is_open(repo):
    setup_pin(repo)
    (repo / "backend" / "tests" / "test_greet.py").write_text(PIN_TEST)
    run_cli(repo, "advance")
    run_cli(repo, "sensitivity", "begin")

    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "run_sensitivity_check"
    assert "deliberately mutated" in out["next_action"]["detail"]


def test_a_mutation_that_does_not_bite_is_rejected(repo):
    setup_pin(repo)
    (repo / "backend" / "tests" / "test_greet.py").write_text(PIN_TEST)
    run_cli(repo, "advance")
    run_cli(repo, "sensitivity", "begin")
    # An irrelevant edit: the test still passes, so it pins nothing.
    (repo / "backend" / "app" / "greet.py").write_text(
        'def greet(name):\n    return f"hello {name}"\n\n\nUNUSED = 1\n'
    )
    out = run_cli(repo, "sensitivity", "check")
    assert out["ok"] is False
    assert "pins nothing" in out["error"]
