"""Why each failing test failed (#105): the adapters work it out, the ledger keeps it
per invocation, and the friction log and `tdd invocation show` print it."""

from __future__ import annotations

import json

from tddcli.ledger import Ledger


def _at(minute):
    return f"2026-09-01T10:{minute:02d}:00+00:00"


def _run(ledger):
    """One contract and one run on a fresh fixture ledger."""
    contract = ledger.insert(
        "plan_contract",
        plan_path="tasks/p.md",
        status="declared",
        declared_cycles=json.dumps([{"n": 1}]),
        annotation_keys="[]",
        registered_at=_at(0),
    )
    return ledger.insert(
        "run",
        plan_contract_id=contract,
        executor_model="m",
        executor_source="declared",
        worktree_path="/wt",
        started_at=_at(0),
        ended_at=_at(10),
        outcome="completed",
        preexisting_dirty="[]",
    )


def test_an_invocation_keeps_the_failure_details_it_was_recorded_with(tmp_path, ledger_home):
    ledger = Ledger(tmp_path / "somerepo")
    run_id = _run(ledger)
    inv = ledger.record_invocation(
        run_id,
        None,
        phase_at="CLOSE_SWEEP",
        project="p",
        adapter="pytest",
        target_test=None,
        target_outcome=None,
        target_failure="",
        total_passed=0,
        total_failed=2,
        other_failures=["p::b", "p::a"],
        duration_ms=1,
        tree_hash=None,
        failures={
            "p::b": {"phase": None, "message": "FAIL: b", "detail": "b out"},
            "p::a": {"phase": "teardown", "message": "RuntimeError: a", "detail": "a out"},
        },
    )
    assert [dict(r) for r in ledger.failure_details(inv)] == [
        {"test_id": "p::a", "phase": "teardown", "message": "RuntimeError: a", "detail": "a out"},
        {"test_id": "p::b", "phase": None, "message": "FAIL: b", "detail": "b out"},
    ]
