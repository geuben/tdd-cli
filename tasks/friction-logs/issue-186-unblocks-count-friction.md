# Implementation Friction Log: tasks/issue-186-unblocks-count.md

- Run: 6
- Executor: claude-opus-5-5 (source: claimed)
- Plan blob: `748a4fa172a6ca985b289ba94872f92ff4589498` (declared)
- Started: 2026-10-30T12:34:26.895090+00:00  Ended: 2026-10-30T12:52:47.765821+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 8
- Delivered: 8   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 8: docs stop calling an unblock a human intervention  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `1dac91a9c` [refactor] docs: unblocks, not human interventions (5 files)

### Cycle 7: resume --unblock without --note asks for a note describing the unblock  _(standard)_
- **Target:** `tddcli::tests/test_unblocks_count.py::test_unblock_without_a_note_asks_for_one_describing_the_unblock`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `6e7cbe762` [red] test: --unblock without --note names the unblock (1 files)
  - `3abfdda63` [green] feat: --unblock asks for a note describing the unblock (1 files)

### Cycle 6: the friction log names an abandoned run's reason on an Abandoned: line  _(standard)_
- **Target:** `tddcli::tests/test_run_abandon.py::test_the_friction_log_names_the_abandonment_reason`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `d1a680d3a` [red] test: the friction log names why a run was abandoned (1 files)
  - `f075caae4` [green] feat: the friction log gains an Abandoned: header line (1 files)

### Cycle 5: an unblock whose note reads like an abandonment is still an unblock  _(standard)_
- **Target:** `tddcli::tests/test_unblocks_count.py::test_an_unblock_whose_note_reads_like_an_abandonment_is_still_counted`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `9bf476e7c` [red] test: an unblock noted like an abandonment still counts (1 files)
  - `931878828` [green] feat: match a pre-change abandon row on its time as well as its note (1 files)
  - `9927cf796` [refactor] refactor: tidy the abandon-row match (1 files)

### Cycle 4: a row a pre-change abandon wrote is not counted or listed as an unblock  _(standard)_
- **Target:** `tddcli::tests/test_unblocks_count.py::test_a_pre_change_abandon_row_is_not_an_unblock`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 4}
- **First run outcome:** failed (as expected)
- **Failures — invocation 214 (AWAITING_IMPL, tddcli):**
  - `tddcli::tests/test_ledger_surface.py::test_no_module_but_the_ledger_speaks_sql` [call]: AssertionError: assert {'render.py':...ort sqlite3']} == {}
- **Commits:**
  - `ce455c404` [red] test: a pre-change abandon row is not an unblock (1 files)
  - `dbe3c24d9` [green] feat: leave rows abandon wrote out of the unblocks (1 files)
> **note** _(during AWAITING_REFACTOR)_: cycle 4: the plan's _unblocks annotation (list[sqlite3.Row]) would import sqlite3 into render.py, which test_no_module_but_the_ledger_speaks_sql forbids; annotated as plain list instead

### Cycle 3: tdd run abandon writes no human_intervention row  _(standard)_
- **Target:** `tddcli::tests/test_run_abandon.py::test_abandoning_records_no_unblock`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `a1b3f0a50` [red] test: abandoning a run records no unblock (1 files)
  - `d5cd7ecf2` [green] feat: tdd run abandon stops writing a human_intervention row (1 files)

### Cycle 2: the friction log lists each unblock under Unblocks: N  _(standard)_
- **Target:** `tddcli::tests/test_unblocks_count.py::test_the_friction_log_lists_each_unblock_under_unblocks`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `1fff5214b` [red] test: the friction log lists unblocks (2 files)
  - `01f3d2df9` [green] feat: the friction log reports Unblocks: N (1 files)

### Cycle 1: tdd metrics reports unblocks, not human_interventions  _(standard)_
- **Target:** `tddcli::tests/test_unblocks_count.py::test_metrics_reports_unblocks_not_human_interventions`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `5c09b0136` [red] test: tdd metrics reports unblocks (1 files)
  - `dc5647128` [green] feat: tdd metrics reports unblocks instead of human_interventions (1 files)
  - `3474e9a73` [refactor] refactor: tidy the unblocks metric (1 files)

## Time

- Wall clock: 18.3 min. Suite: 16.4 min (89%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 7 | 0.2 | 1.3 |
| AWAITING_IMPL | 16 | 11.8 | 44.3 |
| CLOSE_SWEEP | 3 | 4.4 | 87.7 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 3.4 | 3.0 | 4 |
| 2 | 1.7 | 1.5 | 3 |
| 3 | 1.7 | 1.5 | 3 |
| 4 | 3.3 | 2.9 | 5 |
| 5 | 3.1 | 2.9 | 4 |
| 6 | 1.7 | 1.5 | 3 |
| 7 | 1.6 | 1.5 | 3 |
| 8 | 1.7 | 1.4 | 1 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 4, the plan's list[sqlite3.Row] annotation tripped test_no_module_but_the_ledger_speaks_sql; plan got wrong: that annotation, and cycle 1's RED left render unused so ruff F401 failed the first close sweep (import moved to cycle 2); harness friction: none beyond that

