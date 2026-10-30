# Implementation Friction Log: tasks/issue-105-failure-details.md

- Run: 1
- Executor: claude-opus-5-5 (source: claimed)
- Plan blob: `c149c5ef5415ca4dbf1a0e74858d9c9d9f416553` (declared)
- Started: 2026-10-29T23:26:20.115408+00:00  Ended: 2026-10-30T00:22:36.151892+00:00  Outcome: complete
- Baseline failures at start: tddcli=60

## Plan fidelity

- Declared cycles: 15
- Delivered: 15   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 15: a split-mode guest shows its own invocation's failures through the ledger service  _(pin)_
- **Target:** `tddcli::tests/test_ledger_service.py::test_a_guest_shows_its_own_invocations_failures`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `KeyError: 'failures'`
- **Commits:**
  - `3ab30e744` [pin] test: pin that a guest shows its invocation's failures over the socket (1 files)

### Cycle 14: tdd invocation show prints an invocation's stored failure details  _(standard)_
- **Target:** `tddcli::tests/test_failure_details.py::test_invocation_show_prints_the_stored_failure_details`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `163c979c9` [red] test: tdd invocation show prints the stored failure details (1 files)
  - `c714c1ccc` [green] feat: tdd invocation show prints an invocation's failure details (1 files)
  - `f2af433f4` [refactor] docs: tdd invocation show and persisted failure details (4 files)

### Cycle 13: tdd invocation show refuses an id the ledger does not hold  _(standard)_
- **Target:** `tddcli::tests/test_failure_details.py::test_showing_an_unknown_invocation_is_refused`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `f4636645e` [red] test: tdd invocation show refuses an unknown id (2 files)
  - `2155a6cd3` [green] feat: tdd invocation show refuses an unknown invocation (1 files)

### Cycle 12: the friction log lists each invocation's failures with phase and message  _(standard)_
- **Target:** `tddcli::tests/test_failure_details.py::test_the_friction_log_lists_each_invocations_failures`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `cb21af583` [red] test: the friction log says why each failure failed (1 files)
  - `dc2612119` [green] feat: the friction log lists each invocation's failure details (1 files)
  - `4c3ec370c` [refactor] refactor: tidy the friction log's failure block (2 files)

### Cycle 11: exec reports each failing script with its last output line  _(standard)_
- **Target:** `tddcli::tests/test_failure_details.py::test_exec_reports_each_failing_script_with_its_last_output_line`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `c565bbc46` [red] test: exec reports why each script failed (1 files)
  - `2f63ba8e4` [green] feat: exec verdicts carry each failure's details (1 files)

### Cycle 10: xctest reports each failure with its error line  _(standard)_
- **Target:** `tddcli::tests/test_failure_details.py::test_xctest_reports_each_failure_with_its_error_line`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `9e8680d79` [red] test: xctest reports why each test failed (1 files)
  - `97a84ab37` [green] feat: xctest verdicts carry each failure's details (1 files)

### Cycle 9: gradle reports each failure with its failure message  _(standard)_
- **Target:** `tddcli::tests/test_failure_details.py::test_gradle_reports_each_failure_with_its_failure_message`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `2af54bfe5` [red] test: gradle reports why each test failed (1 files)
  - `8af3b5c33` [green] feat: gradle verdicts carry each failure's details (1 files)

### Cycle 8: cargo reports each failure with its panic line  _(standard)_
- **Target:** `tddcli::tests/test_failure_details.py::test_cargo_reports_each_failure_with_its_panic_line`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `a367e4807` [red] test: cargo reports why each test failed (1 files)
  - `7e239c9b2` [green] feat: cargo verdicts carry each failure's details (1 files)

### Cycle 7: vitest reports each failure with its first message line  _(standard)_
- **Target:** `tddcli::tests/test_failure_details.py::test_vitest_reports_each_failure_with_its_first_message_line`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `2b0c8f26d` [red] test: vitest reports why each test failed (1 files)
  - `83baaf993` [green] feat: vitest verdicts carry each failure's details (1 files)

### Cycle 6: a close sweep records why its failures failed  _(standard)_
- **Target:** `tddcli::tests/test_failure_details.py::test_a_close_sweep_records_why_its_failures_failed`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `166b49512` [red] test: a close sweep records its failures' details (1 files)
  - `6982def7c` [green] feat: close sweeps persist the details of their failures (1 files)
  - `4d2ed560d` [refactor] refactor: tidy close-sweep failure recording (1 files)

### Cycle 5: a pytest failure detail is clipped and keeps the error at its tail  _(standard)_
- **Target:** `tddcli::tests/test_failure_clipping.py::test_pytest_failure_detail_keeps_the_error_at_the_tail`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `ca0e6daef` [red] test: a pytest failure detail keeps its tail (1 files)
  - `16d46cf3c` [green] feat: clip pytest failure details like target failures (1 files)

### Cycle 4: a GREEN run records why its other failures failed, and not its baseline's  _(standard)_
- **Target:** `tddcli::tests/test_failure_details.py::test_a_green_run_records_why_its_other_failures_failed`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `bea13861e` [red] test: a GREEN run records its other failures' details (1 files)
  - `0dce926cd` [green] feat: phase runs persist the details of their other failures (1 files)

### Cycle 3: pytest reports each failure with the phase that failed, its message and its longrepr  _(standard)_
- **Target:** `tddcli::tests/test_failure_details.py::test_pytest_reports_each_failure_with_the_phase_that_failed`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `47037be48` [red] test: pytest reports why each test failed (2 files)
  - `a1098eef1` [green] feat: pytest verdicts carry each failure's phase, message and longrepr (1 files)

### Cycle 2: a guest naming another source's invocation is refused  _(standard)_
- **Target:** `tddcli::tests/test_ledger_service.py::test_a_guest_naming_another_sources_invocation_is_refused`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 3, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `246e39520` [red] test: a guest cannot read another source's invocation (1 files)
  - `b21f1227c` [green] feat: the ledger service owns invocations by their run's source (4 files)
  - `6eeb270a2` [refactor] refactor: tidy invocation ownership (2 files)
> **note** _(during AWAITING_REFACTOR)_: cycle 2: the referee's tdd-runner runs suites under umask 0002, so every fixture-written runner/service config failed the trust check (the 60 baseline failures; cycle 2's RED was a fixture ServiceConfigError, not the planned method_not_allowed assertion). Added an autouse umask-022 fixture to tests/conftest.py (undeclared); reproduced: umask 0002 -> errors, with the fixture -> 27/27 pass in test_ledger_service+admin.

### Cycle 1: an invocation keeps the failure details it was recorded with  _(standard)_
- **Target:** `tddcli::tests/test_failure_details.py::test_an_invocation_keeps_the_failure_details_it_was_recorded_with`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `722832f45` [red] test: an invocation keeps its failure details (2 files)
  - `4d943a817` [green] feat: record failure details with each invocation (1 files)
  - `ec993f81d` [refactor] refactor: tidy the failure_detail table (1 files)
> **note** _(during AWAITING_TEST)_: baseline tddcli=60 (plan expected 0): suites run as the split-mode tdd-runner user per /etc/tdd-cli/runner.toml; the same suite run as the agent user passes 722/722. Environment noise, subtracted by the baseline.

## Time

- Wall clock: 56.3 min. Suite: 40.4 min (72%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 14 | 0.4 | 1.6 |
| AWAITING_PIN | 1 | 0.1 | 5.5 |
| SENSITIVITY | 1 | 0.1 | 5.4 |
| AWAITING_IMPL | 29 | 28.6 | 59.3 |
| CLOSE_SWEEP | 6 | 11.1 | 111.5 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 8.1 | 4.3 | 4 |
| 2 | 7.1 | 4.3 | 5 |
| 3 | 3.0 | 2.3 | 3 |
| 4 | 3.1 | 2.3 | 3 |
| 5 | 2.6 | 2.3 | 3 |
| 6 | 5.4 | 4.5 | 4 |
| 7 | 2.8 | 2.2 | 3 |
| 8 | 2.8 | 2.2 | 3 |
| 9 | 2.8 | 2.3 | 3 |
| 10 | 2.7 | 2.1 | 3 |
| 11 | 3.0 | 2.0 | 3 |
| 12 | 4.5 | 3.3 | 4 |
| 13 | 2.1 | 1.4 | 3 |
| 14 | 3.8 | 3.0 | 4 |
| 15 | 2.5 | 1.7 | 3 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 2, not for the code but the referee: suites run as tdd-runner under umask 0002, so every test writing a runner/service config hit the group-writable trust check (60 baseline failures, including cycle 2's and 15's file). Fixed with an autouse umask fixture in tests/conftest.py (undeclared). plan got wrong: baseline 0 expected, 60 observed for the umask reason; otherwise every probed value matched. harness friction: cycles 7-11 extracted the per-adapter _failure_detail helper during GREEN rather than REFACTOR, since the target path and the details share one computation.

