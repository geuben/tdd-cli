# Implementation Friction Log: tasks/issue-179-bind-socket-and-unbind.md

- Run: 3
- Executor: claude-opus-5-5 (source: claimed)
- Plan blob: `62dcc782186c265301abef6661714f10030e98ee` (declared)
- Started: 2026-10-30T10:44:04.823340+00:00  Ended: 2026-10-30T11:13:48.082048+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 15
- Delivered: 15   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 15: document the bind socket and unbind  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `99ca60010` [refactor] docs: the bind socket and tdd ledger unbind (3 files)

### Cycle 14: bind and unbind fall back to the bind socket when the admin socket cannot be opened  _(standard)_
- **Target:** `tddcli::tests/test_ledger_bind_socket.py::test_bind_and_unbind_fall_back_to_the_bind_socket`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `3d78d6768` [red] test: bind and unbind fall back to the bind socket (1 files)
  - `e54ad179c` [green] feat: bind and unbind fall back to the bind socket (1 files)

### Cycle 13: with no bind socket, an admin socket the caller cannot open is ledger_unreachable  _(pin)_
- **Target:** `tddcli::tests/test_ledger_admin.py::test_a_forbidden_admin_socket_with_no_bind_socket_is_unreachable`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert None == 'ledger_unreachable'`
- **Commits:**
  - `6c1424ff0` [pin] test: pin with no bind socket, an admin socket the caller cannot open is ledger_unreachable (1 files)

### Cycle 12: bind and unbind use an explicit --socket  _(standard)_
- **Target:** `tddcli::tests/test_ledger_bind_socket.py::test_bind_and_unbind_use_an_explicit_socket`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `f9293a6f8` [red] test: bind and unbind honour --socket (1 files)
  - `dda77314d` [green] feat: tdd ledger bind and unbind take --socket (1 files)
> **note** _(during AWAITING_IMPL)_: cycle 12: as in cycle 1, RED was accepted on argparse's exit (unrecognized --socket) with no create_stub directive; the flag and its use land together at GREEN

### Cycle 11: a bind_group that does not exist is refused when the config loads  _(standard)_
- **Target:** `tddcli::tests/test_ledger_bind_socket.py::test_a_bind_group_that_does_not_exist_is_refused`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `e2441aaad` [red] test: an unknown bind_group is refused (1 files)
  - `6923028ef` [green] feat: the service config refuses an unknown bind_group (1 files)

### Cycle 10: a half or clashing bind config is refused  _(standard)_
- **Target:** `tddcli::tests/test_ledger_bind_socket.py::test_a_half_or_clashing_bind_config_is_refused`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `ffe2d3adc` [red] test: a half or clashing bind config is refused (1 files)
  - `5644c9aab` [green] feat: bind_socket and bind_group go together, apart from admin_socket (1 files)

### Cycle 9: the bind socket is mode 660 and belongs to bind_group  _(standard)_
- **Target:** `tddcli::tests/test_ledger_bind_socket.py::test_the_bind_socket_belongs_to_its_group`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `3bded77d6` [red] test: the bind socket belongs to its group (1 files)
  - `4113bdd4b` [green] feat: the bind socket is mode 660, owned by bind_group (1 files)

### Cycle 8: the bind socket keeps the admin socket's refusals for bind and unbind  _(pin)_
- **Target:** `tddcli::tests/test_ledger_bind_socket.py::test_the_bind_socket_keeps_the_admin_refusals`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert ['unknown_sou...source', 'ok'] == ['unknown_sou...bad_executor']`
- **Commits:**
  - `4520cb4ed` [pin] test: pin the bind socket keeps the admin socket's refusals for bind and unbind (1 files)

### Cycle 7: the bind socket answers unbind  _(standard)_
- **Target:** `tddcli::tests/test_ledger_bind_socket.py::test_the_bind_socket_unbinds_a_source`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `2265c871e` [red] test: the bind socket unbinds a source (1 files)
  - `21fcb6540` [green] feat: the bind socket answers unbind (1 files)

### Cycle 6: the bind socket refuses every method but bind  _(standard)_
- **Target:** `tddcli::tests/test_ledger_bind_socket.py::test_the_bind_socket_refuses_every_other_method`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `a0289275e` [red] test: the bind socket refuses every other method (1 files)
  - `61108193a` [green] feat: the bind socket answers bind alone (1 files)

### Cycle 5: a configured bind socket answers bind  _(standard)_
- **Target:** `tddcli::tests/test_ledger_bind_socket.py::test_the_bind_socket_binds_a_source`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `2f9f38aac` [red] test: the bind socket binds a source (1 files)
  - `a945f1ac7` [green] feat: the ledger service listens on an optional bind socket (1 files)
  - `1d5bc8b50` [refactor] refactor: tidy the bind listener (1 files)

### Cycle 4: bind refuses an empty or blank executor  _(standard)_
- **Target:** `tddcli::tests/test_ledger_admin.py::test_bind_refuses_an_empty_executor`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `b14ab5d3e` [red] test: bind refuses an empty executor (1 files)
  - `c9d8d6b43` [green] fix: bind refuses an empty executor with bad_executor (1 files)

### Cycle 3: unbind refuses a source that does not exist  _(standard)_
- **Target:** `tddcli::tests/test_ledger_admin.py::test_unbind_refuses_an_unknown_source`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `62c992bf3` [red] test: unbind refuses an unknown source (1 files)
  - `78c6241df` [green] feat: unbind refuses an unknown source (1 files)

### Cycle 2: an unbinding survives a service restart  _(standard)_
- **Target:** `tddcli::tests/test_ledger_admin.py::test_an_unbinding_survives_a_service_restart`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `8660e705d` [red] test: an unbinding survives a restart (1 files)
  - `f121ca06b` [green] feat: the service persists an unbinding (1 files)

### Cycle 1: tdd ledger unbind returns a source's next runs to the guest's claim  _(standard)_
- **Target:** `tddcli::tests/test_ledger_service.py::test_unbind_returns_a_source_to_the_guests_claim`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `1a3f75f9d` [red] test: unbind returns a source to the guest's claim (1 files)
  - `a4b7b280f` [green] feat: tdd ledger unbind clears a source's executor binding (2 files)
  - `b886106ce` [refactor] refactor: tidy unbind (1 files)
> **note** _(during AWAITING_IMPL)_: cycle 1: RED was accepted on the argparse JSONDecodeError without a create_stub directive; the stub and implementation go in together at GREEN

## Time

- Wall clock: 29.7 min. Suite: 26.2 min (88%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 12 | 0.4 | 1.9 |
| AWAITING_PIN | 2 | 0.1 | 1.6 |
| SENSITIVITY | 2 | 0.1 | 1.8 |
| AWAITING_IMPL | 24 | 18.2 | 45.6 |
| CLOSE_SWEEP | 5 | 7.5 | 90.3 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 3.5 | 3.1 | 4 |
| 2 | 1.8 | 1.6 | 3 |
| 3 | 1.7 | 1.5 | 3 |
| 4 | 1.7 | 1.5 | 3 |
| 5 | 3.3 | 3.0 | 4 |
| 6 | 1.8 | 1.6 | 3 |
| 7 | 1.7 | 1.6 | 3 |
| 8 | 1.8 | 1.6 | 3 |
| 9 | 1.9 | 1.6 | 3 |
| 10 | 1.6 | 1.5 | 3 |
| 11 | 1.7 | 1.5 | 3 |
| 12 | 1.8 | 1.5 | 3 |
| 13 | 1.8 | 1.6 | 3 |
| 14 | 1.8 | 1.6 | 3 |
| 15 | 1.8 | 1.5 | 1 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 14, the connect-time fallback, because it needs wire.Connection directly to tell a failed connect from a failed request; plan got wrong: cycles 1 and 12 declared stub_expected but the tool accepted the argparse JSONDecodeError as RED with no create_stub directive, so stub and implementation landed together at GREEN; also cycle 4's GREEN closed before ruff format ran, fixed in cycle 5's refactor; harness friction: none beyond that

