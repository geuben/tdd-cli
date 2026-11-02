# Implementation Friction Log: tasks/issue-234-cycle-close-undeclared-gate.md

- Run: 17
- Executor: claude-opus-5-5 (source: claimed)
- Plan blob: `a3e89b2bdd89244b120f40b47bc1fa9a15f61fd0` (declared)
- Started: 2026-11-01T11:56:09.739249+00:00  Ended: 2026-11-01T12:16:43.390167+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 5
- Delivered: 5   Skipped: 0
- Never reached: none
- Unblocks: 0

### Cycle 5: a RED taken on a dirty tree names the paths its commit left out  _(standard)_
- **Target:** `tddcli::tests/test_red_on_dirty_tree.py::test_a_red_on_a_dirty_tree_names_the_paths_its_commit_left_out`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `40429ed90` [red] test: a RED on a dirty tree must name the paths its commit left out (1 files)
  - `903ea3c01` [green] feat: record red_on_dirty_tree when the RED commit leaves changed paths out (3 files)

### Cycle 4: unblocking with the path still dirty holds the close again  _(pin)_
- **Target:** `tddcli::tests/test_cycle_close_gate.py::test_unblocking_with_the_path_still_dirty_holds_the_close_again`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert ('write_test'...ommitted': 1}) == ('blocked', [...ommitted': 2})`
- **Commits:**
  - `ad6b27f2f` [pin] test: pin — an unblock that leaves the path dirty is held again (1 files)

### Cycle 3: committing or discarding the held path, then unblocking, lets the next advance close the cycle  _(pin)_
- **Target:** `tddcli::tests/test_cycle_close_gate.py::test_committing_or_discarding_the_held_path_lets_the_cycle_close`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert {'commit': (1...cked', False)} == {'commit': (2..._test', True)}`
- **Commits:**
  - `2124fc899` [pin] test: pin — a committed or discarded held path lets the cycle close (1 files)

### Cycle 2: a flagged path still dirty holds an earlier cycle's close  _(standard)_
- **Target:** `tddcli::tests/test_cycle_close_gate.py::test_a_dirty_flagged_path_holds_the_cycle_close`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `99b4967b3` [red] test: a dirty flagged path must hold the cycle close (1 files)
  - `3fa05fd53` [green] fix: a flagged path still dirty holds the cycle close, not only the run close (6 files)
  - `396b8372b` [refactor] refactor: share the blocked-close envelope (1 files)

### Cycle 1: the last cycle keeps the run-close gate, and an unblock still completes the run  _(pin)_
- **Target:** `tddcli::tests/test_cycle_close_gate.py::test_the_last_cycle_keeps_the_run_close_gate`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert ('blocked', '...r_or_advance') == ('blocked', 'complete')`
- **Commits:**
  - `58453a055` [pin] test: pin — the last cycle keeps the run-close gate (1 files)

## Time

- Wall clock: 20.6 min. Suite: 16.5 min (80%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 2 | 0.1 | 4.3 |
| AWAITING_PIN | 3 | 0.2 | 4.5 |
| SENSITIVITY | 3 | 0.2 | 4.8 |
| AWAITING_IMPL | 4 | 5.4 | 81.1 |
| CLOSE_SWEEP | 4 | 10.5 | 157.7 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 3.4 | 2.8 | 3 |
| 2 | 6.6 | 5.2 | 4 |
| 3 | 3.5 | 2.9 | 3 |
| 4 | 3.2 | 2.7 | 3 |
| 5 | 3.9 | 2.9 | 3 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 5, because decision 6 offered moving paths_for_phase above the RED block, but adopt_stubs mutates the classification inside that block, so the event is computed after the existing paths line instead. Plan got wrong: nothing material; every expected failure and pin matched its probe. Harness friction: none; cycles 2 and 5 skipped the optional refactor only for cycle 5 (emission is four lines).
> correction to the previous note: cycle 2 did its planned refactor (shared _undeclared_blocked envelope); only cycle 5 skipped its optional refactor.

