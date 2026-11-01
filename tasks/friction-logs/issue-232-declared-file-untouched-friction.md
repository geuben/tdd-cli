# Implementation Friction Log: tasks/issue-232-declared-file-untouched.md

- Run: 16
- Executor: claude-opus-5-5 (source: claimed)
- Plan blob: `da80ee57a0395cfd083abd7e8060ec3c766e8122` (declared)
- Started: 2026-11-01T11:53:53.812567+00:00  Ended: 2026-11-01T12:26:30.861773+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 10
- Delivered: 10   Skipped: 0
- Never reached: none
- Unblocks: 0

### Cycle 10: the friction log names untouched paths per cycle, and ancillary ones in plan fidelity  _(standard)_
- **Target:** `tddcli::tests/test_declared_untouched.py::test_the_friction_log_names_untouched_paths_per_cycle_and_for_ancillary_files`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `cb7b3ac44` [red] test: the friction log must name untouched declared paths (1 files)
  - `d2e3af71f` [green] feat: render declared_file_untouched in the friction log's plan fidelity (4 files)

### Cycle 9: the final skip reply names the untouched paths and asks for a note  _(standard)_
- **Target:** `tddcli::tests/test_declared_untouched.py::test_the_final_skip_reply_names_the_untouched_paths_and_asks_for_a_note`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `4cfc4ac2c` [red] test: the final skip reply must name the untouched paths (1 files)
  - `490b1f08d` [green] feat: the final skip reply names untouched declared paths and asks for a note (1 files)

### Cycle 8: the complete reply names the untouched paths and asks for a note  _(standard)_
- **Target:** `tddcli::tests/test_declared_untouched.py::test_the_complete_reply_names_the_untouched_paths_and_asks_for_a_note`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `c83f52432` [red] test: the complete reply must name the untouched paths (1 files)
  - `98fe7b269` [green] feat: the complete reply names untouched declared paths and asks for a note (1 files)

### Cycle 7: skipping the last cycle records the untouched paths  _(standard)_
- **Target:** `tddcli::tests/test_declared_untouched.py::test_skipping_the_last_cycle_records_the_untouched_paths`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `bda2b1bb5` [red] test: skipping the last cycle must record the untouched paths (1 files)
  - `a7b7ffee4` [green] feat: a final cycle skip records declared_file_untouched (1 files)

### Cycle 6: paths committed under the project root, removed, skipped or ignored are not reported  _(standard)_
- **Target:** `tddcli::tests/test_declared_untouched.py::test_paths_committed_under_the_project_root_removed_skipped_or_ignored_are_not_reported`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `72adefdd8` [red] test: project-relative, removed, skipped and ignored paths are not untouched (1 files)
  - `26fca49d8` [green] feat: resolve declared paths under their project root, drop skipped and ignored ones (1 files)

### Cycle 5: a last close that blocks still records the untouched paths  _(pin)_
- **Target:** `tddcli::tests/test_declared_untouched.py::test_a_last_close_that_blocks_still_records_the_untouched_paths`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert ('blocked', []) == ('blocked', [.../never.py'])])`
- **Commits:**
  - `9ea4a5b96` [pin] test: pin — a blocked last close still records declared_file_untouched (1 files)

### Cycle 4: the last close records the declared paths no commit of the run touched  _(standard)_
- **Target:** `tddcli::tests/test_declared_untouched.py::test_the_last_close_records_the_declared_paths_no_commit_of_the_run_touched`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `394a2c19b` [red] test: the last close must record the declared paths no commit touched (1 files)
  - `6fe3bf458` [green] feat: record declared_file_untouched when the last cycle closes (3 files)

### Cycle 3: a run with no recorded start_sha still ends complete  _(pin)_
- **Target:** `tddcli::tests/test_declared_untouched.py::test_a_run_with_no_recorded_start_sha_still_ends_complete`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert {'advance': N...': 'complete'} == {'advance': '...': 'complete'}`
- **Commits:**
  - `96a0ccd96` [pin] test: pin — a run with no recorded start_sha still ends complete (1 files)

### Cycle 2: the complete reply is unchanged when every declared path was committed  _(pin)_
- **Target:** `tddcli::tests/test_declared_untouched.py::test_the_complete_reply_is_unchanged_when_every_declared_path_was_committed`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `assert {'advance': '...log render`.'} == {'advance': '...log render`.'}`
- **Commits:**
  - `b15e0a0b4` [pin] test: pin — the complete reply is unchanged when nothing declared is untouched (1 files)

### Cycle 1: a run that committed every declared path records no declared_file_untouched  _(pin)_
- **Target:** `tddcli::tests/test_declared_untouched.py::test_a_run_that_committed_every_declared_path_records_no_untouched_event`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert {'advance': [...], 'skip': []} == {'advance': [], 'skip': []}`
- **Commits:**
  - `06e60f354` [pin] test: pin — a run that committed every declared path records no untouched event (1 files)

## Time

- Wall clock: 32.6 min. Suite: 26.5 min (81%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 6 | 0.4 | 3.8 |
| AWAITING_PIN | 4 | 0.4 | 6.1 |
| SENSITIVITY | 4 | 0.4 | 5.9 |
| AWAITING_IMPL | 12 | 14.7 | 73.3 |
| CLOSE_SWEEP | 4 | 10.6 | 159.3 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 3.9 | 2.7 | 3 |
| 2 | 2.9 | 2.7 | 3 |
| 3 | 3.6 | 3.1 | 3 |
| 4 | 3.6 | 2.8 | 3 |
| 5 | 3.2 | 2.9 | 3 |
| 6 | 3.3 | 2.6 | 3 |
| 7 | 3.4 | 2.9 | 3 |
| 8 | 3.2 | 2.6 | 3 |
| 9 | 2.4 | 2.0 | 3 |
| 10 | 3.1 | 2.1 | 3 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 6, four exclusion rules (project-root spellings, --no-renames, skip filter, ignore filter) in one method, but the plan's probed expected failure matched exactly. plan got wrong: cycle 1 says to write the full import block (os, git, run_cli_text) up front, but unused imports fail ruff F401 in the close sweep, so each import was added in the cycle that first uses it. Cycle 4 used a bare 'if last:' call rather than binding 'untouched' early, for the same F841 reason the plan gives for cycle 7; cycle 8 bound it. render's plan-level filter uses non-skipped cycles, as decision 7 says. harness friction: none; each close sweep took ~150 s.

