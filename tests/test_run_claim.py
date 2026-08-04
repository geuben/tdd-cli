"""Worktree claim during baseline collection (issue #4, foundation for #2).

See tasks/multi-agent-feedback.md Part A.
"""

from __future__ import annotations

import os
import socket
from concurrent.futures import ThreadPoolExecutor

from conftest import run_cli, write_plan
from tddcli import adapters, gitutil
from tddcli.ledger import Ledger

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


def test_successful_start_leaves_no_claim(repo, monkeypatch):
    """The claim is taken before probing and released once the run has started.

    Spies on `adapters.build`, called once per project during the probe loop
    (P6), rather than on the still-stubbed `Ledger.active_claim` — the seam must
    not depend on the method this cycle is implementing.
    """
    plan = register(repo)
    real_build = adapters.build
    seen_claims: list[bool] = []

    def spy(project, worktree):
        led = Ledger(gitutil.repo_identity(worktree))
        rows = led.all(
            "SELECT * FROM baseline_claim WHERE worktree_path = ?", (str(worktree),)
        )
        seen_claims.append(bool(rows))
        return real_build(project, worktree)

    monkeypatch.setattr(adapters, "build", spy)

    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out

    assert any(seen_claims), "claim was never taken"

    led = Ledger(gitutil.repo_identity(repo))
    assert led.all("SELECT * FROM baseline_claim") == []


def test_start_is_rejected_while_a_baseline_is_collecting(repo):
    plan = register(repo)
    led = Ledger(gitutil.repo_identity(repo))
    led.claim(
        str(repo), hostname=socket.gethostname(), pid=os.getpid(), projects_total=1,
    )

    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"] is False
    assert out["result"]["reason"] == "baseline_in_progress"


def test_only_one_of_two_concurrent_starts_wins(repo):
    """P1, reproduced as a test. Assert on returned envelopes only — `run_cli`
    redirects stdout process-globally and threaded output interleaves (P1 caveat).

    Calls `cmd_run_start` directly rather than through `run_cli`: `contextlib.
    redirect_stdout` is itself process-global, and two threads entering/exiting it
    concurrently can hand one thread an empty buffer before either envelope is ever
    inspected — a capture-layer race, not the claim race this test targets. `cwd` is
    set once, outside the thread pool, since both attempts target the same worktree
    and need no per-call `chdir`.
    """
    import os as os_mod

    from tddcli.cli import build_parser, cmd_run_start

    plan = register(repo)
    parser = build_parser()

    def attempt(_):
        args = parser.parse_args(["run", "start", "--plan", plan])
        return cmd_run_start(args).to_dict()

    prev = os_mod.getcwd()
    os_mod.chdir(repo)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, range(2)))
    finally:
        os_mod.chdir(prev)

    oks = [r["ok"] for r in results]
    assert oks.count(True) == 1, results
