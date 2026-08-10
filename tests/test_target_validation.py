"""`tdd target` must refuse a name that is not a collected test (#15).

The command previously recorded whatever string it was given. A typo — or an
agent probing the CLI surface with something like `tdd target env` — silently
*changed the target* to a nonexistent test, deferred the failure to the next
suite run, and misattributed it as `not_found`, pointing the executor at a test
that was never supposed to exist. Phase is derived from observed execution;
the target must be grounded in observed collection the same way.
"""

from __future__ import annotations

from conftest import run_cli, write_plan

PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    stub_expected: ["app/calc.py"]
    commit_red: "test: adding two numbers"
    commit_green: "feat: add()"
---

# Plan
"""


def start(repo):
    plan = write_plan(repo, PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    started = run_cli(repo, "run", "start", "--plan", plan)
    assert started["ok"], started


def test_target_refuses_a_name_that_is_not_a_collected_test(repo):
    start(repo)
    out = run_cli(repo, "target", "env")
    assert out["ok"] is False
    assert "not a collected test" in out["error"]


def test_target_suggests_the_closest_collected_ids_on_a_near_miss(repo):
    start(repo)
    out = run_cli(repo, "target", "backend::tests/test_smoke.py::test_smok")
    assert out["ok"] is False
    assert "backend::tests/test_smoke.py::test_smoke" in out["error"]


def test_target_accepts_a_collected_test(repo):
    start(repo)
    out = run_cli(repo, "target", "backend::tests/test_smoke.py::test_smoke")
    assert out["ok"] is True, out
    assert out["result"]["target"] == "backend::tests/test_smoke.py::test_smoke"
