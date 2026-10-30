# Implementation Friction Log: tasks/issue-73-rerun-untouched-failures.md

- Run: 8
- Executor: claude-opus-5-5 (source: claimed)
- Plan blob: `4339fe9312e618c03a5b8918d28155cfe7449525` (declared)
- Started: 2026-10-30T13:29:02.900823+00:00  Ended: 2026-10-30T14:10:55.935470+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 16
- Delivered: 16   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 16: a rerun records no invocation row  _(pin)_
- **Target:** `tddcli::tests/test_flaky_reruns.py::test_a_rerun_records_no_invocation_row`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert [('AWAITING_T...ING_IMPL', 0)] == [('AWAITING_T...ING_IMPL', 1)]`
- **Commits:**
  - `c534b85a3` [pin] test: pin that a rerun records no invocation row (1 files)

### Cycle 15: tdd plan paths resolves an exec id to its script  _(pin)_
- **Target:** `tddcli::tests/test_plan_paths.py::test_an_exec_id_resolves_to_its_script`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert [] == [{'cycle': 1,...'gates', ...}]`
- **Commits:**
  - `24cba46a4` [pin] test: pin plan paths resolving an exec id to its script (1 files)

### Cycle 14: GREEN on an exec project goes through when an untouched script passes on rerun  _(standard)_
- **Target:** `tddcli::tests/test_flaky_reruns.py::test_green_on_an_exec_project_passes_when_an_untouched_script_passes_on_rerun`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `b472dc5ef` [red] test: an untouched exec script that passes on rerun must not block GREEN (1 files)
  - `f7cdc42d8` [green] fix: an exec id names its script's path (2 files)

### Cycle 13: a flaky_reruns that is not a non-negative integer is refused  _(standard)_
- **Target:** `tddcli::tests/test_config_and_staging.py::test_flaky_reruns_must_be_a_non_negative_integer`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `85c2d2587` [red] test: flaky_reruns must be a non-negative integer (1 files)
  - `cdd8279a4` [green] feat: refuse a flaky_reruns that is not a non-negative integer (3 files)

### Cycle 12: flaky_reruns = 0 replies exactly as before  _(standard)_
- **Target:** `tddcli::tests/test_flaky_reruns.py::test_flaky_reruns_zero_replies_exactly_as_before`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `e2468f2a8` [red] test: flaky_reruns = 0 must reply exactly as before (1 files)
  - `32d37e3ff` [green] feat: flaky_reruns = 0 turns reruns off (1 files)

### Cycle 11: flaky_reruns = 2 reruns until the test passes  _(standard)_
- **Target:** `tddcli::tests/test_flaky_reruns.py::test_flaky_reruns_two_reruns_until_the_test_passes`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `c0e578b08` [red] test: flaky_reruns = 2 must rerun until the test passes (1 files)
  - `3d823ebfc` [green] feat: per-project flaky_reruns sets how many reruns a failure gets (2 files)

### Cycle 10: each rerun emits a heartbeat  _(standard)_
- **Target:** `tddcli::tests/test_flaky_reruns.py::test_each_rerun_emits_a_heartbeat`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `ad26d973c` [red] test: each rerun must emit a heartbeat (1 files)
  - `30c5b1b40` [green] feat: a project_completed heartbeat with phase RERUN per rerun (1 files)

### Cycle 9: a failure whose file cannot be resolved is not rerun  _(standard)_
- **Target:** `tddcli::tests/test_flaky_reruns.py::test_a_failure_whose_file_cannot_be_resolved_is_not_rerun`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `a0fbebbe0` [red] test: a failure whose file cannot be resolved must not be rerun (1 files)
  - `b605bb42b` [green] feat: never rerun a failure whose file cannot be resolved (2 files)

### Cycle 8: a failure in a test the run added is not rerun  _(standard)_
- **Target:** `tddcli::tests/test_flaky_reruns.py::test_a_failure_in_a_test_the_run_added_is_not_rerun`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `1894b59d2` [red] test: a failure in a test the run added must not be rerun (1 files)
  - `0567a289f` [green] feat: rerun only tests collected when the run started (1 files)

### Cycle 7: a failure in any file the plan declares is not rerun  _(standard)_
- **Target:** `tddcli::tests/test_flaky_reruns.py::test_a_failure_in_any_file_the_plan_declares_is_not_rerun`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `b94efc1f3` [red] test: a failure in a file the plan declares must not be rerun (1 files)
  - `0864b5bdd` [green] feat: never rerun a failure in a file the plan declares (1 files)

### Cycle 6: extract plan_paths.locate, the one id-to-file resolver  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `b7fd0187f` [refactor] refactor: extract plan_paths.locate from resolve (1 files)

### Cycle 5: a close-sweep failure that fails again carries its rerun outcomes  _(standard)_
- **Target:** `tddcli::tests/test_flaky_reruns.py::test_a_close_sweep_failure_that_fails_again_carries_its_rerun_outcomes`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `9e9ef4486` [red] test: a close-sweep failure that fails again must carry its rerun outcomes (1 files)
  - `3c1f5fe66` [green] feat: fix_regression at the close sweep carries rerun_outcomes (1 files)

### Cycle 4: the close sweep closes when an untouched failure passes on rerun  _(standard)_
- **Target:** `tddcli::tests/test_flaky_reruns.py::test_the_close_sweep_closes_when_an_untouched_failure_passes_on_rerun`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `9540eb026` [red] test: the close sweep must not block on an untouched failure that passes on rerun (1 files)
  - `3b65addaa` [green] feat: rerun the close sweep's failures before it blocks (1 files)

### Cycle 3: a GREEN failure that fails again carries its rerun outcomes  _(standard)_
- **Target:** `tddcli::tests/test_flaky_reruns.py::test_a_green_failure_that_fails_again_carries_its_rerun_outcomes`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `13e0f886a` [red] test: a GREEN failure that fails again must carry its rerun outcomes (1 files)
  - `bcb5fac2d` [green] feat: fix_regression at GREEN carries rerun_outcomes (2 files)

### Cycle 2: a cleared failure is recorded as flaky_pre_existing with both outcomes  _(standard)_
- **Target:** `tddcli::tests/test_flaky_reruns.py::test_a_cleared_failure_is_recorded_as_flaky_pre_existing_with_both_outcomes`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `686b6b841` [red] test: a failure cleared by a rerun must be recorded as flaky_pre_existing (1 files)
  - `06b261aa6` [green] feat: record flaky_pre_existing with the suite and rerun outcomes (2 files)

### Cycle 1: GREEN goes through when an untouched failure passes on rerun  _(standard)_
- **Target:** `tddcli::tests/test_flaky_reruns.py::test_green_passes_when_an_untouched_failure_passes_on_rerun`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `aa5e6071b` [red] test: GREEN must not block on an untouched failure that passes on rerun (1 files)
  - `568efebe0` [green] feat: rerun a failure outside the cycle once before GREEN blocks on it (2 files)

## Time

- Wall clock: 41.9 min. Suite: 37.4 min (89%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 13 | 1.1 | 5.0 |
| AWAITING_PIN | 2 | 0.1 | 1.9 |
| SENSITIVITY | 2 | 0.1 | 2.2 |
| AWAITING_IMPL | 26 | 30.3 | 70.0 |
| CLOSE_SWEEP | 3 | 5.9 | 117.9 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 2.0 | 1.6 | 3 |
| 2 | 2.6 | 2.3 | 3 |
| 3 | 2.7 | 2.5 | 3 |
| 4 | 2.7 | 2.5 | 3 |
| 5 | 2.7 | 2.5 | 3 |
| 6 | 2.6 | 2.5 | 1 |
| 7 | 3.7 | 3.1 | 3 |
| 8 | 3.0 | 2.8 | 3 |
| 9 | 2.8 | 2.5 | 3 |
| 10 | 2.9 | 2.7 | 3 |
| 11 | 3.1 | 2.8 | 3 |
| 12 | 3.0 | 2.8 | 3 |
| 13 | 2.0 | 1.7 | 3 |
| 14 | 2.1 | 1.7 | 3 |
| 15 | 2.0 | 1.7 | 3 |
| 16 | 2.1 | 1.8 | 3 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 7 (declared-set eligibility: seven plan shapes, built plan-wide via plan_paths.locate and matched in both repo- and project-relative forms). plan got wrong: nothing material; every EXPECTED FAILURE matched. harness friction: running pytest directly in this shell fails even on the committed tree (split mode needs the referee), so tdd advance was the only test oracle.

