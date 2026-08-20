# Implementation Friction Log: tasks/issue-44-scoped-baselines.md

- Run: 1
- Executor: claude-sonnet-4-6 (source: transcript)
- Plan blob: `5b8e7da2857f0dc4b696278d39480ddf9a2b4dbf` (declared)
- Started: 2026-08-19T22:26:17.575041+00:00  Ended: 2026-08-20T00:02:35.720336+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 11
- Delivered: 11   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 11: --accept-failures creates a baseline row for a project that never had one  _(standard)_
- **Target:** `tddcli::tests/test_baseline_integrity.py::test_accept_failures_inserts_baseline_row_for_unbaselined_project`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `3c817b52b` [red] test: accept-failures covers projects with no baseline row (1 files)
  - `baa99567a` [green] fix: accept-failures inserts missing baseline rows (1 files)

### Cycle 10: close sweep with unattributable failures directs the blocker path  _(standard)_
- **Target:** `tddcli::tests/test_baseline_integrity.py::test_close_sweep_with_unbaselined_failures_directs_resolve_blocker`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `47ff6ace9` [red] test: unattributable sweep failures direct the blocker path (2 files)
  - `a3a31dbbc` [green] feat: unattributable sweep failures get a legible blocker reply (1 files)

### Cycle 9: the sweep separates un-baselined projects' failures from regressions  _(standard)_
- **Target:** `tddcli::tests/test_baseline_integrity.py::test_sweep_reports_unbaselined_failures_separately`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `e03262be4` [red] test: sweep separates unattributable failures (1 files)
  - `0eb32c06d` [green] feat: sweep classifies un-baselined failures as unattributable (1 files)
  - `13ec7aec6` [refactor] refactor: the sweep separates un-baselined projects' failures from regressions (1 files)

### Cycle 8: no_baseline_for_project is a typed blocker kind  _(standard)_
- **Target:** `tddcli::tests/test_baseline_integrity.py::test_blocker_accepts_no_baseline_for_project_kind`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `302aa9b1d` [red] test: no_baseline_for_project blocker kind (1 files)
  - `c04a79eb0` [green] feat: no_baseline_for_project blocker kind (1 files)

### Cycle 7: --baseline-all restores full probing  _(standard)_
- **Target:** `tddcli::tests/test_baseline_integrity.py::test_run_start_baseline_all_probes_every_project`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `14f61841f` [red] test: --baseline-all opts out of scoping (1 files)
  - `65ea14e5e` [green] feat: --baseline-all flag on run start (1 files)
  - `49bb96867` [refactor] refactor: --baseline-all restores full probing (1 files)

### Cycle 6: skipped projects are recorded via a baseline_scoped event  _(standard)_
- **Target:** `tddcli::tests/test_baseline_integrity.py::test_run_start_records_baseline_scoped_event`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `cb3d7fbcd` [red] test: baseline scoping is recorded on the run (1 files)
  - `e852f57ee` [green] feat: record baseline_scoped event with skipped projects (2 files)

### Cycle 5: run start probes only reachable projects  _(standard)_
- **Target:** `tddcli::tests/test_baseline_integrity.py::test_run_start_probes_only_reachable_projects`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 2, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `6163f26fe` [red] test: run start scopes baseline probe to reachable projects (3 files)
  - `2560954de` [green] feat: scope run-start baseline capture to plan-reachable projects (1 files)
  - `580c909b6` [refactor] refactor: run start probes only reachable projects (1 files)

### Cycle 4: downstream projects excluded from the close sweep are not reachable  _(standard)_
- **Target:** `tddcli::tests/test_config_and_staging.py::test_reachable_projects_excludes_downstream_not_in_close_sweep`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `ba1b7c39d` [red] test: in_close_sweep filter on reachable consumers (1 files)
  - `2ead83676` [green] feat: reachable_projects respects in_close_sweep (1 files)

### Cycle 3: reachable_projects resolves artifact.<name> producer chains to their root project  _(standard)_
- **Target:** `tddcli::tests/test_config_and_staging.py::test_reachable_projects_resolves_artifact_upstream_chain`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `ae923597d` [red] test: reachable_projects follows artifact upstream chains (1 files)
  - `8ef8f40e1` [green] feat: resolve artifact.<name> producers in reachable_projects (1 files)
  - `ad8524ab3` [refactor] refactor: shared root-producer resolution for touched and reachable (1 files)

### Cycle 2: reachable_projects follows consumed_by transitively  _(standard)_
- **Target:** `tddcli::tests/test_config_and_staging.py::test_reachable_projects_includes_transitive_consumers`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `51a8c8033` [red] test: reachable_projects transitive consumed_by closure (1 files)
  - `41c44a3ec` [green] feat: transitive consumer closure in reachable_projects (1 files)

### Cycle 1: reachable_projects returns declared projects when no artifacts exist  _(standard)_
- **Target:** `tddcli::tests/test_config_and_staging.py::test_reachable_projects_returns_declared_when_no_artifacts`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `664bf1fd8` [red] test: reachable_projects with no artifact graph (1 files)
  - `ea6883e9d` [green] feat: Config.reachable_projects, declared-only case (1 files)

