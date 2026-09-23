# Implementation Friction Log: tasks/issue-148-red-target-only.md

- Run: 3
- Executor: claude-opus-5-5 (source: transcript)
- Plan blob: `b00698748adf69213963dd2b127215a3d254d032` (declared)
- Started: 2026-09-23T08:30:55.501859+00:00  Ended: 2026-09-23T09:09:53.987573+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 17
- Delivered: 17   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 17: an xctest run with a target, not target-only, has no -only-testing flag  _(standard)_
- **Target:** `tddcli::tests/test_xctest_adapter.py::test_a_run_with_a_target_but_not_target_only_has_no_only_testing`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `42be05167` [red] test: xctest GREEN runs the whole suite (1 files)
  - `8f5c5b712` [green] fix: xctest narrows to the target only when asked (2 files)
  - `0ba31dafc` [refactor] docs: PRD R9.1a-d, harness table and changelog for target-only RED (3 files)

### Cycle 16: a gradle run with a target, not target-only, has no --tests filter  _(standard)_
- **Target:** `tddcli::tests/test_gradle_adapter.py::test_a_run_with_a_target_but_not_target_only_has_no_tests_filter`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `8088747b3` [red] test: gradle GREEN runs the whole suite (1 files)
  - `cebd6f357` [green] fix: gradle narrows to the target only when asked (2 files)

### Cycle 15: a cargo run with a target, not target-only, runs the whole suite  _(standard)_
- **Target:** `tddcli::tests/test_cargo_adapter.py::test_a_run_with_a_target_but_not_target_only_runs_the_whole_suite`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `9ab8eea8e` [red] test: cargo GREEN runs the whole suite (1 files)
  - `ba7c30735` [green] fix: cargo narrows to the target only when asked (1 files)

### Cycle 14: GREEN on an exec project runs every script and is blocked by one failing elsewhere  _(standard)_
- **Target:** `tddcli::tests/test_suite_scope.py::test_green_on_an_exec_project_is_blocked_by_a_failing_script_elsewhere`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `e1522c07a` [red] test: exec GREEN sees a regression in another script (1 files)
  - `936e4ac4a` [green] fix: exec narrows to the target only when asked (2 files)
> **note** _(during AWAITING_REFACTOR)_: cycle 14: the first GREEN attempt returned fix_regression because my edit script aborted after changing exec_adapter but before applying the authorised one-line target_only=True change to test_targeting_runs_only_that_script (the call string appears twice in that file). Applied it with a scoped edit; no assertion changed.

### Cycle 13: a sensitivity check runs only the target  _(standard)_
- **Target:** `tddcli::tests/test_suite_scope.py::test_a_sensitivity_check_runs_only_the_target`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `a30b39bc9` [red] test: the sensitivity check does not observe other failures (1 files)
  - `4f66e4219` [green] feat: the sensitivity check runs only the target (1 files)

### Cycle 12: a pin is not blocked by a failing test outside the cycle  _(pin)_
- **Target:** `tddcli::tests/test_suite_scope.py::test_a_pin_is_not_blocked_by_a_failing_test_elsewhere`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `…rsion': 1, 'run': {'id': 1, 'plan': 'tasks/plan.md', 'cycle': 1, 'of': 1, ...}, 'result': {'other_failures': ['backend::tests/test_other.py::test_other']}, ...}`
- **Commits:**
  - `2d2ebad0f` [pin] test: pin that AWAITING_PIN runs only the target (1 files)

### Cycle 11: a RED invocation records others_observed = 0 and a GREEN one records 1  _(standard)_
- **Target:** `tddcli::tests/test_suite_scope.py::test_red_records_others_unobserved_and_green_records_them_observed`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `fb732b46f` [red] test: invocations record whether they observed other failures (1 files)
  - `c12d0065b` [green] feat: record others_observed on every invocation (1 files)
  - `6f0073ee3` [refactor] refactor: tidy the invocation row (1 files)

### Cycle 10: RED is not blocked by a failing test outside the cycle  _(standard)_
- **Target:** `tddcli::tests/test_suite_scope.py::test_red_is_not_blocked_by_a_failing_test_elsewhere`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `398fe3533` [red] test: RED ignores failures it did not observe (1 files)
  - `1b6854fe2` [green] feat: RED runs only the target (2 files)

### Cycle 9: a target-only vitest run uses the owning override's command and env, once  _(pin)_
- **Target:** `tddcli::tests/test_target_only_runs.py::test_a_target_only_vitest_run_uses_the_owning_override`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `assert [("npx vitest...rks$'", None)] == [("npx vitest...I_URL': 'x'})]`
- **Commits:**
  - `16ae3898f` [pin] test: pin that a target-only vitest run uses only the owning suite (1 files)

### Cycle 8: a target-only vitest run selects the file and an anchored, escaped full name  _(standard)_
- **Target:** `tddcli::tests/test_target_only_runs.py::test_a_target_only_vitest_run_selects_the_file_and_an_anchored_name`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `248c60c9e` [red] test: a target-only vitest run filters to one test (1 files)
  - `4a8dc89ee` [green] feat: vitest runs only the target when asked (1 files)

### Cycle 7: a target-only pytest run of a missing file is not_found, not a tooling error  _(pin)_
- **Target:** `tddcli::tests/test_target_only_runs.py::test_a_target_only_pytest_run_of_a_missing_file_is_not_found`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert ('not_found', 'mutant') == ('not_found', None)`
- **Commits:**
  - `8ba5a38c2` [pin] test: pin that a missing target file is not_found on a target-only run (1 files)

### Cycle 6: a target-only pytest run reports an uncollectable target file as not_collected  _(pin)_
- **Target:** `tddcli::tests/test_target_only_runs.py::test_a_target_only_pytest_run_reports_an_uncollectable_file_as_not_collected`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert 'not_found' == 'not_collected'`
- **Commits:**
  - `fe7e38a51` [pin] test: pin that a collection error in the target's file is still not_collected (1 files)

### Cycle 5: a target-only pytest run uses the owning override's command and env  _(pin)_
- **Target:** `tddcli::tests/test_target_only_runs.py::test_a_target_only_pytest_run_uses_the_owning_override`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert 'failed' == 'passed'`
- **Commits:**
  - `b19b17ae2` [pin] test: pin that a target-only pytest run keeps the override's env (1 files)

### Cycle 4: a target-only pytest run executes only the target, even with a path-scoped test_command  _(standard)_
- **Target:** `tddcli::tests/test_target_only_runs.py::test_a_target_only_pytest_run_executes_only_the_target`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `de9bd2b4b` [red] test: a target-only pytest run executes one node id (1 files)
  - `d35bf9b96` [green] feat: pytest runs only the target when asked (1 files)

### Cycle 3: an adopted target is evaluated in the same advance when the run only ran the declared target  _(standard)_
- **Target:** `tddcli::tests/test_suite_scope.py::test_an_adopted_target_is_evaluated_in_the_same_advance`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `976dbcc9a` [red] test: adoption on a target-only run is judged in one advance (1 files)
  - `b496b7bb9` [green] fix: re-run an adopted target the run did not execute (1 files)

### Cycle 2: the invocation table gains others_observed, fresh and migrated  _(standard)_
- **Target:** `tddcli::tests/test_release_surface.py::test_invocation_gains_others_observed_column`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `304119a9f` [red] test: invocation rows carry others_observed (1 files)
  - `2df41fbbc` [green] feat: schema 12 adds invocation.others_observed (1 files)

### Cycle 1: Adapter.run and Engine.run_projects accept an unused target_only keyword  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `eade583bc` [refactor] refactor: Adapter.run and run_projects take a target_only keyword (8 files)

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 3, keeping the adoption re-run a single helper so the resolved branch (unreachable from exec ids) was covered before cycle 10 made pytest RED target-only; the existing adoption tests all stayed green at cycle 10. Plan got wrong: nothing material; every probed expected failure matched. Harness friction: the worktree guard refused a heredoc append followed by other commands, and a multi-occurrence edit script aborted mid-way in cycle 14, costing one fix_regression round trip. The referee predates the change, so this run's own REDs still ran the whole suite.

