# Implementation Friction Log: tasks/issue-98-ignored-paths-are-build-output.md

- Run: 11
- Executor: claude-opus-5-5 (source: claimed)
- Plan blob: `dea99fecc32aeeb928af365b2263842ab748fcdb` (declared)
- Started: 2026-10-30T14:33:44.647614+00:00  Ended: 2026-10-30T16:52:00.801618+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 4
- Delivered: 4   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 4: run close names the dirty paths git ignores once, as ignored_paths_dirty  _(standard)_
- **Target:** `tddcli::tests/test_ignored_paths.py::test_dirty_ignored_paths_are_reported_once_at_run_close`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `f2e19676d` [red] test: run close must name the dirty paths git ignores once (1 files)
  - `27d3a0f84` [green] feat: report dirty ignored paths once at run close as ignored_paths_dirty (5 files)
> **note** _(during AWAITING_REFACTOR)_: cycle 4 GREEN also reformatted the cycle-4 test (ruff format joined a split string) so the PR's format gate passes; no assertion changed.

### Cycle 3: a tracked path git ignores, left dirty, does not block run close  _(pin)_
- **Target:** `tddcli::tests/test_ignored_paths.py::test_a_tracked_ignored_path_left_dirty_does_not_block_run_close`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert 'blocked' == 'complete'`
- **Commits:**
  - `e8cfa8c72` [pin] test: pin — a dirty path git ignores does not block run close (1 files)

### Cycle 2: a tracked path git ignores, changed outside the cycle's project, fires no undeclared_file_touched  _(pin)_
- **Target:** `tddcli::tests/test_ignored_paths.py::test_a_tracked_ignored_path_outside_the_cycle_project_fires_no_undeclared_event`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert 1 == 0`
- **Commits:**
  - `9389f8178` [pin] test: pin — a path git ignores fires no undeclared_file_touched (1 files)

### Cycle 1: a tracked path git ignores, changed inside the cycle's project, is left out of the GREEN commit  _(standard)_
- **Target:** `tddcli::tests/test_ignored_paths.py::test_a_tracked_ignored_path_inside_the_cycle_project_is_left_out_of_the_green_commit`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `c6f01eb3f` [red] test: a tracked path git ignores must stay out of the GREEN commit (1 files)
  - `6b728fb8b` [green] fix: paths git's ignore rules match are build output, never staged or flagged (4 files)
> **note** _(during AWAITING_REFACTOR)_: cycle 1 GREEN advance exceeded the 600s tool timeout (full suite ~887s on this box) and was auto-backgrounded; polled it to completion in-turn, no concurrent advance was issued.

## Time

- Wall clock: 138.3 min. Suite: 68.4 min (49%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 2 | 0.3 | 10.2 |
| AWAITING_PIN | 2 | 1.6 | 47.0 |
| SENSITIVITY | 2 | 0.7 | 20.3 |
| AWAITING_IMPL | 4 | 27.3 | 409.6 |
| CLOSE_SWEEP | 2 | 38.5 | 1155.2 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 17.0 | 15.2 | 3 |
| 2 | 49.6 | 19.7 | 3 |
| 3 | 31.2 | 21.1 | 3 |
| 4 | 40.5 | 12.5 | 3 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 1 (the fix itself; plan's --no-index/check=False/no -v footguns were all accurate). plan got wrong: nothing observed; every expected failure matched verbatim. harness friction: the full tddcli suite took ~15 min per advance here, past the 600s tool timeout, so every suite-running advance had to be backgrounded and polled.

