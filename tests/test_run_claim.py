"""Worktree claim during baseline collection (issue #4, foundation for #2).

See tasks/multi-agent-feedback.md Part A.
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


def register(repo):
    plan = write_plan(repo, PLAN)
    reg = run_cli(repo, "plan", "register", plan)
    assert reg["ok"], reg
    return plan


def test_second_start_reports_the_active_run_id(repo):
    plan = register(repo)
    first = run_cli(repo, "run", "start", "--plan", plan)
    assert first["ok"], first

    second = run_cli(repo, "run", "start", "--plan", plan)
    assert second["ok"] is False
    assert second["result"]["reason"] == "run_already_active"
    assert second["result"]["run_id"] == 1
