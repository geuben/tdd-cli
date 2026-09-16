# Implementation Friction Log: tasks/issue-115-stale-baseline-claim.md

- Run: 20
- Executor: claude-sonnet-4-6 (source: transcript)
- Plan blob: `b5622e337187a9846d50ec07dc9c4ecb45d257f6` (declared)
- Started: 2026-09-09T13:24:58.772320+00:00  Ended: 2026-09-09T13:46:14.318648+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 5
- Delivered: 5   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 5: document the stale-claim reply across every verb table that claims await_baseline is unconditional  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `9425cfa19` [refactor] docs: a dead baseline collector no longer replies await_baseline (5 files)
> **note** _(during AWAITING_REFACTOR)_: hardest cycle: cycle 3 (pin) — had to decide what 'agree' meant for progress/status on a stale claim; chose to surface liveness in the shared _collecting_envelope seam so the refactor in AWAITING_REFACTOR simplified cmd_status. Plan got right: the one-seam refactor was a natural consequence of the prior cycles. No harness friction: all advances clean.

### Cycle 4: bare progress names the dead collector and the command that clears it  _(standard)_
- **Target:** `tddcli::tests/test_progress.py::test_bare_progress_names_the_dead_collector_and_the_recovery_command`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `103ec16cc` [red] test: bare progress names the dead collector (1 files)
  - `c64e6586c` [green] feat: bare progress reports a dead baseline collector (1 files)

### Cycle 3: progress --json and status agree on a stale claim — one seam, two commands  _(pin)_
- **Target:** `tddcli::tests/test_progress.py::test_progress_json_and_status_agree_on_a_stale_claim`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert False is True`
- **Commits:**
  - `cc548eb33` [pin] test: pin progress --json and status agree on a stale claim — one seam, two commands (1 files)
  - `5eadddf2d` [refactor] refactor: progress --json and status agree on a stale claim — one seam, two commands (1 files)

### Cycle 2: the collecting_baseline result body reports the claim's liveness and owner pid  _(standard)_
- **Target:** `tddcli::tests/test_progress.py::test_collecting_baseline_result_reports_claim_liveness`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `18dd5617a` [red] test: collecting_baseline body carries stale and pid (1 files)
  - `4a0411c50` [green] feat: surface stale and pid in the collecting_baseline result (1 files)

### Cycle 1: status on a stale baseline claim replies confirm_cycle_applicable, not await_baseline  _(standard)_
- **Target:** `tddcli::tests/test_progress.py::test_status_on_a_stale_claim_does_not_tell_the_agent_to_wait`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `e04c2612f` [red] test: status on a dead baseline collector must not reply await_baseline (1 files)
  - `3042f05ce` [green] fix: a stale baseline claim replies confirm_cycle_applicable (1 files)

