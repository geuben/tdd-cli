# Implementation Friction Log: tasks/issue-249-suite-time-by-project.md

- Run: 19
- Executor: claude-opus-5-5 (source: claimed)
- Plan blob: `a72247bbe3eab05de24935135604120d1b04efa9` (declared)
- Started: 2026-11-08T20:30:06.258866+00:00  Ended: 2026-11-08T20:43:17.480804+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 4
- Delivered: 4   Skipped: 0
- Never reached: none
- Unblocks: 0

### Cycle 4: the friction log's Time section tables suite time per project  _(standard)_
- **Target:** `tddcli::tests/test_time_report.py::test_the_friction_log_tables_suite_time_by_project`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `541a2b8f1` [red] test: the friction log must table suite time per project (1 files)
  - `5a503514b` [green] feat: the friction log tables suite time per project (1 files)
  - `fc7a56015` [refactor] docs: suite time per project in the PRD, README, split-runner guide and changelog (4 files)

### Cycle 3: time.by_project sums to the suite total, in seconds and in runs  _(pin)_
- **Target:** `tddcli::tests/test_time_report.py::test_metrics_by_project_sums_to_the_suite_total`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `assert (90.0, 4) == (198.0, 7)`
- **Commits:**
  - `97cb4a19d` [pin] test: pin that the projects' suite time and runs sum to the run's (1 files)

### Cycle 2: a run with no invocations has an empty time.by_project  _(pin)_
- **Target:** `tddcli::tests/test_time_report.py::test_metrics_by_project_is_empty_for_a_run_with_no_invocations`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert None == {}`
- **Commits:**
  - `7408e25f9` [pin] test: pin that a run with no suite runs has an empty time.by_project (1 files)

### Cycle 1: tdd metrics reports suite time per project, a close sweep credited to the project it ran  _(standard)_
- **Target:** `tddcli::tests/test_time_report.py::test_metrics_reports_suite_time_by_project`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `701330ce2` [red] test: tdd metrics must report suite time per project (1 files)
  - `b65f1b5fe` [green] feat: tdd metrics reports time.by_project (2 files)

## Time

- Wall clock: 13.2 min. Suite: 10.8 min (82%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 2 | 0.0 | 0.9 |
| AWAITING_PIN | 2 | 0.0 | 1.2 |
| SENSITIVITY | 2 | 0.1 | 1.6 |
| AWAITING_IMPL | 4 | 4.1 | 62.2 |
| CLOSE_SWEEP | 3 | 6.6 | 131.3 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 3.1 | 2.1 | 3 |
| 2 | 2.5 | 2.2 | 3 |
| 3 | 2.4 | 2.1 | 3 |
| 4 | 5.2 | 4.5 | 4 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: none was hard; cycle 1 carried all the implementation and the plan's hand-worked numbers matched exactly. plan got wrong: Execution omits 'tdd plan register', which run start demanded first. harness friction: cycle 1's GREEN advance printed multi-line output that broke my JSON parse, so I confirmed the phase with tdd status instead.

