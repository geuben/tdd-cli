# Implementation Friction Log: tasks/issue-185-report-socket.md

- Run: 5
- Executor: claude-opus-5-5 (source: claimed)
- Plan blob: `e0c87150a14bd016b4df612b884ac41eeeef4e14` (declared)
- Started: 2026-10-30T11:57:29.829207+00:00  Ended: 2026-10-30T12:22:25.270416+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 11
- Delivered: 11   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 11: document the report socket, --since and the per-cycle table  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `bb8752bf1` [refactor] docs: the report socket, tdd ledger metrics --since and per-cycle times (3 files)

### Cycle 10: metrics --since refuses a time with no UTC offset  _(standard)_
- **Target:** `tddcli::tests/test_ledger_report_socket.py::test_metrics_since_refuses_a_time_with_no_offset`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `17b817dd8` [red] test: metrics --since refuses a time with no offset (1 files)
  - `3e749cde5` [green] feat: metrics refuses a bad since with bad_since (1 files)

### Cycle 9: metrics --since keeps the runs still open or ended since then, on both sockets  _(standard)_
- **Target:** `tddcli::tests/test_ledger_report_socket.py::test_metrics_since_keeps_runs_open_or_ended_since_then`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `620dc4e4a` [red] test: metrics --since keeps runs open or ended since then (2 files)
  - `bf75d317e` [green] feat: tdd ledger metrics --since (3 files)

### Cycle 8: metrics reports each cycle's time  _(standard)_
- **Target:** `tddcli::tests/test_time_report.py::test_metrics_reports_each_cycles_time`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `f0ab1a353` [red] test: metrics reports each cycle's time (1 files)
  - `68bebe857` [green] feat: tdd metrics reports a per-cycle time table (2 files)

### Cycle 7: tdd ledger metrics, fleet and log fall back to the report socket  _(standard)_
- **Target:** `tddcli::tests/test_ledger_report_socket.py::test_ledger_reads_fall_back_to_the_report_socket`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `e590d364d` [red] test: ledger reads fall back to the report socket (1 files)
  - `6b74af7db` [green] feat: tdd ledger metrics, fleet and log fall back to the report socket (1 files)

### Cycle 6: with no report socket, a forbidden admin socket is ledger_unreachable for every read  _(pin)_
- **Target:** `tddcli::tests/test_ledger_admin.py::test_a_forbidden_admin_socket_with_no_report_socket_is_unreachable`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert ['mutated', '...d', 'mutated'] == ['ledger_unre..._unreachable']`
- **Commits:**
  - `e9d3ccefd` [pin] test: pin with no report socket, a forbidden admin socket is ledger_unreachable for every read (1 files)

### Cycle 5: a report socket on the admin socket's path is refused  _(standard)_
- **Target:** `tddcli::tests/test_ledger_report_socket.py::test_a_report_socket_on_the_admin_path_is_refused`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `2372ef649` [red] test: a report socket on the admin path is refused (1 files)
  - `40f0fce3f` [green] feat: report_socket must not be admin_socket (1 files)

### Cycle 4: the report socket is mode 660  _(standard)_
- **Target:** `tddcli::tests/test_ledger_report_socket.py::test_the_report_socket_is_mode_660`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `e7764e076` [red] test: the report socket is mode 660 (1 files)
  - `d1def3c87` [green] feat: the report socket is mode 660, like a source's (1 files)
  - `90d651e21` [refactor] refactor: tidy socket modes (1 files)

### Cycle 3: the report socket reads ledgers it could not write  _(standard)_
- **Target:** `tddcli::tests/test_ledger_report_socket.py::test_the_report_socket_reads_ledgers_it_cannot_write`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `3b4131be7` [red] test: the report socket reads a ledger it cannot write (1 files)
  - `a5185cbac` [green] feat: the report socket opens ledgers read-only (1 files)

### Cycle 2: the report socket refuses every other method  _(standard)_
- **Target:** `tddcli::tests/test_ledger_report_socket.py::test_the_report_socket_refuses_every_other_method`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `f6bb457f6` [red] test: the report socket refuses every other method (1 files)
  - `e39d731e9` [green] feat: the report socket answers metrics, fleet and log alone (1 files)
  - `1b8735946` [refactor] refactor: tidy report socket dispatch (1 files)

### Cycle 1: the report socket answers metrics, fleet and log as the admin socket does  _(standard)_
- **Target:** `tddcli::tests/test_ledger_report_socket.py::test_the_report_socket_answers_as_the_admin_socket_does`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `c45810e73` [red] test: the report socket answers metrics, fleet and log (1 files)
  - `9538d768f` [green] feat: the ledger service listens on an optional report socket (1 files)
  - `1f1c72b8d` [refactor] refactor: tidy the report listener (1 files)

## Time

- Wall clock: 24.9 min. Suite: 21.1 min (85%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 9 | 0.2 | 1.5 |
| AWAITING_PIN | 1 | 0.0 | 1.5 |
| SENSITIVITY | 1 | 0.0 | 1.3 |
| AWAITING_IMPL | 18 | 13.4 | 44.8 |
| CLOSE_SWEEP | 5 | 7.4 | 88.9 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 3.7 | 3.0 | 4 |
| 2 | 3.4 | 3.0 | 4 |
| 3 | 1.8 | 1.5 | 3 |
| 4 | 3.2 | 3.0 | 4 |
| 5 | 1.7 | 1.5 | 3 |
| 6 | 1.9 | 1.5 | 3 |
| 7 | 1.8 | 1.5 | 3 |
| 8 | 1.9 | 1.5 | 3 |
| 9 | 2.0 | 1.5 | 3 |
| 10 | 1.8 | 1.5 | 3 |
| 11 | 1.8 | 1.5 | 1 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 3 (read-only open) — a shared _view helper had to keep the admin path migrating while the report path uses open_readonly. Plan got wrong: nothing; every expected failure matched as written, and cycle 9's declared argparse stub went in with the RED commit. #179's bind_socket was not in ServiceConfig at run start, so cycle 5 compares report_socket with admin_socket only. Harness friction: tdd run start needed tdd plan register first; ruff format of the new test file fell to cycle 1's refactor.

