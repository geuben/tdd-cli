# Implementation Friction Log: tasks/issue-163-vitest-adoption-ids.md

- Run: 1
- Executor: claude-opus-5-5 (source: transcript)
- Plan blob: `4cce3c1b230d70ba6e80e3b79d3056f9f50baba2` (declared)
- Started: 2026-09-25T08:58:07.893400+00:00  Ended: 2026-09-25T09:30:35.439682+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 10
- Delivered: 10   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 10: an adopted target the run cannot find is refused  _(standard)_
- **Target:** `tddcli::tests/test_advance_adoption.py::test_an_adopted_target_the_run_cannot_find_is_refused`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `9450800fd` [red] test: an adoption the run cannot find is refused (1 files)
  - `794024aca` [green] fix: refuse an adopted target the run cannot find (1 files)
  - `9e147f55a` [refactor] refactor: tidy the refused adoption (4 files)

### Cycle 9: fold the two adoption branches into one path  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `7baa42d2d` [refactor] refactor: one adoption path for single and resolved candidates (1 files)

### Cycle 8: a resolved adoption the run did not evaluate asks for another advance  _(pin)_
- **Target:** `tddcli::tests/test_advance_adoption.py::test_a_resolved_adoption_the_run_did_not_evaluate_asks_for_another_advance`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `KeyError: 'adopted'`
- **Commits:**
  - `a2a8dbd95` [pin] test: pin the unevaluated resolved-candidate adoption reply (1 files)

### Cycle 7: an adopted target the run did not evaluate asks for another advance  _(pin)_
- **Target:** `tddcli::tests/test_advance_adoption.py::test_an_adopted_target_the_run_did_not_evaluate_asks_for_another_advance`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `KeyError: 'adopted'`
- **Commits:**
  - `237fd8496` [pin] test: pin the unevaluated single-candidate adoption reply (1 files)

### Cycle 6: tdd target accepts every spelling of a collected test  _(standard)_
- **Target:** `tddcli::tests/test_target_validation.py::test_target_accepts_every_spelling_of_a_collected_test`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `e43812545` [red] test: tdd target accepts the plan's spelling of a test (1 files)
  - `0eb1e6ac5` [green] fix: tdd target matches ids the way a plan declaration does (1 files)
  - `eb6524ce9` [refactor] refactor: tidy tdd target matching (3 files)

### Cycle 5: adoption never picks a test another cycle already targets  _(standard)_
- **Target:** `tddcli::tests/test_advance_adoption.py::test_adoption_skips_a_test_an_earlier_cycle_targets`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `f19c824b3` [red] test: adoption skips an earlier cycle's target (3 files)
  - `67a8ef305` [green] fix: exclude every cycle's target from adoption candidates (1 files)
  - `51f64300e` [refactor] refactor: tidy adoption candidates (2 files)

### Cycle 4: the vitest isolation probe fails when the listing is not JSON  _(standard)_
- **Target:** `tddcli::tests/test_suite_overrides.py::test_vitest_isolation_probe_fails_on_a_listing_that_is_not_json`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `7108dd7bc` [red] test: an unreadable vitest listing fails the isolation probe (1 files)
  - `ec6c2a769` [green] fix: fail the vitest isolation probe on a listing that is not JSON (1 files)
  - `d4e65b322` [refactor] refactor: tidy the vitest isolation probe (4 files)

### Cycle 3: the vitest override-isolation probe reads `vitest list --json`  _(standard)_
- **Target:** `tddcli::tests/test_suite_overrides.py::test_vitest_isolation_probe_flags_default_reach_into_override_files`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `2c376823a` [red] test: the vitest isolation probe reads list --json (1 files)
  - `93d7cc35b` [green] fix: the vitest isolation probe reads file paths from list --json (1 files)
  - `ac4efcfed` [refactor] refactor: share the vitest JSON listing between collection and isolation (1 files)

### Cycle 2: a vitest batch listing that is not JSON is left to the per-file loop  _(standard)_
- **Target:** `tddcli::tests/test_batch_collection.py::test_vitest_batch_leaves_a_text_listing_to_the_per_file_loop`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `7a33ca920` [red] test: a text vitest listing is not trusted by the batch (1 files)
  - `06cd70319` [green] fix: drop the text parse from vitest batch collection (2 files)

### Cycle 1: vitest batch collection builds ids from `vitest list --json`  _(standard)_
- **Target:** `tddcli::tests/test_vitest_adapter.py::test_batch_collection_roots_each_id_at_its_listed_file`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `8ca346a82` [red] test: vitest batch collection reads each id's file from list --json (1 files)
  - `d43dc65cf` [green] fix: build vitest batch ids from vitest list --json (2 files)
  - `e472d9574` [refactor] refactor: tidy the vitest JSON listing (3 files)

## Time

- Wall clock: 32.5 min. Suite: 25.8 min (79%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 7 | 0.1 | 0.8 |
| AWAITING_PIN | 2 | 0.1 | 2.3 |
| SENSITIVITY | 2 | 0.1 | 2.3 |
| AWAITING_IMPL | 14 | 11.2 | 48.1 |
| CLOSE_SWEEP | 9 | 14.3 | 95.3 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 4.1 | 3.3 | 4 |
| 2 | 2.1 | 1.7 | 3 |
| 3 | 3.6 | 3.2 | 4 |
| 4 | 3.4 | 3.0 | 4 |
| 5 | 4.7 | 3.2 | 4 |
| 6 | 4.0 | 3.3 | 4 |
| 7 | 2.1 | 1.7 | 3 |
| 8 | 2.0 | 1.6 | 3 |
| 9 | 2.2 | 1.5 | 1 |
| 10 | 4.1 | 3.2 | 4 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 5, building fake_vitest.py + repo_vitest so adoption could be driven end to end; every expected failure in the plan matched verbatim. plan got wrong: nothing material; cycle 8's test needed a ruff-format wrap, applied in cycle 10's refactor phase. harness friction: running the suite directly with '.venv/bin/python -m pytest -n0' gave spurious NoneType envelopes (in-process CLI needs the uv-run env); 'uv run pytest' was correct. Worktree guard refused a heredoc append chained with tdd advance; split commands.

