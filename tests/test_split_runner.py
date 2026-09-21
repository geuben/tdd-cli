"""The runner role: `tdd` invoked through sudo, as the uid that owns the ledger."""

from __future__ import annotations

from conftest import current_user, run_cli, write_plan

MINIMAL_PLAN = """\
---
cycles:
  - n: 1
    project: backend
    title: "placeholder"
    test: "tests/test_smoke.py::test_smoke"
    commit_red: "test: placeholder"
    commit_green: "feat: placeholder"
---
# Minimal plan for split-mode tests
"""


def test_run_start_spawns_git_and_the_suite_as_the_agent(repo, split_runner):
    plan = write_plan(repo, MINIMAL_PLAN)
    run_cli(repo, "plan", "register", plan)

    out = run_cli(repo, "run", "start", "--plan", plan)

    as_agent = f"-u {current_user()} -- "
    lines = split_runner.shim.lines()
    spawned = (
        out["ok"],
        any(as_agent + "git -C" in line for line in lines),
        any(as_agent + "/bin/sh -c" in line for line in lines),
    )
    assert spawned == (True, True, True)
