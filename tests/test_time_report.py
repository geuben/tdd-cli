"""Where a run's time went (#147): `tdd metrics` and the friction log, against a
fixture ledger whose every number is chosen by hand."""

from __future__ import annotations

import json

from tddcli import render
from tddcli.ledger import Ledger


def _at(minute):
    return f"2026-09-01T10:{minute:02d}:00+00:00"


# (cycle ordinal, phase, duration_ms)
RUNS = [
    (1, "AWAITING_TEST", 30000),
    (1, "AWAITING_IMPL", 30000),
    (1, "CLOSE_SWEEP", 30000),
    (2, "AWAITING_TEST", 30000),
    (2, "AWAITING_IMPL", 42000),
    (2, "AWAITING_IMPL", 30000),
    (2, "CLOSE_SWEEP", 30000),
]


def _ledger(tmp_path):
    """A run that started at 10:00 and was blocked at 10:10. Cycle 1 ran 10:00-10:04;
    cycle 2 opened at 10:04 and never closed."""
    ledger = Ledger(tmp_path / "somerepo")
    contract = ledger.insert(
        "plan_contract",
        plan_path="tasks/p.md",
        status="declared",
        declared_cycles=json.dumps([{"n": 1}, {"n": 2}]),
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
        outcome="blocked",
        preexisting_dirty="[]",
    )
    cycles = {}
    for ordinal, opened, closed, phase in ((1, 0, 4, "CLOSED"), (2, 4, None, "AWAITING_REFACTOR")):
        cycles[ordinal] = ledger.insert(
            "cycle",
            run_id=run_id,
            ordinal=ordinal,
            kind="standard",
            projects='["p"]',
            declared_tests="[]",
            target_tests="[]",
            phase=phase,
            head_at_open="0" * 40,
            opened_at=_at(opened),
            closed_at=_at(closed) if closed is not None else None,
        )
    for ordinal, phase, ms in RUNS:
        ledger.insert(
            "invocation",
            run_id=run_id,
            cycle_id=cycles[ordinal],
            phase_at=phase,
            project="p",
            adapter="pytest",
            other_failures="[]",
            duration_ms=ms,
            started_at=_at(1),
        )
    return ledger, run_id


def test_metrics_reports_suite_time_by_phase_and_the_wall_clock(tmp_path, ledger_home):
    ledger, _ = _ledger(tmp_path)

    m = render.metrics(ledger, "/wt")["runs"][0]

    assert m.get("time") == {
        "wall_clock_s": 600.0,
        "suite_s": 222.0,
        "suite_share": 0.37,
        "by_phase": {
            "AWAITING_TEST": {"runs": 2, "suite_s": 60.0},
            "AWAITING_IMPL": {"runs": 3, "suite_s": 102.0},
            "CLOSE_SWEEP": {"runs": 2, "suite_s": 60.0},
        },
    }


def test_metrics_measures_a_live_runs_wall_clock_to_now(tmp_path, ledger_home):
    ledger, run_id = _ledger(tmp_path)
    ledger._write("UPDATE run SET ended_at = NULL, outcome = NULL WHERE id = ?", (run_id,))

    m = render.metrics(ledger, "/wt")["runs"][0]

    # Started 2026-09-01 and still running: far more than the ten minutes it had at 10:10.
    assert m["time"]["wall_clock_s"] > 600
