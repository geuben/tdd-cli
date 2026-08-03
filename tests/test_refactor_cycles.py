"""Refactor-only cycles (§6.3).

A third of `router-deps-containers.md` is behaviour-preserving migration with no new
test: the existing suite is the guard. `cycle skip` would be wrong — real work happens
— so these open straight into the refactor phase.
"""

from __future__ import annotations

import pytest

from tddcli.contract import REFACTOR, ContractError, parse

from conftest import git, run_cli, write_plan

PLAN = """---
cycles:
  - n: 1
    project: backend
    refactor_cycle: true
    title: "auth router takes a deps container"
    files: ["app/routers/auth.py"]
    commit_refactor: "refactor: auth router takes an identity deps container"
  - n: 2
    project: backend
    title: "no router constructs a repository"
    test: "tests/test_discipline.py::test_no_router_constructs_a_repository"
---
"""


def test_refactor_cycle_declares_no_test():
    body = """---
cycles:
  - n: 1
    project: backend
    refactor_cycle: true
    test: "tests/a.py::test_x"
---
"""
    with pytest.raises(ContractError, match="declares no test"):
        parse(body, "p.md")


def test_a_cycle_without_a_test_must_say_it_is_a_refactor():
    body = """---
cycles:
  - n: 1
    project: backend
---
"""
    with pytest.raises(ContractError, match="refactor_cycle"):
        parse(body, "p.md")


def test_kinds_are_exclusive():
    body = """---
cycles:
  - n: 1
    project: backend
    refactor_cycle: true
    pin_cycle: true
---
"""
    with pytest.raises(ContractError, match="kinds are exclusive"):
        parse(body, "p.md")


def test_refactor_cycle_parses_without_a_target():
    cycle = parse(PLAN, "p.md").cycles[0]
    assert cycle.kind == REFACTOR
    assert cycle.tests == []


def test_refactor_cycle_opens_straight_into_the_refactor_phase(repo):
    plan = write_plan(repo, PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    started = run_cli(repo, "run", "start", "--plan", plan)
    assert started["ok"], started
    assert started["run"]["phase"] == "AWAITING_REFACTOR"
    assert started["run"]["kind"] == "refactor"


def test_refactor_cycle_closes_when_the_existing_suite_stays_green(repo):
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    run_cli(repo, "run", "start", "--plan", plan)

    (repo / "backend" / "app" / "moved.py").write_text("VALUE = 1\n")
    out = run_cli(repo, "advance")
    assert out["run"]["cycle"] == 2, out
    assert "refactor: auth router" in git(repo, "log", "-1", "--pretty=%s")


def test_refactor_cycle_is_blocked_by_a_regression(repo):
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    run_cli(repo, "run", "start", "--plan", plan)

    (repo / "backend" / "tests" / "test_smoke.py").write_text(
        "def test_smoke():\n    assert False\n"
    )
    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "fix_regression", out


def test_refactor_cycles_are_excluded_from_the_red_first_metric(repo):
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    run_cli(repo, "run", "start", "--plan", plan)
    (repo / "backend" / "app" / "moved.py").write_text("VALUE = 1\n")
    run_cli(repo, "advance")

    metrics = run_cli(repo, "metrics")["result"]["runs"][0]
    # Only cycle 2 counts as a standard cycle.
    assert metrics["red_first_violation_rate"] == 0.0
