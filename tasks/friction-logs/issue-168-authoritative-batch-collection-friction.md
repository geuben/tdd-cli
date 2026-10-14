# Implementation Friction Log: tasks/issue-168-authoritative-batch-collection.md

- Run: 1
- Executor: claude-opus-5-5 (source: transcript)
- Plan blob: `c11c8209a1b7aa54cff896b3439292719a3a935b` (declared)
- Started: 2026-10-03T00:01:00.311891+00:00  Ended: 2026-10-03T00:28:37.474313+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 9
- Delivered: 9   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 9: document the authoritative batch rule  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `3f2903dfa` [refactor] docs: a successful batch is authoritative for its suite (R10.3) (2 files)

### Cycle 8: parallel baseline probes report the per-file count too  _(standard)_
- **Target:** `tddcli::tests/test_timing_visibility.py::test_parallel_baselines_report_how_many_files_fell_to_the_loop`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `efe3fa0cc` [red] test: parallel baseline_captured counts per-file collects (1 files)
  - `614a3bd0b` [green] feat: parallel baseline_captured reports per_file_collects (1 files)
  - `32a037f92` [refactor] refactor: share the baseline_captured payload (1 files)

### Cycle 7: baseline_captured reports how many files fell to the per-file loop  _(standard)_
- **Target:** `tddcli::tests/test_timing_visibility.py::test_baseline_reports_how_many_files_fell_to_the_per_file_loop`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `5ace2e626` [red] test: baseline_captured counts per-file collects (1 files)
  - `a416d8d61` [green] feat: baseline_captured reports per_file_collects (2 files)

### Cycle 6: a test file a successful cargo listing did not list costs no runner start  _(standard)_
- **Target:** `tddcli::tests/test_cargo_adapter.py::test_a_test_file_the_listing_did_not_list_costs_no_runner_start`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `0d43fd7d9` [red] test: a successful cargo listing settles the files it did not list (1 files)
  - `1a3d50f1b` [green] perf: cargo collect invocations name their suite (1 files)

### Cycle 5: a file a successful vitest listing did not name costs no runner start  _(standard)_
- **Target:** `tddcli::tests/test_batch_collection.py::test_vitest_a_file_the_listing_did_not_name_costs_no_runner_start`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `f4fff39e6` [red] test: a successful vitest listing settles the files it did not name (1 files)
  - `dc6810f9c` [green] perf: vitest collect invocations name their suite (1 files)

### Cycle 4: a file a successful pytest batch did not list costs no runner start  _(standard)_
- **Target:** `tddcli::tests/test_batch_collection.py::test_a_file_a_successful_batch_did_not_list_costs_no_runner_start`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `22e42c581` [red] test: a successful batch settles the files it did not list (2 files)
  - `860477096` [green] perf: a successful pytest batch is authoritative for its suite's files (2 files)
  - `dfc448e01` [refactor] refactor: tidy authoritative batch collection (1 files)

### Cycle 3: an adapter whose collect invocations name no suite keeps the per-file loop  _(pin)_
- **Target:** `tddcli::tests/test_batch_collection.py::test_an_adapter_whose_invocations_name_no_suite_keeps_the_loop`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: ['pytest --collect-only -q']`
- **Commits:**
  - `3dcd1d390` [pin] test: pin an adapter whose collect invocations name no suite keeps the per-file loop (1 files)

### Cycle 2: a failed override batch still attributes its own files  _(pin)_
- **Target:** `tddcli::tests/test_batch_collection.py::test_a_failed_override_batch_still_attributes_its_own_files`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert set() == {'contract/test_api.py'}`
- **Commits:**
  - `607831eec` [pin] test: pin a failed override batch still attributes its own files (1 files)
  - `8e9e41d55` [refactor] refactor: tidy override attribution (1 files)

### Cycle 1: an empty successful batch leaves its files to the per-file loop  _(pin)_
- **Target:** `tddcli::tests/test_batch_collection.py::test_an_empty_successful_batch_leaves_its_files_to_the_loop`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert 'backend::tests/test_smoke.py::test_smoke' in set()`
- **Commits:**
  - `b26683b1a` [pin] test: pin an empty successful batch leaves its files to the per-file loop (1 files)

## Time

- Wall clock: 27.6 min. Suite: 21.5 min (78%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 5 | 0.1 | 1.4 |
| AWAITING_PIN | 3 | 0.0 | 1.0 |
| SENSITIVITY | 3 | 0.0 | 0.8 |
| AWAITING_IMPL | 10 | 9.4 | 56.7 |
| CLOSE_SWEEP | 6 | 11.9 | 118.5 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 2.6 | 2.2 | 3 |
| 2 | 2.2 | 1.7 | 3 |
| 3 | 2.2 | 2.0 | 3 |
| 4 | 7.0 | 4.2 | 4 |
| 5 | 2.5 | 2.1 | 3 |
| 6 | 2.1 | 1.8 | 3 |
| 7 | 2.1 | 1.6 | 3 |
| 8 | 4.6 | 4.1 | 4 |
| 9 | 2.2 | 1.8 | 1 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 8's refactor, folding both baseline_captured heartbeats into one helper without changing either payload. plan got wrong: nothing material; the plan was registered by hand (tdd plan register) before run start. harness friction: running pytest directly needs the venv bin on PATH, because the adapter tests shell out to a bare 'pytest'; one combined shell command was refused by the worktree guard and had to be split.

