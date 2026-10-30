# Implementation Friction Log: tasks/issue-99-inherited-artifacts-unreadable-baseline.md

- Run: 12
- Executor: claude-opus-5-5 (source: claimed)
- Plan blob: `6dfdd37057a55e972558d47c9ffe465153ec3a0f` (declared)
- Started: 2026-10-30T14:53:02.660969+00:00  Ended: 2026-10-30T16:46:50.165202+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 7
- Delivered: 7   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 7: doctor notes a VIRTUAL_ENV that points outside every project root  _(standard)_
- **Target:** `tddcli::tests/test_doctor_blockers.py::test_doctor_notes_a_virtual_env_outside_every_project_root`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 4}
- **First run outcome:** failed (as expected)
- **Failures — invocation 354 (AWAITING_IMPL, tddcli):**
  - `tddcli::tests/test_split_doctor.py::test_a_split_runner_that_can_act_reports_its_checks_once_and_in_order` [call]: assert (['worktree r...ach", ...], 1) == (['worktree r...ach", ...], 1)
- **Commits:**
  - `653d83452` [red] test: doctor must note a foreign VIRTUAL_ENV (1 files)
  - `1db8151c0` [green] feat: doctor notes a VIRTUAL_ENV outside every project root (4 files)
> **note** _(during AWAITING_IMPL)_: cycle 7 GREEN broke tests/test_split_doctor.py::test_a_split_runner_that_can_act_reports_its_checks_once_and_in_order: it asserts doctor's exact non-project check list, and under 'uv run pytest' VIRTUAL_ENV points at the outer .venv, outside the test repo, so the new VIRTUAL_ENV notice appears. Fixed by delenv in that test (undeclared file), same remedy the plan prescribes for cycle 7's own 'unset' case.

### Cycle 6: an unreadable baseline probe is never cached for --reuse-baselines  _(standard)_
- **Target:** `tddcli::tests/test_baseline_integrity.py::test_an_unreadable_baseline_is_not_cached_for_reuse`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `389e79134` [red] test: a retry with --reuse-baselines must not reuse an unreadable probe (1 files)
  - `a0aadd784` [green] fix: never cache a baseline probe whose suite produced no readable report (2 files)

### Cycle 5: run start refuses a baseline whose suite produced no readable report  _(standard)_
- **Target:** `tddcli::tests/test_baseline_integrity.py::test_run_start_refuses_a_baseline_whose_suite_produced_no_report`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `3cf4cd8cf` [red] test: run start must refuse a baseline whose report could not be read (1 files)
  - `daa029bfb` [green] fix: run start refuses an unreadable baseline with reason baseline_unreadable (3 files)

### Cycle 4: pin: a project with no tests is not refused when its suite writes no report  _(pin)_
- **Target:** `tddcli::tests/test_baseline_integrity.py::test_a_project_with_no_tests_is_not_refused_when_its_suite_writes_no_report`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `KeyError: 'baselines'`
- **Commits:**
  - `bb4da08d0` [pin] test: pin — a project with no suite yet starts even when its runner writes no report (1 files)

### Cycle 3: run start records outside stale artifacts once, as artifact_stale_inherited  _(standard)_
- **Target:** `tddcli::tests/test_artifact_regeneration.py::test_run_start_reports_outside_stale_artifacts_once_as_inherited`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `8183e9638` [red] test: run start must report inherited stale artifacts once (1 files)
  - `191cb1031` [green] feat: run start records artifact_stale_inherited for artifacts outside the run (2 files)

### Cycle 2: a cycle close checks an artifact outside the run's projects only when the cycle touched its producer  _(standard)_
- **Target:** `tddcli::tests/test_artifact_regeneration.py::test_a_cycle_close_checks_an_outside_artifact_only_when_the_cycle_touched_its_producer`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `914da518c` [red] test: a cycle close must not check an artifact the run cannot reach (1 files)
  - `8a9fd72e6` [green] fix: scope per-cycle artifact checks to the run's reachable projects (4 files)

### Cycle 1: pin: run start still regenerates and commits an artifact whose producer the run cannot reach  _(pin)_
- **Target:** `tddcli::tests/test_artifact_regeneration.py::test_run_start_still_regenerates_an_artifact_outside_the_runs_projects`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert (False, 'M sv...e, 'client')]) == (True, '', [])`
- **Commits:**
  - `455874429` [pin] test: pin — run start regenerates an artifact outside the run's projects (1 files)

## Time

- Wall clock: 113.8 min. Suite: 88.1 min (77%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 5 | 1.3 | 15.8 |
| AWAITING_PIN | 2 | 0.4 | 11.6 |
| SENSITIVITY | 2 | 0.4 | 11.8 |
| AWAITING_IMPL | 12 | 63.7 | 318.5 |
| CLOSE_SWEEP | 2 | 22.3 | 669.2 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 11.9 | 8.4 | 3 |
| 2 | 10.2 | 8.6 | 3 |
| 3 | 19.8 | 18.3 | 3 |
| 4 | 16.2 | 14.7 | 3 |
| 5 | 23.1 | 18.5 | 3 |
| 6 | 13.2 | 1.7 | 3 |
| 7 | 19.5 | 17.9 | 5 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 7 — its doctor notice leaked into test_split_doctor's exact check-list assertion via the VIRTUAL_ENV uv run pytest exports; plan got wrong: cycle 7's files omitted tests/test_split_doctor.py, although decision text already knew uv sets VIRTUAL_ENV for the test process; harness friction: the full suite takes 15-18 min on this host, so run start and most advances outlived the 10-minute foreground cap and had to be polled in the background.

