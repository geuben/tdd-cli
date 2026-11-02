# Implementation Friction Log: tasks/issue-235-test-only-green-and-reference-paths.md

- Run: 18
- Executor: claude-opus-5-5 (source: claimed)
- Plan blob: `2103f56fa6d6b2ac250db0df0204543dbf33ff5c` (declared)
- Started: 2026-11-01T12:46:09.096658+00:00  Ended: 2026-11-01T13:29:37.690953+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 9
- Delivered: 9   Skipped: 0
- Never reached: none
- Unblocks: 0

### Cycle 9: the friction log shows reference_path_touched in the cycle's section  _(standard)_
- **Target:** `tddcli::tests/test_reference_paths.py::test_the_friction_log_shows_reference_path_touched_in_the_cycle_section`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `056754d40` [red] test: the friction log must show reference_path_touched beside the cycle's commits (1 files)
  - `32eafc1b1` [green] feat: record reference_path_touched as an integrity event on the cycle (2 files)

### Cycle 8: a reference path an artifact regenerates at close blocks the run  _(standard)_
- **Target:** `tddcli::tests/test_reference_paths.py::test_a_reference_path_regenerated_at_close_blocks_the_run`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `690190920` [red] test: a reference path regenerated at close must block (1 files)
  - `8bc451b80` [green] feat: re-check reference paths after a close regenerates artifacts (1 files)

### Cycle 7: a reference path committed behind the tool's back blocks the next advance  _(standard)_
- **Target:** `tddcli::tests/test_reference_paths.py::test_a_reference_path_committed_behind_the_tool_blocks_the_next_advance`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `590ecb3ec` [red] test: a reference path committed since run start must block (1 files)
  - `0e97ac839` [green] feat: reference paths are compared with the run's start commit (2 files)

### Cycle 6: an uncommitted change to a reference path blocks the run, in every phase  _(standard)_
- **Target:** `tddcli::tests/test_reference_paths.py::test_touching_a_reference_path_blocks_the_run_in_every_phase`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `40cc08c21` [red] test: touching a reference path must block the run in every phase (1 files)
  - `bd3d22aee` [green] feat: a changed reference path is a reference_path_touched blocker (5 files)
  - `2fc1b8862` [refactor] refactor: tidy the reference path gate (1 files)

### Cycle 5: plan register stores the contract's reference_paths in the ledger  _(standard)_
- **Target:** `tddcli::tests/test_reference_paths.py::test_plan_register_stores_reference_paths`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `204acd2bd` [red] test: plan register must store reference_paths (2 files)
  - `1f1f37793` [green] feat: store a contract's reference_paths in a new ledger table (2 files)

### Cycle 4: reference_paths parses as a list of strings, and anything else is a contract error  _(standard)_
- **Target:** `tddcli::tests/test_reference_paths.py::test_reference_paths_parse_as_a_list_of_strings_or_fail`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `9b115c9dd` [red] test: reference_paths must parse as a list of strings or fail (2 files)
  - `322ba83fe` [green] feat: parse the plan-level reference_paths key (3 files)
  - `1ab8606e2` [refactor] refactor: tidy the front-matter path-list parsing (1 files)

### Cycle 3: the friction log shows green_without_implementation in the cycle's section  _(pin)_
- **Target:** `tddcli::tests/test_green_without_implementation.py::test_the_friction_log_shows_green_without_implementation_in_the_cycle_section`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `…est_golden.py::test_output_matches_gol...st: output matches the golden file (2 files)\n  - `fc391cd52` [green] feat: output matches the golden file (1 files)\n'`
- **Commits:**
  - `630fca92b` [pin] test: pin — the friction log shows green_without_implementation beside the cycle's commits (1 files)

### Cycle 2: green_without_implementation is a nudge: the GREEN reply asks for a tdd note  _(standard)_
- **Target:** `tddcli::tests/test_green_without_implementation.py::test_a_green_of_only_test_files_asks_for_a_note`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `6033b63c1` [red] test: a GREEN of only test files must ask for a tdd note (1 files)
  - `2a754d925` [green] feat: green_without_implementation is a nudge (3 files)

### Cycle 1: a GREEN whose staged set is only test files records green_without_implementation  _(standard)_
- **Target:** `tddcli::tests/test_green_without_implementation.py::test_green_without_implementation_fires_only_when_every_staged_path_is_a_test`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `ffa0a727d` [red] test: a GREEN of only test files must record green_without_implementation (1 files)
  - `890b74bb6` [green] feat: record green_without_implementation when GREEN stages only test files (2 files)

## Time

- Wall clock: 43.5 min. Suite: 36.1 min (83%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 8 | 0.9 | 6.6 |
| AWAITING_PIN | 1 | 0.1 | 3.6 |
| SENSITIVITY | 1 | 0.1 | 3.3 |
| AWAITING_IMPL | 16 | 25.8 | 96.6 |
| CLOSE_SWEEP | 3 | 9.3 | 186.4 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 5.5 | 3.7 | 3 |
| 2 | 4.3 | 3.7 | 3 |
| 3 | 4.0 | 3.5 | 3 |
| 4 | 7.8 | 7.2 | 4 |
| 5 | 3.1 | 2.4 | 3 |
| 6 | 6.3 | 5.0 | 4 |
| 7 | 3.1 | 2.6 | 3 |
| 8 | 4.7 | 4.1 | 3 |
| 9 | 4.6 | 3.9 | 3 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 6 — four end-to-end drives in one test, and the BLOCKED envelope had to match the run-close gate's shape (refactor extracted _blocked_run for both). plan got wrong: nothing material; every EXPECTED FAILURE matched as written, and cycle 3's pin passed on arrival and bit under a render-loop mutation. Deviations: test helpers _advance_to_impl/_advance_expecting added for the repeated 'advance, assert write_implementation' step; cycle 4 refactor folded both path-list validations into contract._path_list. harness friction: tdd advance prints progress JSON lines before the envelope on stdout, so piping straight into json.load fails; worked around with a wrapper.

