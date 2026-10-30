# Implementation Friction Log: tasks/issue-210-mypy-typecheck.md

- Run: 14
- Executor: claude-opus-5-5 (source: claimed)
- Plan blob: `c61d2229c0b8f1a1f3b7609e5131dfdaf4cd14cd` (declared)
- Started: 2026-10-30T19:24:20.160975+00:00  Ended: 2026-10-30T19:42:54.457515+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 6
- Delivered: 6   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 6: mypy is the close sweep's typecheck gate and a CI step  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `678f31d78` [refactor] build: type-check with mypy in the close sweep and in CI (4 files)
- **Event — config_changed:** e8172b2df36d97e79f2e0d937ece15446903e058d7e1148bcedfa03f87ace8b7

### Cycle 5: the CLI, the adapters and the tests type-check  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `838ba9cb7` [refactor] refactor: make the CLI, the adapters and the tests type-check (7 files)

### Cycle 4: the engine, advance and render type-check  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 3}
- **Failures — invocation 375 (CLOSE_SWEEP, tddcli):**
  - `tddcli::tests/test_ledger_surface.py::test_no_module_but_the_ledger_speaks_sql` [call]: AssertionError: assert {'machine.py'...ort sqlite3']} == {}
- **Failures — invocation 376 (CLOSE_SWEEP, tddcli):**
  - `tddcli::tests/test_ledger_surface.py::test_no_module_but_the_ledger_speaks_sql` [call]: AssertionError: assert {'machine.py'...ort sqlite3']} == {}
- **Commits:**
  - `ba5d13e80` [refactor] refactor: make the engine, advance and render type-check (3 files)
  - `5c3f76c6d` [refactor] refactor: make the engine, advance and render type-check (1 files)
> **note** _(during AWAITING_REFACTOR)_: cycle 4: fixed 17 errors (machine 4, advance 3, render 10); the plan's cycle-4 header says 16 but its own per-file list sums to 17. 13 remain for cycle 5, matching its list (cli 7, adapters 2, tests 4).
> **note** _(during AWAITING_REFACTOR)_: cycle 4: the plan's 'annotate self.contract_row: sqlite3.Row' would need import sqlite3 in machine.py, which test_no_module_but_the_ledger_speaks_sql forbids; the close sweep caught it. The assert alone narrows the attribute, so there is no import and no explicit annotation.

### Cycle 3: the ledger, the ledger service and leases type-check  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `3b8d1dcdf` [refactor] refactor: make the ledger, its service and leases type-check (3 files)

### Cycle 2: a late baseline probe records its collection's failed files as a map  _(standard)_
- **Target:** `tddcli::tests/test_late_baseline.py::test_a_late_probe_records_its_failed_files_as_an_empty_map`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `891f2f1db` [red] test: a late probe records its failed files as an empty map (1 files)
  - `9cab6ca68` [green] fix: a late baseline probe records failed_files as a map, not a list (1 files)
> **note** _(during AWAITING_TEST)_: cycle 1: uv run mypy reports 53 errors in 13 files as planned, but checks 118 source files rather than the plan's 117 (one test file landed after planning; no new errors).

### Cycle 1: mypy is a dev dependency, configured to check src and tests  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `b97982e3c` [refactor] build: add mypy and its configuration as dev tooling (3 files)

## Time

- Wall clock: 18.6 min. Suite: 14.6 min (79%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 1 | 0.1 | 3.7 |
| AWAITING_IMPL | 2 | 1.9 | 56.2 |
| CLOSE_SWEEP | 7 | 12.7 | 109.0 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 2.2 | 1.8 | 1 |
| 2 | 2.5 | 1.9 | 3 |
| 3 | 2.9 | 1.8 | 1 |
| 4 | 6.4 | 5.5 | 3 |
| 5 | 2.5 | 1.8 | 1 |
| 6 | 2.2 | 1.8 | 1 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 4, the plan's sqlite3.Row annotation collided with the ledger-surface architecture test and cost one close sweep; plan got wrong: cycle 4's error count (16 vs 17 listed) and the 117-file count (118); harness friction: none, each advance ~110s of full-suite sweep.

