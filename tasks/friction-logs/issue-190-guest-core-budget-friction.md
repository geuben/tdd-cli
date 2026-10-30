# Implementation Friction Log: tasks/issue-190-guest-core-budget.md

- Run: 7
- Executor: claude-opus-5-5 (source: claimed)
- Plan blob: `2ac1963f0e5c178f324eb23adabc5f95175c8b6f` (declared)
- Started: 2026-10-30T13:05:17.490406+00:00  Ended: 2026-10-30T13:15:37.277464+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 6
- Delivered: 6   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 6: document the guest's own core budget  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `68b73cafa` [refactor] docs: a guest caps its worker lease at its own budget (3 files)

### Cycle 5: a core_budget that is not a positive integer is refused  _(standard)_
- **Target:** `tddcli::tests/test_split_config.py::test_a_core_budget_that_is_not_a_positive_integer_is_refused`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `b82f6dd9f` [red] test: a core_budget that is not a positive integer is refused (1 files)
  - `f02fca8c8` [green] feat: runner.toml refuses a core_budget that is not a positive integer (1 files)

### Cycle 4: a guest without sched_getaffinity falls back to os.cpu_count()  _(standard)_
- **Target:** `tddcli::tests/test_remote_leases.py::test_a_guest_without_sched_getaffinity_falls_back_to_cpu_count`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `1ac6f8f60` [red] test: a guest without sched_getaffinity falls back to cpu_count (1 files)
  - `6ba8bffa8` [green] fix: a guest without sched_getaffinity budgets os.cpu_count() (1 files)

### Cycle 3: runner.toml's core_budget is the guest's budget, in place of its affinity  _(standard)_
- **Target:** `tddcli::tests/test_remote_leases.py::test_core_budget_is_the_guests_own_budget`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `fc1c66c51` [red] test: core_budget is the guest's own budget (1 files)
  - `c8fc3af12` [green] feat: a guest runner caps its lease at runner.toml's core_budget (2 files)

### Cycle 2: a guest caps its lease at the CPUs it may run on  _(standard)_
- **Target:** `tddcli::tests/test_remote_leases.py::test_a_guest_caps_its_lease_at_the_cpus_it_may_use`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `a1ee7882e` [red] test: a guest caps its lease at the CPUs it may use (1 files)
  - `bdb3f7f4a` [green] fix: a guest runner caps the service's lease at its own CPU affinity (1 files)

### Cycle 1: a runner that keeps its own ledger ignores core_budget  _(pin)_
- **Target:** `tddcli::tests/test_remote_leases.py::test_core_budget_does_not_cap_a_runner_that_keeps_its_own_ledger`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `assert 2 == 12`
- **Commits:**
  - `b909d25e9` [pin] test: pin a runner that keeps its own ledger ignores core_budget (1 files)

## Time

- Wall clock: 10.3 min. Suite: 9.1 min (88%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 4 | 0.1 | 1.4 |
| AWAITING_PIN | 1 | 0.0 | 0.8 |
| SENSITIVITY | 1 | 0.0 | 0.8 |
| AWAITING_IMPL | 8 | 6.0 | 44.8 |
| CLOSE_SWEEP | 2 | 2.9 | 88.5 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 1.7 | 1.5 | 3 |
| 2 | 1.7 | 1.5 | 3 |
| 3 | 1.9 | 1.5 | 3 |
| 4 | 1.7 | 1.5 | 3 |
| 5 | 1.7 | 1.5 | 3 |
| 6 | 1.7 | 1.5 | 1 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: none was hard; the plan's probed failures matched exactly in cycles 2-5. plan got wrong: nothing material; cycle 3's helper needed a TYPE_CHECKING import of RunnerConfig (leases imports runner lazily). harness friction: none; each GREEN costs ~90s of full-suite sweep.

