# Implementation Friction Log: tasks/issue-146-content-tree-hash.md

- Run: 2
- Executor: claude-opus-5-5 (source: transcript)
- Plan blob: `2bf303506db858d153a3adb0fb0df291d95482a3` (declared)
- Started: 2026-09-22T22:17:19.205098+00:00  Ended: 2026-09-22T22:44:34.468999+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 9
- Delivered: 9   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 9: a cycle with no refactor edit skips its own close-sweep suite  _(pin)_
- **Target:** `tddcli::tests/test_close_sweep_gates.py::test_a_cycle_with_no_refactor_edit_skips_its_own_close_sweep_suite`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert ('complete', 1) == ('complete', 0)`
- **Commits:**
  - `dc6163403` [pin] test: pin that a cycle with no refactor edit skips its close-sweep suite (1 files)

### Cycle 8: the same content hashes the same unstaged, staged and committed  _(standard)_
- **Target:** `tddcli::tests/test_tree_hash.py::test_the_same_content_hashes_the_same_unstaged_staged_and_committed`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `2f3262178` [red] test: tree_hash is independent of index and commit state (1 files)
  - `76c8d464b` [green] fix: tree_hash hashes working-tree content, not git state (4 files)
> **note** _(during AWAITING_REFACTOR)_: cycle 8: the plan's decision 2 said to copy the real index to seed the stat cache, but a plain shutil.copyfile gives the copy a fresh mtime and defeats git's racy-clean check, so a same-size edit in the same second as the last index write hashed as unchanged. It showed up as an intermittent failure of this cycle's own test in the full suite; a scratch stress loop missed 1/200 edits with copyfile and 0/1000 with shutil.copy2, which the GREEN uses. No test in the contract pins this; it deserves one in a follow-up.

### Cycle 7: a root that exists neither on disk nor in the index hashes without error  _(pin)_
- **Target:** `tddcli::tests/test_tree_hash.py::test_a_missing_root_hashes_without_error`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `tddcli.gitutil.GitError: git add -A --dry-run -- nope failed: fatal: pathspec 'nope' did not match any files`
- **Commits:**
  - `87df11332` [pin] test: pin that tree_hash accepts a root that does not exist yet (1 files)

### Cycle 6: hashing leaves the real index untouched  _(pin)_
- **Target:** `tddcli::tests/test_tree_hash.py::test_hashing_leaves_the_index_untouched`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert 'p/a.py\np/new.py\n' == ''`
- **Commits:**
  - `6ec73a56b` [pin] test: pin that tree_hash stages nothing (1 files)

### Cycle 5: a change outside the hashed roots does not change the tree hash  _(pin)_
- **Target:** `tddcli::tests/test_tree_hash.py::test_a_change_outside_the_roots_does_not_change_the_hash`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert 'c728c4e22058...2969c100a993b' == '6fa12a997205...ad6996101db7f'`
- **Commits:**
  - `364d84af8` [pin] test: pin that tree_hash is scoped to its roots (1 files)

### Cycle 4: an ignored file does not change the tree hash  _(pin)_
- **Target:** `tddcli::tests/test_tree_hash.py::test_an_ignored_file_does_not_change_the_hash`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert 'b64b632b873e...d1e204f3e6670' == '6fa12a997205...ad6996101db7f'`
- **Commits:**
  - `73c0222c2` [pin] test: pin that ignored files stay out of tree_hash (1 files)

### Cycle 3: editing an untracked, non-ignored file changes the tree hash  _(pin)_
- **Target:** `tddcli::tests/test_tree_hash.py::test_editing_an_untracked_file_changes_the_hash`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert '315aecb2a85652eb190e6598b51fd09ae3f3a146e78f24507dd2ac3c405e1791' != '315aecb2a85652eb190e6598b51fd09ae3f3a146e78f24507dd2ac3c405e1791'`
- **Commits:**
  - `0f27099af` [pin] test: pin that untracked file content is part of tree_hash (1 files)

### Cycle 2: deleting a tracked file changes the tree hash  _(pin)_
- **Target:** `tddcli::tests/test_tree_hash.py::test_deleting_a_tracked_file_changes_the_hash`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert '6fa12a9972059ab222b1e48f9fbe70571560ed512758cbf2430ad6996101db7f' != '6fa12a9972059ab222b1e48f9fbe70571560ed512758cbf2430ad6996101db7f'`
- **Commits:**
  - `babda8d6d` [pin] test: pin that deleting a tracked file changes tree_hash (1 files)

### Cycle 1: a sweep that skips the cycle's own suites still runs that project's lint/typecheck gates  _(standard)_
- **Target:** `tddcli::tests/test_close_sweep_gates.py::test_skip_own_still_runs_the_cycle_projects_gates`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `fdbb0aa79` [red] test: a close sweep that skips its own suites still runs their gates (1 files)
  - `39226f44b` [green] fix: skip_own drops the cycle's own suites, not its lint/typecheck gates (1 files)

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 8. The plan was right about the throwaway index but wrong about how to seed it: copying the real index with a fresh mtime defeats the racy-clean stat check, so a same-size, same-second edit read as unchanged. It surfaced as an intermittent failure of the cycle's own test, and shutil.copy2 fixed it (0/1000 misses in a stress loop). No regression test pins it yet. Plan got right: the latent skip_own gate bug (cycle 1) and the exact two-test blast radius at cycle 8. Harness friction: the worktree isolation guard refuses heredocs and notes that name the VCS, so edits went through the Edit tool. The run is refereed by 0.12.2, so its own close sweeps still ran every cycle, as the plan said.

