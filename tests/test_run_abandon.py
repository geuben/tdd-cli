"""`tdd run abandon`: end a run that will not be finished (issue #150)."""

from __future__ import annotations

from conftest import run_cli, write_plan

from tddcli import gitutil
from tddcli.ledger import Ledger

PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding"
    test: "tests/test_add.py::test_add_two_numbers"
---
# Plan
"""


def ledger(repo):
    return Ledger(gitutil.repo_identity(repo))


def register(repo):
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    return plan


def start(path, plan):
    out = run_cli(path, "run", "start", "--plan", plan)
    assert out["ok"], out
    return out


def outcome(repo, run_id):
    return ledger(repo).one("SELECT outcome FROM run WHERE id = ?", (run_id,))["outcome"]


def test_abandon_ends_the_live_run_as_abandoned(repo):
    plan = register(repo)
    start(repo, plan)

    run_cli(repo, "run", "abandon", "--reason", "superseded by #145")

    row = ledger(repo).one("SELECT outcome, ended_at FROM run")
    assert (row["outcome"], row["ended_at"] is not None) == ("abandoned", True)
