"""Unblocks, not human interventions (issue #186)."""

from __future__ import annotations

import json
import sqlite3

from conftest import run_cli, write_plan
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

FIDELITY_HEAD = "- Declared cycles: 1\n- Delivered: 0   Skipped: 0\n- Never reached: [1]\n"


def blocked_run(repo):
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]
    run_cli(repo, "blocker", "--kind", "plan_defect", "--detail", "x")


def _at(minute):
    return f"2026-09-01T10:{minute:02d}:00+00:00"


def fixture_ledger(tmp_path, unblocks, abandoned=None) -> tuple[Ledger, sqlite3.Row]:
    """A run with no cycles, a `human_intervention` row per `(minute, note)` in
    `unblocks`, and, when `abandoned` is a `(minute, reason)` pair, what tdd <= 0.15.0's
    `abandon_run` wrote."""
    ledger = Ledger(tmp_path / "somerepo")
    contract = ledger.insert(
        "plan_contract",
        plan_path="tasks/p.md",
        status="declared",
        declared_cycles=json.dumps([{"n": 1}]),
        annotation_keys="[]",
        registered_at=_at(0),
    )
    run_id = ledger.insert(
        "run",
        plan_contract_id=contract,
        executor_model="m",
        executor_source="declared",
        worktree_path="/wt",
        started_at=_at(0),
        ended_at=_at(10),
        outcome="abandoned" if abandoned else "complete",
        preexisting_dirty="[]",
    )
    for minute, note in unblocks:
        ledger.insert("human_intervention", run_id=run_id, note=note, at=_at(minute))
    if abandoned:
        minute, reason = abandoned
        ledger.insert(
            "abandonment",
            run_id=run_id,
            reason=reason,
            account="op",
            executor_model="m",
            executor_source="declared",
            at=_at(minute),
        )
        ledger.insert(
            "human_intervention", run_id=run_id, note=f"abandoned: {reason}", at=_at(minute)
        )
    return ledger, ledger.one("SELECT * FROM run WHERE id = ?", (run_id,))


def fidelity(text):
    if "\n## Plan fidelity\n" not in text:
        return ""
    return text.split("\n## Plan fidelity\n", 1)[1].split("\n## ", 1)[0].strip()


def test_metrics_reports_unblocks_not_human_interventions(repo):
    blocked_run(repo)
    run_cli(repo, "resume", "--unblock", "--note", "fixed the fixture")

    m = run_cli(repo, "metrics")["result"]["runs"][0]

    assert (m.get("unblocks"), "human_interventions" in m) == (1, False)
