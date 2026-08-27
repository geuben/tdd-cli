# Implementation Friction Log: tasks/issue-45-baseline-reuse.md

- Run: 3
- Executor: claude-sonnet-4-6 (source: transcript)
- Plan blob: `f84076d3ce1794ce15d676c9ebd945da823c9971` (declared)
- Started: 2026-08-23T20:12:11.861627+00:00  Ended: 2026-08-23T21:17:31.916266+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 7
- Delivered: 7   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 7: a stale reused baseline still recovers via resume --unblock --accept-failures  _(pin)_
- **Target:** `tddcli::tests/test_baseline_integrity.py::test_stale_reused_baseline_recovers_via_accept_failures`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `repo = PosixPath('/private/var/folders/zl/3010c_557g5_2rm9tyqsc03h0000gp/T/pytest-of-headless-coding/pytest-597/test_stale_reused_baseline_rec0/workspace')`
- **Commits:**
  - `390548698` [pin] test: pin that accept-failures folds a drifted failure into a reused baseline (1 files)

### Cycle 6: a cache entry older than --reuse-max-age is ignored and re-probed  _(standard)_
- **Target:** `tddcli::tests/test_snapshot_and_identity.py::test_cached_baseline_respects_max_age`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (**passed**)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `tmp_path = PosixPath('/private/var/folders/zl/3010c_557g5_2rm9tyqsc03h0000gp/T/pytest-of-headless-coding/pytest-589/test_cached_baseline_respects_0')`
- **Commits:**
  - `f9c1bca64` [refactor] refactor: a cache entry older than --reuse-max-age is ignored and re-probed (1 files)
- **Event — red_first_violation:** ["tddcli::tests/test_snapshot_and_identity.py::test_cached_baseline_respects_max_age"]

### Cycle 5: a reused baseline row records its provenance and a baseline_reused event  _(standard)_
- **Target:** `tddcli::tests/test_baseline_integrity.py::test_reused_baseline_records_provenance_and_event`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `488be9fef` [red] test: reused baseline row is marked reused and logs a baseline_reused event (1 files)
  - `7e238a1ad` [green] feat: baseline.source provenance column and baseline_reused event (schema v5) (2 files)

### Cycle 4: a second --reuse-baselines run reuses the cached probe and skips the suite  _(standard)_
- **Target:** `tddcli::tests/test_baseline_integrity.py::test_second_reuse_run_reuses_cached_baseline`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `845202ace` [red] test: identical reuse run emits baseline_reused, not baseline_captured (1 files)
  - `969f190db` [green] feat: reuse cached failing set + collection snapshot, skipping the probe (1 files)

### Cycle 3: --reuse-baselines populates the cache on probe; default writes nothing  _(standard)_
- **Target:** `tddcli::tests/test_baseline_integrity.py::test_reuse_baselines_populates_cache_and_default_does_not`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `3d063bd70` [red] test: --reuse-baselines writes cache rows, default leaves cache empty (1 files)
  - `0d6cee6e2` [green] feat: --reuse-baselines flag populates baseline_cache after each probe (2 files)

### Cycle 2: baseline_cache persists and looks up a probe result keyed by (project, tree_hash, config_sha)  _(standard)_
- **Target:** `tddcli::tests/test_snapshot_and_identity.py::test_baseline_cache_round_trips_by_content_key`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `f2a7e1b9c` [red] test: baseline_cache round-trips a probe by content key (1 files)
  - `a0bb93317` [green] feat: baseline_cache table with cache_baseline/cached_baseline (schema v4) (1 files)
  - `a56b5737b` [refactor] refactor: baseline_cache persists and looks up a probe result keyed by (project, tree_hash, config_sha) (1 files)

### Cycle 1: upstream_producer_roots returns a project's own root plus its upstream artifact producers' roots  _(standard)_
- **Target:** `tddcli::tests/test_config_and_staging.py::test_upstream_producer_roots_includes_self_and_upstream_producers`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `d7117e8e9` [red] test: upstream_producer_roots resolves self plus upstream producer roots (1 files)
  - `901e9f678` [green] feat: Config.upstream_producer_roots for baseline cache keys (1 files)

