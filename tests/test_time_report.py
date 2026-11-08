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


def _ledger(tmp_path, runs=None, cycle_projects=("p", "p")):
    """A run that started at 10:00 and was blocked at 10:10. Cycle 1 ran 10:00-10:04;
    cycle 2 opened at 10:04 and never closed. `runs` are (cycle ordinal, phase, project,
    duration_ms); the default is RUNS, all in project `p`."""
    if runs is None:
        runs = [(ordinal, phase, "p", ms) for ordinal, phase, ms in RUNS]
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
            projects=json.dumps([cycle_projects[ordinal - 1]]),
            declared_tests="[]",
            target_tests="[]",
            phase=phase,
            head_at_open="0" * 40,
            opened_at=_at(opened),
            closed_at=_at(closed) if closed is not None else None,
        )
    for ordinal, phase, project, ms in runs:
        ledger.insert(
            "invocation",
            run_id=run_id,
            cycle_id=cycles[ordinal],
            phase_at=phase,
            project=project,
            adapter="pytest",
            other_failures="[]",
            duration_ms=ms,
            started_at=_at(1),
        )
    return ledger, run_id


#: Each cycle's time, worked out by hand: cycle 1 ran 10:00-10:04 with three 30 s suite
#: runs; cycle 2 is open, with suite runs of 30, 42, 30 and 30 s.
CYCLES = [
    {
        "ordinal": 1,
        "opened_at": "2026-09-01T10:00:00+00:00",
        "closed_at": "2026-09-01T10:04:00+00:00",
        "wall_clock_s": 240.0,
        "suite_s": 90.0,
        "runs": 3,
    },
    {
        "ordinal": 2,
        "opened_at": "2026-09-01T10:04:00+00:00",
        "closed_at": None,
        "wall_clock_s": None,
        "suite_s": 132.0,
        "runs": 4,
    },
]


# (cycle ordinal, phase, project, duration_ms): cycle 1 is `server`'s, and its close sweep
# also ran `client`, downstream of an artifact cycle 1 touched. Cycle 2 is `client`'s.
SPLIT_RUNS = [
    (1, "AWAITING_TEST", "server", 30000),
    (1, "AWAITING_IMPL", "server", 30000),
    (1, "CLOSE_SWEEP", "server", 30000),
    (1, "CLOSE_SWEEP", "client", 60000),
    (2, "AWAITING_TEST", "client", 12000),
    (2, "AWAITING_IMPL", "client", 18000),
    (2, "CLOSE_SWEEP", "client", 18000),
]


def _split_ledger(tmp_path):
    return _ledger(tmp_path, SPLIT_RUNS, ("server", "client"))


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
        "by_project": {
            "p": {
                "runs": 7,
                "suite_s": 222.0,
                "by_phase": {
                    "AWAITING_TEST": {"runs": 2, "suite_s": 60.0},
                    "AWAITING_IMPL": {"runs": 3, "suite_s": 102.0},
                    "CLOSE_SWEEP": {"runs": 2, "suite_s": 60.0},
                },
            },
        },
        "cycles": CYCLES,
    }


def test_metrics_reports_suite_time_by_project(tmp_path, ledger_home):
    ledger, _ = _split_ledger(tmp_path)

    m = render.metrics(ledger, "/wt")["runs"][0]

    # client's CLOSE_SWEEP includes the 60 s sweep cycle 1 triggered: credited to the
    # project that ran, not the cycle.
    assert m["time"].get("by_project") == {
        "client": {
            "runs": 4,
            "suite_s": 108.0,
            "by_phase": {
                "AWAITING_TEST": {"runs": 1, "suite_s": 12.0},
                "AWAITING_IMPL": {"runs": 1, "suite_s": 18.0},
                "CLOSE_SWEEP": {"runs": 2, "suite_s": 78.0},
            },
        },
        "server": {
            "runs": 3,
            "suite_s": 90.0,
            "by_phase": {
                "AWAITING_TEST": {"runs": 1, "suite_s": 30.0},
                "AWAITING_IMPL": {"runs": 1, "suite_s": 30.0},
                "CLOSE_SWEEP": {"runs": 1, "suite_s": 30.0},
            },
        },
    }


def test_metrics_reports_each_cycles_time(tmp_path, ledger_home):
    ledger, _ = _ledger(tmp_path)

    m = render.metrics(ledger, "/wt")["runs"][0]

    assert m["time"].get("cycles") == CYCLES


def test_metrics_by_project_is_empty_for_a_run_with_no_invocations(tmp_path, ledger_home):
    ledger, run_id = _ledger(tmp_path)
    ledger._write("DELETE FROM invocation WHERE run_id = ?", (run_id,))

    m = render.metrics(ledger, "/wt")["runs"][0]

    assert m["time"].get("by_project") == {}


def test_metrics_by_project_sums_to_the_suite_total(tmp_path, ledger_home):
    ledger, _ = _split_ledger(tmp_path)

    t = render.metrics(ledger, "/wt")["runs"][0]["time"]

    # The left side comes from suite_time_by_project, the right from suite_time_by_phase.
    assert (
        sum(p["suite_s"] for p in t["by_project"].values()),
        sum(p["runs"] for p in t["by_project"].values()),
    ) == (t["suite_s"], sum(p["runs"] for p in t["by_phase"].values()))


def test_metrics_measures_a_live_runs_wall_clock_to_now(tmp_path, ledger_home):
    ledger, run_id = _ledger(tmp_path)
    ledger._write("UPDATE run SET ended_at = NULL, outcome = NULL WHERE id = ?", (run_id,))

    m = render.metrics(ledger, "/wt")["runs"][0]

    # Started 2026-09-01 and still running: far more than the ten minutes it had at 10:10.
    assert m["time"]["wall_clock_s"] > 600


TIME_SECTION = """
- Wall clock: 10.0 min. Suite: 3.7 min (37%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 2 | 1.0 | 30.0 |
| AWAITING_IMPL | 3 | 1.7 | 34.0 |
| CLOSE_SWEEP | 2 | 1.0 | 30.0 |

| Project | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| p | 7 | 3.7 | 31.7 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 4.0 | 1.5 | 3 |
| 2 | — | 2.2 | 4 |
"""


def test_the_friction_log_carries_a_time_section(tmp_path, ledger_home):
    ledger, run_id = _ledger(tmp_path)

    text = render.friction_log(ledger, ledger.one("SELECT * FROM run WHERE id = ?", (run_id,)))

    section = text.split("\n## Time\n", 1)[1].split("\n## ", 1)[0] if "\n## Time\n" in text else ""
    assert section.strip() == TIME_SECTION.strip()


SPLIT_TIME_SECTION = """
- Wall clock: 10.0 min. Suite: 3.3 min (33%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 2 | 0.7 | 21.0 |
| AWAITING_IMPL | 2 | 0.8 | 24.0 |
| CLOSE_SWEEP | 3 | 1.8 | 36.0 |

| Project | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| client | 4 | 1.8 | 27.0 |
| server | 3 | 1.5 | 30.0 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 4.0 | 2.5 | 4 |
| 2 | — | 0.8 | 3 |
"""


def test_the_friction_log_tables_suite_time_by_project(tmp_path, ledger_home):
    ledger, run_id = _split_ledger(tmp_path)

    text = render.friction_log(ledger, ledger.one("SELECT * FROM run WHERE id = ?", (run_id,)))

    # server's rows were recorded first; the table is in name order.
    section = text.split("\n## Time\n", 1)[1].split("\n## ", 1)[0] if "\n## Time\n" in text else ""
    assert section.strip() == SPLIT_TIME_SECTION.strip()
