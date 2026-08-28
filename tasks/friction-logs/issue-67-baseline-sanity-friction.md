# Implementation Friction Log: tasks/issue-67-baseline-sanity.md

- Run: 11
- Executor: claude-sonnet-4-6 (source: transcript)
- Plan blob: `cb355307f45d81108b17e8662ac12d2752b91443` (declared)
- Started: 2026-08-28T10:57:03.452563+00:00  Ended: 2026-08-28T14:19:51.435782+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 12
- Delivered: 12   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 12: a passing health_command lets the run proceed normally  _(pin)_
- **Target:** `tddcli::tests/test_baseline_sanity.py::test_reachable_services_proceed_normally`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `repo = PosixPath('/private/var/folders/zl/3010c_557g5_2rm9tyqsc03h0000gp/T/pytest-of-headless-coding/pytest-103/test_reachable_services_procee0/workspace')`
- **Commits:**
  - `d46fcd5fd` [pin] test: pin that a passing health_command does not block the run (1 files)

### Cycle 11: run start refuses when a project's health_command fails  _(standard)_
- **Target:** `tddcli::tests/test_baseline_sanity.py::test_unreachable_services_refuse_before_probing`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `ceeea32fd` [red] test: a failing health_command refuses with services_unreachable (1 files)
  - `adff5be36` [green] feat: probe health_command before baseline capture, refuse if down (1 files)

### Cycle 10: health_command parses onto a project from tdd.toml  _(standard)_
- **Target:** `tddcli::tests/test_config_and_staging.py::test_health_command_parses_onto_project`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `55fa89643` [red] test: a project's health_command parses onto Project (1 files)
  - `c3216db7e` [green] feat: Project.health_command parsed and validated from tdd.toml (1 files)

### Cycle 9: a first run with no prior baseline reports every failure as new  _(pin)_
- **Target:** `tddcli::tests/test_baseline_sanity.py::test_first_run_reports_all_standing_failures_new`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `repo = PosixPath('/private/var/folders/zl/3010c_557g5_2rm9tyqsc03h0000gp/T/pytest-of-headless-coding/pytest-93/test_first_run_reports_all_sta0/workspace')`
- **Commits:**
  - `27d1583ac` [pin] test: pin the no-prior-baseline delta path (1 files)

### Cycle 8: run start emits a standing-failure delta against the previous run  _(standard)_
- **Target:** `tddcli::tests/test_baseline_sanity.py::test_non_empty_baseline_emits_standing_delta`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `8a3ff0c44` [red] test: a non-empty baseline logs new-vs-inherited standing failures (1 files)
  - `75f883b53` [green] feat: emit baseline_standing_delta partitioning new vs inherited (1 files)

### Cycle 7: Ledger.previous_baseline returns the prior run's failing set for a project  _(standard)_
- **Target:** `tddcli::tests/test_snapshot_and_identity.py::test_previous_baseline_returns_prior_runs_failing_set`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `8fe7f4133` [red] test: previous_baseline reads the last earlier run's failing set (1 files)
  - `719069da2` [green] feat: Ledger.previous_baseline joins baseline to run by worktree (1 files)

### Cycle 6: a healthy large baseline is recorded without refusal or event  _(pin)_
- **Target:** `tddcli::tests/test_baseline_sanity.py::test_a_healthy_baseline_is_recorded_untouched`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `repo = PosixPath('/private/var/folders/zl/3010c_557g5_2rm9tyqsc03h0000gp/T/pytest-of-headless-coding/pytest-84/test_a_healthy_baseline_is_rec0/workspace')`
- **Commits:**
  - `351438063` [pin] test: pin that a healthy baseline is untouched by the gate (1 files)

### Cycle 5: an accepted implausible baseline records an audit event  _(standard)_
- **Target:** `tddcli::tests/test_baseline_sanity.py::test_accepted_implausible_baseline_records_an_event`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `91e63d113` [red] test: an accepted implausible baseline logs baseline_accepted (1 files)
  - `e7a8cf3aa` [green] feat: emit a baseline_accepted integrity event on override (1 files)

### Cycle 4: per-project baseline_max_failure_ratio overrides the default  _(standard)_
- **Target:** `tddcli::tests/test_baseline_sanity.py::test_project_ratio_config_raises_the_threshold`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `b7cd4b8b9` [red] test: a project's baseline_max_failure_ratio suppresses the refusal (1 files)
  - `bfd482767` [green] feat: honour per-project baseline_max_failure_ratio from tdd.toml (2 files)

### Cycle 3: a small all-red suite is exempt from the gate  _(pin)_
- **Target:** `tddcli::tests/test_baseline_sanity.py::test_a_small_all_red_suite_is_not_refused`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `repo = PosixPath('/private/var/folders/zl/3010c_557g5_2rm9tyqsc03h0000gp/T/pytest-of-headless-coding/pytest-75/test_a_small_all_red_suite_is_0/workspace')`
- **Commits:**
  - `4cdf24d91` [pin] test: pin the small-suite exemption from the baseline gate (1 files)

### Cycle 2: --accept-baseline overrides the implausibility refusal  _(standard)_
- **Target:** `tddcli::tests/test_baseline_sanity.py::test_accept_baseline_overrides_the_refusal`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `a1b1fc419` [red] test: --accept-baseline lets an implausible baseline through (1 files)
  - `23ddac87c` [green] feat: --accept-baseline bypasses the implausibility gate (1 files)

### Cycle 1: a large, mostly-red baseline is refused as implausible  _(standard)_
- **Target:** `tddcli::tests/test_baseline_sanity.py::test_a_mostly_red_baseline_is_refused`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `ac807aa6c` [red] test: run start refuses an implausible mostly-red baseline (1 files)
  - `c003f697c` [green] feat: refuse a baseline whose failing ratio exceeds the threshold (1 files)

