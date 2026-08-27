# Implementation Friction Log: tasks/issue-70-ancillary-files.md

- Run: 9
- Executor: claude-sonnet-4-6 (source: transcript)
- Plan blob: `4231381de700f8473d4bd3893031ace8bc7c5511` (declared)
- Started: 2026-08-27T22:20:59.570485+00:00  Ended: 2026-08-27T22:56:02.681850+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 6
- Delivered: 6   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 6: a declared ancillary file is committed and fires no undeclared_file_touched  _(standard)_
- **Target:** `tddcli::tests/test_ancillary_files.py::test_declared_ancillary_file_is_committed_and_not_flagged`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `85e6efb6b` [red] test: a declared ancillary file is committed and fires no undeclared_file_touched (1 files)
  - `48e0dd3e1` [green] feat: Engine loads ancillary_files and advance stages them (2 files)

### Cycle 5: staging.classify routes a declared ancillary path to its own bucket and stages it  _(standard)_
- **Target:** `tddcli::tests/test_config_and_staging.py::test_declared_ancillary_file_is_bucketed_and_staged`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `28323c178` [red] test: a declared ancillary path is bucketed out of outside and staged (2 files)
  - `bb08d92e9` [green] feat: staging.classify routes declared ancillary files to their own bucket (1 files)

### Cycle 4: plan register persists declared ancillary_files into the ledger row  _(standard)_
- **Target:** `tddcli::tests/test_ancillary_files.py::test_plan_register_persists_ancillary_files`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 4}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `5031a2498` [red] test: plan register persists declared ancillary_files (1 files)
  - `ddb1329b0` [green] feat: cmd_plan_register writes ancillary_files to the ledger (1 files)
  - `8805a1df4` [refactor] refactor: plan register persists declared ancillary_files into the ledger row (1 files)
  - `7eaa56b4f` [refactor] refactor: plan register persists declared ancillary_files into the ledger row (1 files)
  - `ac93b7ead` [refactor] refactor: plan register persists declared ancillary_files into the ledger row (1 files)

### Cycle 3: plan_contract carries an ancillary_files column, migrated on old ledgers  _(standard)_
- **Target:** `tddcli::tests/test_release_surface.py::test_plan_contract_gains_ancillary_files_column`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `8c1f0e8e0` [red] test: plan_contract carries an ancillary_files column (1 files)
  - `8afd9ee24` [green] feat: ancillary_files column with a v5->v6 migration (1 files)

### Cycle 2: non-list / non-string ancillary_files hard-fails registration  _(standard)_
- **Target:** `tddcli::tests/test_contract.py::test_non_list_ancillary_files_raises_contract_error`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `34a9490de` [red] test: non-list ancillary_files is rejected (1 files)
  - `eb1952cf7` [green] feat: validate ancillary_files is a list of strings (1 files)

### Cycle 1: top-level ancillary_files parses onto PlanContract.ancillary_files  _(standard)_
- **Target:** `tddcli::tests/test_contract.py::test_ancillary_files_parse_onto_plan_contract`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `5a7b62822` [red] test: top-level ancillary_files parses onto PlanContract (1 files)
  - `815f30cdb` [green] feat: PlanContract.ancillary_files from top-level front-matter key (1 files)

