---
closes: 147
cycles:
  - n: 1
    project: tddcli
    title: "tdd metrics reports suite time by phase, the run's wall clock and the suite's share"
    test: "tests/test_time_report.py::test_metrics_reports_suite_time_by_phase_and_the_wall_clock"
    files: ["src/tddcli/render.py"]
    commit_red: "test: tdd metrics reports where a run's time went"
    commit_green: "feat: tdd metrics reports suite time by phase and wall clock"
    commit_refactor: "refactor: tidy the time summary"
  - n: 2
    project: tddcli
    pin_cycle: true
    title: "a live run's wall clock is measured to now"
    test: "tests/test_time_report.py::test_metrics_measures_a_live_runs_wall_clock_to_now"
    files: []
    commit_pin: "test: pin that a live run's wall clock runs to now"
  - n: 3
    project: tddcli
    title: "the friction log carries a Time section with per-phase and per-cycle tables"
    test: "tests/test_time_report.py::test_the_friction_log_carries_a_time_section"
    files: ["src/tddcli/render.py", "docs/PRD.md", "README.md", "CHANGELOG.md"]
    commit_red: "test: the friction log reports suite and wall-clock time"
    commit_green: "feat: the friction log carries a Time section"
    commit_refactor: "docs: time reporting in the PRD, README and changelog"
---

# Issue 147 — report suite durations in `tdd metrics` and the friction log

## Context

Issue #147 (part of #145). The ledger records every suite run's `invocation.duration_ms`, the
run's `started_at` / `ended_at`, and each cycle's `opened_at` / `closed_at`. Nothing reports
them. #145 needed a hand-written SQLite query to find that 68% of a run's wall clock was the
suite. This plan makes the tool report it.

**Done when** (from the issue): `tdd metrics` for a finished run reports suite time per phase,
and the rendered friction log carries the per-cycle table. Both are tested against a fixture
ledger.

Nothing new is recorded. Both outputs are projections in `src/tddcli/render.py`:
- `metrics(ledger, worktree)` builds `tdd metrics`' JSON result, one entry per run in
  `out["runs"]`. `cmd_metrics` returns it, and so does `tdd progress --json`.
- `friction_log(ledger, run)` renders `tdd log render`.

## Design decisions (locked)

1. **The `tdd metrics` shape** (the user chose this on 2026-09-23). Each run entry gains a
   `time` object:

   ```json
   "time": {
     "wall_clock_s": 600.0,
     "suite_s": 222.0,
     "suite_share": 0.37,
     "by_phase": {
       "AWAITING_TEST": {"runs": 2, "suite_s": 60.0},
       "AWAITING_IMPL": {"runs": 3, "suite_s": 102.0},
       "CLOSE_SWEEP":   {"runs": 2, "suite_s": 60.0}
     }
   }
   ```

   - Times are in **seconds, rounded to one decimal**. `suite_share` is rounded to three
     decimals.
   - `by_phase` has one key per `invocation.phase_at` value the run recorded: any of
     `AWAITING_TEST`, `AWAITING_PIN`, `SENSITIVITY`, `AWAITING_IMPL` and `CLOSE_SWEEP`. So the
     phases add up to `suite_s`.
   - `suite_s` is the sum of `duration_ms` over **every** invocation of the run
     (`WHERE run_id = ?`), not only those with a cycle.

2. **Wall clock.** For a run: `run.started_at` to `run.ended_at`, or **to now** while
   `ended_at` is NULL (a live run, for `tdd progress --json`). For a cycle: `opened_at` to
   `closed_at`. A cycle that is still open has no wall clock. The run row is written after
   `run start` captures its baselines, so baseline capture is outside the run's wall clock.
   Nothing records its duration, so it is not reported.

   `suite_share = suite_s / wall_clock_s`, or `None` when `wall_clock_s` is 0. Parse
   timestamps with `datetime.fromisoformat`. The helper `render._elapsed` already does this
   for `tdd progress`, so reuse its approach rather than inventing another.

3. **Where the friction log shows it** (the user chose this on 2026-09-23). A new
   `## Time` section after the last `### Cycle` block and before `## Executor narrative`.
   The existing per-cycle blocks are unchanged. The exact text for the fixture is given in
   cycle 3. The layout:
   - The first line is
     `- Wall clock: {wall/60:.1f} min. Suite: {suite/60:.1f} min ({share:.0%}).`
   - Then a per-phase table: `| Phase | Suite runs | Suite (min) | Average (s) |`. Rows appear
     in the order `AWAITING_TEST`, `AWAITING_PIN`, `SENSITIVITY`, `AWAITING_IMPL`,
     `CLOSE_SWEEP`, with any other `phase_at` value after them, sorted. Only phases the run
     recorded get a row.
   - Then a per-cycle table: `| Cycle | Wall (min) | Suite (min) | Suite runs |`. It has one
     row per cycle, in ascending ordinal. An open cycle's wall clock is `—`. A cycle with no
     runs shows `0.0` and `0`.
   - Minutes use `:.1f`, and the per-phase average in seconds uses `:.1f`.

   One helper computes the numbers for both outputs. It lives in `render.py`, and
   `metrics` and `friction_log` both call it, so the two cannot disagree.

4. **The fixture ledger** is built directly with `Ledger.insert`, with fixed timestamps and
   durations. Every number is independent of the code under test, and each expected value
   below is worked out by hand from the fixture. The run is **blocked**: it ended at 10:10,
   cycle 1 closed at 10:04, and cycle 2 never closed. That is a real shape, since a blocked
   run's last cycle stays open, and it gives the open-cycle `—` row a place without a second
   fixture.

## Deliberate scope cuts (do not build)

- **Cost** (the PRD's "Suite duration, wall clock, cost" row). Premise: the issue names only
  time. Nothing in the ledger records cost, and the issue says nothing new is recorded.

## Cycles

Cycle 1 writes the shared fixture at the top of the new `tests/test_time_report.py`:

```python
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
```

Hand-worked from `RUNS`:
- **Suite:** 222 s = 3.7 min.
- **By phase:** `AWAITING_TEST` has 2 runs, 60 s. `AWAITING_IMPL` has 3 runs, 102 s = 1.7 min,
  averaging 34.0 s. `CLOSE_SWEEP` has 2 runs, 60 s.
- **Wall clock:** 600 s = 10.0 min, so the share is 0.37, or 37%.
- **Cycle 1:** wall 4.0 min, suite 90 s = 1.5 min, 3 runs.
- **Cycle 2:** wall `—`, suite 132 s = 2.2 min, 4 runs.

All of these are exact at one decimal, so rounding cannot move them.

**Probed** in the planning checkout: the fixture builds, and today `render.metrics(ledger, "/wt")["runs"][0]` has no `time` key. `render.friction_log(...)` has no `## Time` section. The probe was deleted.

### Cycle 1 — `tdd metrics` reports where the time went

- **Test** `test_metrics_reports_suite_time_by_phase_and_the_wall_clock(tmp_path, ledger_home)`:
  - `ledger, _ = _ledger(tmp_path)`, then `m = render.metrics(ledger, "/wt")["runs"][0]`.
  - Single assertion:
    `assert m.get("time") == {"wall_clock_s": 600.0, "suite_s": 222.0, "suite_share": 0.37,
    "by_phase": {"AWAITING_TEST": {"runs": 2, "suite_s": 60.0}, "AWAITING_IMPL": {"runs": 3,
    "suite_s": 102.0}, "CLOSE_SWEEP": {"runs": 2, "suite_s": 60.0}}}`.
- **Production target:** `src/tddcli/render.py`. Add the shared helper (decision 3), for
  example `_time_summary(ledger, run)`, returning the run's wall clock and suite seconds, the
  per-phase runs and seconds, and the per-cycle rows. `metrics` sets `"time"` on each run
  entry from it. Compute the wall clock as in decision 2, including "to now" for a live run.
  Cycle 2 pins that.
- **EXPECTED FAILURE** (probed: there is no `time` key today): `AssertionError: assert None ==
  {'by_phase': {...}, 'suite_s': 222.0, 'suite_share': 0.37, 'wall_clock_s': 600.0}`.

### Cycle 2 — pin: a live run's wall clock runs to now

- **Test** `test_metrics_measures_a_live_runs_wall_clock_to_now(tmp_path, ledger_home)`:
  - `ledger, run_id = _ledger(tmp_path)`, then
    `ledger._write("UPDATE run SET ended_at = NULL, outcome = NULL WHERE id = ?", (run_id,))`.
  - `m = render.metrics(ledger, "/wt")["runs"][0]`.
  - Single assertion: `assert m["time"]["wall_clock_s"] > 600`. The run started on
    2026-09-01 and "now" is later, so the true value is far above 600 and does not depend on
    when the test runs.
- **Kind: pin.** It passes on arrival once cycle 1 computes the wall clock as decision 2
  says. If it fails on arrival, cycle 1 left the live case out: stop and raise
  `tdd blocker --kind plan_defect`. Do not add the case here as implementation.
- Sensitivity: make the helper return 0 when `ended_at` is NULL, and the test fails.

### Cycle 3 — the friction log carries a Time section

- **Test** `test_the_friction_log_carries_a_time_section(tmp_path, ledger_home)`:
  - `ledger, run_id = _ledger(tmp_path)`.
  - `text = render.friction_log(ledger, ledger.one("SELECT * FROM run WHERE id = ?", (run_id,)))`.
  - Take the section: `section = text.split("\n## Time\n", 1)[1].split("\n## ", 1)[0] if
    "\n## Time\n" in text else ""`.
  - Single assertion: `assert section.strip() == TIME_SECTION.strip()`, where:

    ```python
    TIME_SECTION = """
    - Wall clock: 10.0 min. Suite: 3.7 min (37%).

    | Phase | Suite runs | Suite (min) | Average (s) |
    |---|---|---|---|
    | AWAITING_TEST | 2 | 1.0 | 30.0 |
    | AWAITING_IMPL | 3 | 1.7 | 34.0 |
    | CLOSE_SWEEP | 2 | 1.0 | 30.0 |

    | Cycle | Wall (min) | Suite (min) | Suite runs |
    |---|---|---|---|
    | 1 | 4.0 | 1.5 | 3 |
    | 2 | — | 2.2 | 4 |
    """
    ```

    Write `TIME_SECTION` at module level without the indentation shown here.
- **Production target:** `src/tddcli/render.py`, `friction_log`. After the per-cycle loop and
  before `run_notes`, append the section from the cycle 1 helper (decision 3).
- **EXPECTED FAILURE** (probed: the log has no `## Time` today): `AssertionError: assert '' ==
  '- Wall clock: 10.0 min. Suite: 3.7 min (37%).\n\n| Phase | …'`.
- **Refactor phase: the docs.**
  - `docs/PRD.md` §11.1: replace the "Suite duration, wall clock, cost" row with "Suite
    duration and wall clock | `invocation.duration_ms` summed per phase and per cycle; wall
    clock from `run.started_at`/`ended_at` (to now while live) and `cycle.opened_at`/`closed_at`
    — reported by `tdd metrics` (`time`) and the friction log's `## Time` section". Then add
    "Cost | not recorded" as its own row.
  - `README.md`: in "The friction log", add that it reports "a Time section: wall clock, suite
    time and its share, per phase and per cycle". In the `tdd metrics` paragraph, add "suite
    time per phase and wall clock". In the command table, make the `tdd metrics` row read
    "fidelity, attempts, violations, interventions, time".
  - `CHANGELOG.md`: add an `### Added` entry under `## [Unreleased]` for #147.

### Behaviour census

| Promise | Test |
|---|---|
| `metrics` reports suite time per phase, the total, the wall clock and the share | cycle 1 |
| phases sum to the total (every `phase_at` value counted) | cycle 1 (the fixture's three phases total 222 s) |
| a live run's wall clock runs to now | cycle 2 |
| the friction log carries the summary, the per-phase table and the per-cycle table | cycle 3 |
| an open cycle shows `—` for wall clock | cycle 3 (cycle 2 of the fixture) |
| `metrics` and the friction log agree | cycle 3's numbers equal cycle 1's, computed by one helper |
| `tdd metrics` and `tdd progress --json` both carry `time` | both return `render.metrics`, unchanged wiring |

There are no fakes (the ledger is real SQLite), no mirrors, no generated artifacts, no schema
change and no `docs/INVARIANTS.md`. The one numeric expectation, the 37% share, is fixture
arithmetic, not a performance target.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-147-time-report            # first, before anything else
    tdd doctor                                       # must report healthy: true
    tdd run start --plan tasks/issue-147-time-report.md

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

**Referee.** Use the released `tdd` on `PATH` (`tdd --version`), never an editable install of
this working tree. `SCHEMA_VERSION` does not change in this plan.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is
  green at the plan's base (638 passed, 2026-09-23); expect `baselines: {tddcli: 0}`.
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`;
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`. Cycle 2 is a pin and will
    ask for it.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|regression|bad_red|tooling>
    --detail '...'`;
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.

  This plan declares no annotation keys beyond the reserved `plan_defect` and
  `friction_note`.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- cycle 1 adds the shared time helper and the `time` object in `metrics`. It does not touch
  `friction_log`.
- cycle 2 is a pin: write the test, and change no production code.
- cycle 3 renders the `## Time` section from the same helper. Its refactor phase carries the
  docs.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-147-time-report-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-147-time-report-friction.md
    git commit -m "docs: friction log for issue-147-time-report"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #147`.

Docs are deliverables. Each of these must be non-empty (cycle 3), or the PR body says which
cycle dropped it and why:
- `git diff --stat origin/main -- docs/PRD.md`
- `git diff --stat origin/main -- README.md`
- `git diff --stat origin/main -- CHANGELOG.md`

The run is refereed by the released tool, which predates this change, so this run's own
friction log will **not** carry a `## Time` section. Cycle 3's test is the evidence. Nothing a
user sees changes beyond the rendered log and the JSON result, so no demo recording is
required.
