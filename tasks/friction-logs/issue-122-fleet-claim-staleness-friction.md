# Implementation Friction Log: tasks/issue-122-fleet-claim-staleness.md

- Run: 22
- Executor: claude-sonnet-4-6 (source: transcript)
- Plan blob: `bc254aba6031dd52e4e73ff20513ff9af5c424b1` (declared)
- Started: 2026-09-16T10:47:03.932516+00:00  Ended: 2026-09-16T11:06:35.571776+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 8
- Delivered: 8   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 8: document fleet's claim liveness and advance-claim rows  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `7cf5a703d` [refactor] docs: fleet reports claim liveness and advance claims (2 files)

### Cycle 7: an advance claim alone is not 'no active runs'  _(standard)_
- **Target:** `tddcli::tests/test_fleet.py::test_an_advance_claim_alone_is_not_no_active_runs`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (**passed**)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert 'no active runs' not in 'no active r...of 8 cores\n'`
- **Commits:**
  - `69367f4d5` [refactor] refactor: an advance claim alone is not 'no active runs' (1 files)
- **Event — red_first_violation:** ["tddcli::tests/test_fleet.py::test_an_advance_claim_alone_is_not_no_active_runs"]
- **plan_defect:** cycle_7_test_passed_on_arrival_because_cycle_6_green_required_the_advancing_condition_fix_to_make_its_own_test_pass
> **note** _(during SENSITIVITY_REQUIRED)_: cycle 7 test passes on arrival because cycle 6's GREEN included the 'not summary[advancing]' condition fix — the plan anticipated this scenario (see 'if this block passes without cycle 7's change, the plan is wrong') and specified annotating plan_defect after sensitivity check.

### Cycle 6: the human fleet output prints a line per advance claim and marks a dead holder  _(standard)_
- **Target:** `tddcli::tests/test_fleet.py::test_render_lists_advance_claims_and_marks_a_dead_holder`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `629b22f4b` [red] test: the rendered fleet output names a dead advance holder (1 files)
  - `827da11e6` [green] feat: tdd fleet renders advance claims (1 files)
> **note** _(during AWAITING_IMPL)_: cycle 6 GREEN required the 'no active runs' condition fix (not summary['advancing']) to make the test pass — the condition could not be isolated to cycle 7 because the cycle 6 test asserts the exact rendered block without 'no active runs'. Per plan: cycle 7 test expected to pass on arrival; will annotate plan_defect then.

### Cycle 5: fleet lists in-flight advance claims with their holder's liveness  _(standard)_
- **Target:** `tddcli::tests/test_fleet.py::test_fleet_lists_advance_claims_with_holder_liveness`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `d3be4bcc9` [red] test: fleet --json lists advance claims (1 files)
  - `7c3d1746e` [green] feat: fleet reports in-flight advance claims (1 files)

### Cycle 4: pin: fleet and progress agree on a dead collector — one staleness rule, two commands  _(pin)_
- **Target:** `tddcli::tests/test_fleet.py::test_fleet_and_progress_agree_on_a_dead_collector`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `assert (False, 54546) == (True, 54546)`
- **Commits:**
  - `49dd19332` [pin] test: pin pin: fleet and progress agree on a dead collector — one staleness rule, two commands (1 files)

### Cycle 3: the human fleet line marks a dead collector and leaves a live one alone  _(standard)_
- **Target:** `tddcli::tests/test_fleet.py::test_render_marks_a_dead_collector_and_leaves_a_live_one_alone`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `e279469f4` [red] test: the rendered fleet line names a dead collector (1 files)
  - `70d67cbfd` [green] feat: tdd fleet names a dead baseline collector (1 files)

### Cycle 2: fleet claim rows report the collector's liveness and owner pid  _(standard)_
- **Target:** `tddcli::tests/test_fleet.py::test_fleet_claim_rows_report_collector_liveness`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `35474ee57` [red] test: fleet claim rows carry stale and pid (1 files)
  - `53eba2f27` [green] feat: fleet reports baseline collector liveness (2 files)

### Cycle 1: extract the claim staleness rule to a module-level function in ledger.py  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `43e6f97c3` [refactor] refactor: extract claim_is_stale as a module-level function (1 files)

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: cycle 6 — the plan said 'add the advancing loop and nothing else; cycle 7 owns the condition fix', but the cycle 6 test asserts the exact rendered block without 'no active runs', which required the condition fix to pass; this is a plan defect (annotated on cycle 7). Environment friction: uv 0.5.9 on PATH could not parse the newer uv.lock (missing version field); had to run uv self update before doctor could pass. The worktree venv also needed pip installed via ensurepip before packages could be installed. Plan got wrong: the condition fix had to be bundled into cycle 6 GREEN rather than isolated in cycle 7 as intended.

