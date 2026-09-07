# Implementation Friction Log: tasks/issue-107-regenerate-hook-failure.md

- Run: 18
- Executor: claude-sonnet-4-6 (source: transcript)
- Plan blob: `98689a287c1e96004d3847f8d88e84d3a3e0ba2c` (declared)
- Started: 2026-09-07T16:59:31.139070+00:00  Ended: 2026-09-07T17:22:32.825446+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 8
- Delivered: 8   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 8: the friction log lists the hook failure under its cycle  _(pin)_
- **Target:** `tddcli::tests/test_artifact_regeneration.py::test_friction_log_lists_failed_regeneration_under_its_cycle`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `…ecutor (source: declared)\n- Plan blob... _(refactor)_\n- **Target:** none\n- **Projects:** `backend`\n- **Suite runs by phase:** none\n- **Commits:** none\n\n'`
- **Commits:**
  - `5b0415909` [pin] test: pin the friction log lists the hook failure under its cycle (1 files)

### Cycle 7: run start refuses when a regenerate hook fails before cycle 1  _(standard)_
- **Target:** `tddcli::tests/test_artifact_regeneration.py::test_failed_regenerate_hook_at_run_start_refuses`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `bc22b16de` [red] test: run start refuses on a failed regenerate hook (1 files)
  - `8d2d553b7` [green] fix: run start refuses when an artifact cannot be regenerated (2 files)

### Cycle 6: a stale artifact whose regenerate hook fails reports the hook failure, not bare stale_artifact  _(standard)_
- **Target:** `tddcli::tests/test_artifact_regeneration.py::test_failed_regenerate_after_stale_check_reports_hook_failure_not_stale`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `dbaba458c` [red] test: stale-then-failed regenerate reports artifact_regenerate_failed only (1 files)
  - `982fbebbc` [green] fix: route the check-then-regenerate path through the hook-failure outcome (1 files)

### Cycle 5: once the hook recovers, the next advance closes the cycle normally  _(pin)_
- **Target:** `tddcli::tests/test_artifact_regeneration.py::test_cycle_closes_once_the_regenerate_hook_recovers`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `…: {'ok': True, 'envelope_version': 1, 'run': {'id': 1, 'plan': 'tasks/plan.md', 'cycle': 1, 'of': 1, ...}, 'result': {'commit': None, 'regenerated': None}, ...}`
- **Commits:**
  - `35afc2d72` [pin] test: pin once the hook recovers, the next advance closes the cycle normally (1 files)

### Cycle 4: a failed regenerate hook at cycle close replies fix_regression, not complete  _(standard)_
- **Target:** `tddcli::tests/test_artifact_regeneration.py::test_failed_regenerate_hook_at_close_replies_fix_regression`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `b98a4298b` [red] test: failed regenerate hook at close replies fix_regression (1 files)
  - `6c4fbfbb4` [green] fix: a failed regenerate hook is a close-sweep failure, not a fresh artifact (3 files)

### Cycle 3: a failed regenerate hook emits artifact_regenerate_failed carrying the exit code and stderr  _(standard)_
- **Target:** `tddcli::tests/test_artifact_regeneration.py::test_failed_regenerate_hook_emits_artifact_regenerate_failed_event`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `5b0027247` [red] test: failed regenerate hook emits artifact_regenerate_failed (1 files)
  - `90348f3e1` [green] feat: artifact_regenerate_failed integrity event with code and stderr (1 files)

### Cycle 2: a v8 ledger is migrated in place to v9 and gains the regenerate_failed column  _(standard)_
- **Target:** `tddcli::tests/test_release_surface.py::test_artifact_check_gains_regenerate_failed_column`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `3d16fa357` [red] test: v8 ledger gains artifact_check.regenerate_failed on open (1 files)
  - `fb93e98a6` [green] feat: ledger schema v9 — artifact_check.regenerate_failed migration (2 files)
> **note** _(during AWAITING_REFACTOR)_: regression in test_v7_ledger_is_upgraded_in_place_to_v8: it hardcoded schema_version '8' but bumping SCHEMA_VERSION to 9 means v7 ledgers now migrate to v9; fixed assertion to use str(SCHEMA_VERSION)

### Cycle 1: a regenerate hook that exits non-zero marks its artifact_check row regenerate_failed=1  _(standard)_
- **Target:** `tddcli::tests/test_artifact_regeneration.py::test_failed_regenerate_hook_marks_artifact_check_regenerate_failed`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `0d4110850` [red] test: a failed regenerate hook is recorded on artifact_check (1 files)
  - `82d2e91cf` [green] fix: capture the regenerate hook's exit code; record regenerate_failed (2 files)

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: cycle 2 (migration) caused a regression in test_v7_ledger_is_upgraded_in_place_to_v8 which hardcoded the schema version as '8' — bumping to v9 made the assertion wrong, fixed by importing SCHEMA_VERSION. Plan got right: the check-then-regenerate path (cycle 6) was accurately scoped as a separate fix. Harness friction: none.

