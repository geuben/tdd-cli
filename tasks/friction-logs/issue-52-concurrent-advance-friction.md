# Implementation Friction Log: tasks/issue-52-concurrent-advance.md

- Run: 2
- Executor: claude-sonnet-4-6 (source: transcript)
- Plan blob: `75870ac29f8a9f7d031966569dc21fdbdf0f3ba8` (declared)
- Started: 2026-08-23T12:53:25.825496+00:00  Ended: 2026-08-23T13:33:20.894530+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 6
- Delivered: 6   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 6: the advance claim is released when the handler raises  _(standard)_
- **Target:** `tddcli::tests/test_concurrent_advance.py::test_advance_releases_its_claim_when_the_handler_raises`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `da8fecc1d` [red] test: a raising advance must not leave its claim behind (1 files)
  - `289d94a75` [green] fix: release the advance claim in a finally (1 files)

### Cycle 5: a dead holder's advance claim is reclaimed  _(standard)_
- **Target:** `tddcli::tests/test_concurrent_advance.py::test_a_dead_advance_claim_is_reclaimed`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `b9e50e3fc` [red] test: an advance claim held by a dead pid (1 files)
  - `00f6a6d61` [green] fix: reclaim a stale advance claim (2 files)
  - `e09543da1` [refactor] refactor: one staleness rule shared by both claim kinds (1 files)
  - `76db57279` [refactor] refactor: one staleness rule shared by both claim kinds (1 files)

### Cycle 4: the refusal tells the agent to wait rather than kill or re-run  _(standard)_
- **Target:** `tddcli::tests/test_concurrent_advance.py::test_advance_in_flight_directs_the_agent_to_wait`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `8af2eac80` [red] test: advance_in_flight refusal names elapsed, status, and do-not-re-run (1 files)
  - `86cd9e7d4` [green] feat: advance_in_flight reports pid, elapsed and the wait instruction (1 files)

### Cycle 3: a second advance is refused while one is in flight  _(standard)_
- **Target:** `tddcli::tests/test_concurrent_advance.py::test_advance_is_rejected_while_another_advance_is_in_flight`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `e5f8fdb8c` [red] test: a second advance while one is in flight (1 files)
  - `5b24a83b3` [green] feat: advance_claim table and an advance_in_flight refusal (2 files)

### Cycle 2: open_cycle returns the existing open row for an ordinal instead of inserting a duplicate  _(standard)_
- **Target:** `tddcli::tests/test_concurrent_advance.py::test_open_cycle_returns_the_existing_open_row_for_an_ordinal`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `a2587ffdf` [red] test: open_cycle called twice for one ordinal (1 files)
  - `8ed0ca231` [green] fix: open_cycle returns the existing open row for an ordinal (1 files)

### Cycle 1: close_cycle is a no-op when the ledger says the row is already closed  _(standard)_
- **Target:** `tddcli::tests/test_concurrent_advance.py::test_close_cycle_is_idempotent_when_the_row_is_already_closed`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `be2e34efd` [red] test: close_cycle called twice on one cycle row (1 files)
  - `4fbef2b1b` [green] fix: close_cycle re-reads closed_at and no-ops on an already-closed row (1 files)
  - `d5c755c13` [refactor] refactor: close_cycle is a no-op when the ledger says the row is already closed (1 files)

