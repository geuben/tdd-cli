# Implementation Friction Log: tasks/issue-46-parallel-baseline-probing.md

- Run: 5
- Executor: unknown (source: unknown)
- Plan blob: `e02a1ae0d8b7c257ae9b6a785af2560cfa4c1817` (declared)
- Started: 2026-08-24T20:40:22.508370+00:00  Ended: 2026-08-24T21:08:42.941015+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 5
- Delivered: 5   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 5: a probe failure under concurrency aborts before a run row and releases the claim  _(standard)_
- **Target:** `tddcli::tests/test_baseline_integrity.py::test_concurrent_probe_failure_aborts_and_releases_claim`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `f77fd6b50` [red] test: a concurrent probe failure aborts cleanly and frees the worktree (1 files)
  - `b0dc92f56` [green] fix: a worker probe exception becomes an attributed failure, claim released (1 files)

### Cycle 4: baseline_captured heartbeat is emitted per project under concurrency  _(standard)_
- **Target:** `tddcli::tests/test_heartbeat.py::test_baseline_captured_lines_emitted_under_concurrency`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `9bc4cdb7e` [red] test: baseline_captured heartbeat survives the worker pool (1 files)
  - `1f177b825` [green] feat: emit baseline_captured from the main thread as probes complete (1 files)

### Cycle 3: with jobs>1 the reachable projects are probed concurrently  _(standard)_
- **Target:** `tddcli::tests/test_baseline_integrity.py::test_run_start_probes_concurrently_under_a_bounded_pool`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `b25c76eb1` [red] test: run start probes concurrently under a bounded pool (1 files)
  - `a002b4f9d` [green] feat: bounded ThreadPoolExecutor for baseline probing when jobs>1 (1 files)

### Cycle 2: --baseline-jobs below 1 is refused  _(standard)_
- **Target:** `tddcli::tests/test_baseline_integrity.py::test_run_start_refuses_baseline_jobs_below_one`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `33099debd` [red] test: --baseline-jobs must be >= 1 (1 files)
  - `ccbdeafd0` [green] feat: reject --baseline-jobs < 1 before probing (1 files)

### Cycle 1: run start accepts --baseline-jobs N, default 1  _(standard)_
- **Target:** `tddcli::tests/test_baseline_integrity.py::test_run_start_accepts_baseline_jobs_flag`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `298ee26a4` [red] test: run start accepts --baseline-jobs (1 files)
  - `644e91d7f` [green] feat: --baseline-jobs flag on run start (parsed, default 1) (1 files)

