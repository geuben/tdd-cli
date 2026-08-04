"""Worktree claim during baseline collection (issue #4, foundation for #2).

See tasks/multi-agent-feedback.md Part A.
"""

from __future__ import annotations

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
