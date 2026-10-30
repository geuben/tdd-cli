"""`tdd run start` refuses a plan path a completed run already delivered (issue #97)."""

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


def deliver(repo, plan):
    run_id = run_cli(repo, "run", "start", "--plan", plan)["run"]["id"]
    run_cli(repo, "cycle", "skip", "--reason", "delivered")
    return run_id


def test_a_delivered_plan_is_refused_before_its_suite_runs(repo, tmp_path):
    counter = tmp_path / "suite-runs"
    (repo / "backend/tests/test_smoke.py").write_text(
        f"def test_smoke():\n    with open({str(counter)!r}, 'a') as f:\n        f.write('x')\n"
    )
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    first = deliver(repo, plan)
    ledger(repo).update("run", first, outcome="abandoned")
    deliver(repo, plan)
    ledger(repo).update("run", first, outcome="complete")
    write_plan(repo, PLAN + "\nEdited after delivery.\n")
    run_cli(repo, "plan", "register", plan)
    before = counter.read_text()

    out = run_cli(repo, "run", "start", "--plan", plan)

    assert {
        "reason": out["result"].get("reason"),
        "prior_run_id": out["result"].get("prior_run_id"),
        "ended_at": out["result"].get("ended_at"),
        "suite_ran": counter.read_text() != before,
    } == {
        "reason": "plan_already_delivered",
        "prior_run_id": first,
        "ended_at": ledger(repo).run(first)["ended_at"],
        "suite_ran": False,
    }


def test_a_blocked_or_abandoned_run_does_not_deliver_its_plan(repo):
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    run_cli(repo, "run", "start", "--plan", plan)
    run_cli(repo, "run", "abandon", "--reason", "x")
    after_abandon = run_cli(repo, "run", "start", "--plan", plan)
    run_cli(repo, "blocker", "--kind", "plan_defect", "--detail", "x")

    after_block = run_cli(repo, "run", "start", "--plan", plan)

    assert [after_abandon["ok"], after_block["ok"]] == [True, True]


def test_an_unchanged_plan_is_refused_after_its_delivery(repo):
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    deliver(repo, plan)

    out = run_cli(repo, "run", "start", "--plan", plan)

    assert out["result"].get("reason") == "plan_already_delivered"
