"""`tdd run abandon`: end a run that will not be finished (issue #150)."""

from __future__ import annotations

from conftest import current_user, run_cli, write_plan
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


def test_metrics_reports_the_reason_and_who_abandoned_the_run(repo):
    plan = register(repo)
    start(repo, plan)

    run_cli(repo, "run", "abandon", "--reason", "superseded by #145")

    entry = run_cli(repo, "metrics")["result"]["runs"][0]
    assert entry.get("abandoned") == {
        "reason": "superseded by #145",
        "by": {
            "account": current_user(),
            "executor": "pytest-executor",
            "executor_source": "declared",
        },
    }


def test_abandoning_records_a_human_intervention(repo):
    plan = register(repo)
    start(repo, plan)

    run_cli(repo, "run", "abandon", "--reason", "superseded by #145")

    notes = [r["note"] for r in ledger(repo).all("SELECT note FROM human_intervention")]
    assert notes == ["abandoned: superseded by #145"]


def test_fleet_stops_listing_an_abandoned_run(repo):
    plan = register(repo)
    start(repo, plan)

    run_cli(repo, "run", "abandon", "--reason", "superseded by #145")

    assert run_cli(repo, "fleet", "--json")["result"]["runs"] == []
