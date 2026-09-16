# Implementation Friction Log: tasks/issue-129-gates-before-suite.md

- Run: 23
- Executor: claude-sonnet-4-6 (source: transcript)
- Plan blob: `dcd5c3c5e9a8a9a72895aa05e5fa121bf35df14b` (declared)
- Started: 2026-09-16T22:58:33.075527+00:00  Ended: 2026-09-16T23:47:27.559360+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 13
- Delivered: 13   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 13: amend the PRD and changelog for the new close-sweep order and schema v11  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `5e32917c7` [refactor] docs: close-sweep gates run before the suite (R9.2, R9.11, schema v11) (2 files)

### Cycle 12: a skipped gate still records a gate_result row, marked skipped  _(standard)_
- **Target:** `tddcli::tests/test_close_sweep_gates.py::test_a_skipped_gate_records_a_skipped_row`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `21cb7b835` [red] test: a skipped gate records a skipped gate_result row (1 files)
  - `8ed68e45e` [green] feat: record the skipped gate_result row (1 files)

### Cycle 11: a gate that passed at this tree hash is not re-executed  _(standard)_
- **Target:** `tddcli::tests/test_close_sweep_gates.py::test_a_passing_gate_is_not_reexecuted_at_an_unchanged_tree`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `100db04c4` [red] test: a passing gate is not re-executed at an unchanged tree (1 files)
  - `f33f0a4da` [green] feat: skip a gate whose tree hash is unchanged since it passed (1 files)

### Cycle 10: gate_result carries the tree hash a gate ran at, and whether it was skipped  _(standard)_
- **Target:** `tddcli::tests/test_release_surface.py::test_gate_result_gains_tree_hash_and_skipped_columns`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `dcf437d7a` [red] test: gate_result carries tree_hash and skipped (1 files)
  - `ceb3304fd` [green] feat: schema v11 adds gate_result.tree_hash and gate_result.skipped (1 files)

### Cycle 9: a gate is re-run when its project tree changed  _(pin)_
- **Target:** `tddcli::tests/test_close_sweep_gates.py::test_a_gate_is_rerun_when_the_tree_changed`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert 1 == 2`
- **Commits:**
  - `a2565c217` [pin] test: pin that a changed tree re-runs the gate (1 files)

### Cycle 8: a gate that failed is re-run on the next close at the same tree  _(pin)_
- **Target:** `tddcli::tests/test_close_sweep_gates.py::test_a_failed_gate_is_rerun_at_the_same_tree`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert 1 == 2`
- **Commits:**
  - `6d6a31e74` [pin] test: pin that a failed gate is re-run at the same tree (1 files)

### Cycle 7: the gate-failure reply no longer claims the sweep is green  _(standard)_
- **Target:** `tddcli::tests/test_close_sweep_gates.py::test_the_gate_failure_reply_does_not_claim_the_sweep_is_green`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `ab4ccf5a8` [red] test: the gate-failure reply does not claim the sweep is green (1 files)
  - `b67007dab` [green] feat: reword the gate-failure reply for the short-circuit (1 files)

### Cycle 6: every sweep project's gates run before any project's suite  _(standard)_
- **Target:** `tddcli::tests/test_close_sweep_gates.py::test_a_later_projects_failing_gate_runs_no_earlier_suite`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (**passed**)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `assert 1 == 0`
- **Commits:**
  - `488d5e25f` [refactor] refactor: tidy sweep passes (1 files)
- **Event — red_first_violation:** ["tddcli::tests/test_close_sweep_gates.py::test_a_later_projects_failing_gate_runs_no_earlier_suite"]
> **note** _(during SENSITIVITY_REQUIRED)_: cycle 6 pre-passes: cycle 5 already restructured sweep into two loops — gate pass over all projects then suite pass — so the cross-project gate-before-suite invariant was already satisfied

### Cycle 5: a failing gate short-circuits the sweep before any suite runs  _(standard)_
- **Target:** `tddcli::tests/test_close_sweep_gates.py::test_a_failing_gate_runs_no_suite`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `90528954a` [red] test: a failing close-sweep gate runs no suite (1 files)
  - `4259b5620` [green] feat: close-sweep gates run before the suite and short-circuit (1 files)

### Cycle 4: a failing lint means typecheck is never run  _(standard)_
- **Target:** `tddcli::tests/test_close_sweep_gates.py::test_a_failing_lint_stops_the_gate_pass_before_typecheck`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `8e3bf59e2` [red] test: a failing lint stops the gate pass before typecheck (1 files)
  - `1d99bf2fa` [green] feat: the close-sweep gate pass stops at the first failing gate (1 files)

### Cycle 3: _gate stops at the first failing command  _(standard)_
- **Target:** `tddcli::tests/test_close_sweep_gates.py::test_gate_stops_at_the_first_failing_command`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `9bb9f4072` [red] test: _gate stops at the first failing command (1 files)
  - `fa8ce2aee` [green] feat: _gate returns at the first failing command (1 files)

### Cycle 2: a gate that ran records a gate_result row  _(pin)_
- **Target:** `tddcli::tests/test_close_sweep_gates.py::test_a_failing_lint_records_its_gate_result_row`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `assert False`
- **Commits:**
  - `26d261850` [pin] test: pin the gate_result row a failing lint writes (1 files)

### Cycle 1: a failing gate at close still replies fix_regression with that gate's entry  _(pin)_
- **Target:** `tddcli::tests/test_close_sweep_gates.py::test_failing_lint_replies_fix_regression_with_the_lint_gate`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert ('fix_regression', []) == ('fix_regress...nd', 'lint')])`
- **Commits:**
  - `0453ad68f` [pin] test: pin the fix_regression reply a failing close-sweep gate produces (1 files)

## Executor narrative

_Claims from the executor, unverified by design._

> Hardest cycle: 4 (gate_fn() lazy-call bug — tuple eager-evaluated both gates before the loop; fixed by using callables). Plan inaccuracies: cycle 6 pre-passed because cycle 5's two-pass restructure already satisfied the cross-project assertion; sensitivity check confirmed (mutation: swap back to suite-first order collapsed the test). Cycle 12 was correctly RED — cycle 11's continue-without-insert was plan-correct; the insert was added in cycle 12. Harness friction: context compacted mid-run (between cycles 12 and 13); resumed cleanly from summary.

