# Implementation Friction Log: tasks/issue-108-late-baseline-start-sha.md

- Run: 19
- Executor: claude-sonnet-4-6 (source: transcript)
- Plan blob: `68cb3ad93b1b0c0a6347890c5ceef710ec39b1b5` (declared)
- Started: 2026-09-07T20:53:42.191966+00:00  Ended: 2026-09-07T22:11:39.549238+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 14
- Delivered: 14   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 14: the friction log names late baselines in the run header and keeps them out of the start line  _(standard)_
- **Target:** `tddcli::tests/test_late_baseline.py::test_friction_log_names_late_baselines_in_the_run_header`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `3b8186adf` [red] test: friction log header names late baselines (1 files)
  - `8365d1438` [green] feat: friction log — Late baselines header line; start line excludes late_probe rows (1 files)
  - `569eb404f` [refactor] refactor: the friction log names late baselines in the run header and keeps them out of the start line (1 files)

### Cycle 13: the friction log lists amended-baseline verdicts under Human interventions  _(standard)_
- **Target:** `tddcli::tests/test_late_baseline.py::test_friction_log_lists_amended_baseline_verdicts_under_human_interventions`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `39eb71871` [red] test: friction log renders per-test accept/refuse verdicts (1 files)
  - `cff4fb662` [green] feat: friction log — amended baselines with per-test verdicts under Human interventions (1 files)

### Cycle 12: accept-failures refuses every candidate of an unobserved project and inserts no row  _(standard)_
- **Target:** `tddcli::tests/test_late_baseline.py::test_accept_failures_refuses_an_unobserved_project_and_inserts_no_row`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 2, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 2}
- **First run outcome:** failed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert (True, None) == (True, {'svc'..._svc_fails']})`
- **Commits:**
  - `dc4855051` [refactor] refactor: accept-failures refuses every candidate of an unobserved project and inserts no row (5 files)
  - `8a9bdcd3e` [refactor] refactor: accept-failures refuses every candidate of an unobserved project and inserts no row (1 files)
- **Event — red_first_violation:** ["tddcli::tests/test_late_baseline.py::test_accept_failures_refuses_an_unobserved_project_and_inserts_no_row"]
> **note** _(during SENSITIVITY_REQUIRED)_: Wrote test and production together; blast-radius rewrite of test_accept_failures_inserts_baseline_row needed the same production change (row-is-None branch now refuses instead of inserts), so both were done in one step.

### Cycle 11: baseline_amended records a per-test verdict and the start sha  _(standard)_
- **Target:** `tddcli::tests/test_late_baseline.py::test_baseline_amended_records_a_verdict_per_test`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `a922b57b2` [red] test: baseline_amended carries accepted/refused verdicts per test (1 files)
  - `81708f125` [green] feat: baseline_amended detail — {project: {start_sha, accepted, refused}} (1 files)

### Cycle 10: accept-failures still accepts a candidate that fails at the start sha  _(pin)_
- **Target:** `tddcli::tests/test_late_baseline.py::test_accept_failures_accepts_a_test_that_fails_at_the_start_sha`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert None == {'backend': ['backend::tests/test_flaky.py::test_flaky']}`
- **Commits:**
  - `d2c4b7abd` [pin] test: pin accept-failures still accepts a candidate that fails at the start sha (1 files)

### Cycle 9: accept-failures refuses a candidate that passes at the start sha  _(standard)_
- **Target:** `tddcli::tests/test_late_baseline.py::test_accept_failures_refuses_a_test_that_passes_at_the_start_sha`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 2, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert (['backend::t...smoke'], None) == ([], {'backen...test_smoke']})`
- **Commits:**
  - `86288f9b9` [refactor] refactor: accept-failures refuses a candidate that passes at the start sha (3 files)
- **Event — red_first_violation:** ["tddcli::tests/test_late_baseline.py::test_accept_failures_refuses_a_test_that_passes_at_the_start_sha"]
> **note** _(during SENSITIVITY_REQUIRED)_: Wrote test and implementation together: test_unblocking_can_accept and test_stale_reused were blast-radius rewrites that needed the production probe check to stop failing; the new target test and its implementation were written in the same step to fix all three simultaneously.

### Cycle 8: an unobservable start-sha probe blocks with no baseline row and no accept-failures advice  _(standard)_
- **Target:** `tddcli::tests/test_late_baseline.py::test_an_unobservable_late_probe_blocks_without_a_baseline_row`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 3, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `ab8fd7695` [red] test: an unobservable late probe blocks without a row (1 files)
  - `5aed03bc1` [green] fix: unobservable late probe → no_baseline_for_project with the reason; accept-failures no longer advised (2 files)
  - `82ec04def` [refactor] refactor: an unobservable start-sha probe blocks with no baseline row and no accept-failures advice (2 files)

### Cycle 7: a failure that passes at the start sha is a regression, even in a late-baselined project  _(pin)_
- **Target:** `tddcli::tests/test_late_baseline.py::test_a_failure_absent_at_the_start_sha_is_a_regression_in_a_late_baselined_project`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert 'blocked' == 'fix_regression'`
- **Commits:**
  - `ce7a297a3` [pin] test: pin a failure that passes at the start sha is a regression, even in a late-baselined project (1 files)

### Cycle 6: a failure that also fails at the start sha is baseline: the cycle closes  _(pin)_
- **Target:** `tddcli::tests/test_late_baseline.py::test_a_failure_present_at_the_start_sha_lets_the_cycle_close`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 3, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (**failed**)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert 'resolve_blocker' == 'complete'`
- **Commits:**
  - `e234e3a8a` [pin] test: pin a failure that also fails at the start sha is baseline: the cycle closes (1 files)

### Cycle 5: a close sweep that reaches an un-baselined project probes it at the start sha and records a late_probe baseline  _(standard)_
- **Target:** `tddcli::tests/test_late_baseline.py::test_close_sweep_late_probes_an_unbaselined_project_at_the_start_sha`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `cc0dfcf2c` [red] test: an un-baselined project is late-probed at the start sha (2 files)
  - `1b477456f` [green] feat: late baseline — probe an un-baselined project at run.start_sha, source late_probe (2 files)
- **Event — implementation_during_red:** ["src/tddcli/machine.py"]
> **note** _(during AWAITING_IMPL)_: machine.py production code was written in AWAITING_TEST phase alongside the stub for cycle 3; the late-probe implementation in Engine.probe_at_start_sha and sweep() was added during test writing as it is tightly coupled to the same commit. The test itself still fails RED confirming the code is not yet exercised.

### Cycle 4: temporary_worktree links the ignored directories directly under a project root  _(standard)_
- **Target:** `tddcli::tests/test_late_baseline.py::test_temporary_worktree_links_ignored_directories_under_the_project_root`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `6cc363151` [red] test: temporary_worktree links a project root's ignored directories (1 files)
  - `056a16ad1` [green] feat: temporary_worktree symlinks ignored top-level dirs (node_modules, .venv) from the live root (1 files)

### Cycle 3: gitutil.temporary_worktree checks out a sha in a throwaway worktree and removes it on exit  _(standard)_
- **Target:** `tddcli::tests/test_late_baseline.py::test_temporary_worktree_checks_out_the_sha_and_is_removed_on_exit`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `0f65d88a1` [red] test: temporary_worktree checks out a sha and cleans up (2 files)
  - `e5dc5ee0f` [green] feat: gitutil.temporary_worktree — detached worktree at a sha, removed on exit (1 files)

### Cycle 2: a v9 ledger is migrated in place to v10 and gains run.start_sha  _(standard)_
- **Target:** `tddcli::tests/test_release_surface.py::test_run_gains_start_sha_column`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `ef02f54c4` [red] test: v9 ledger gains run.start_sha on open (1 files)
  - `f79e5f64b` [green] feat: ledger schema v10 — run.start_sha migration (1 files)

### Cycle 1: run start records the start sha on the run row  _(standard)_
- **Target:** `tddcli::tests/test_late_baseline.py::test_run_start_records_the_start_sha_on_the_run_row`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `230195aa6` [red] test: run start records run.start_sha (1 files)
  - `8b95657bb` [green] feat: run.start_sha — HEAD at run start, recorded on the run row (3 files)
  - `3f2ad4998` [refactor] refactor: run start records the start sha on the run row (1 files)

## Executor narrative

_Claims from the executor, unverified by design._

> Hardest cycle: cycle 6 (close sweep closes when failure present at start sha) - the undeclared_file_touched gate blocked for 3 iterations because writing other/schema.json was classified as 'outside' until the schema artifact was marked generated=true in _drive_to_close. Plan got wrong: cycles 9, 12 required test+production in one step because blast-radius rewrites needed the production change to stop failing before the target test could be isolated. Harness friction: sensitivity_required after red_first_violation in standard cycles required an extra tdd note + sensitivity loop; the plan did not anticipate the coupling between blast-radius rewrites and the target test implementation.

