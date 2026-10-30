# Implementation Friction Log: tasks/issue-76-scoped-annotation-keys.md

- Run: 9
- Executor: claude-opus-5-5 (source: claimed)
- Plan blob: `59a2a7d5e0c39556a3733e7e69f35679bd3cfca9` (declared)
- Started: 2026-10-30T13:33:24.752476+00:00  Ended: 2026-10-30T13:59:37.894316+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 6
- Delivered: 6   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 6: a plain key warns too when the run delivered no cycle  _(pin)_
- **Target:** `tddcli::tests/test_annotation_scope.py::test_the_friction_log_warns_of_a_plain_key_when_no_cycle_was_delivered`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert ['- Human int...tions: 0', ''] == ['- **Declare...rventions: 0']`
- **Commits:**
  - `be57b3ca1` [pin] test: pin the never-ran warning for plain keys (1 files)

### Cycle 5: the friction log warns of a declared check no delivered cycle carried  _(standard)_
- **Target:** `tddcli::tests/test_annotation_scope.py::test_the_friction_log_warns_of_a_scoped_key_no_delivered_cycle_carried`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `b64ea7100` [red] test: the friction log must warn of a declared check that never ran (1 files)
  - `8364e2c02` [green] feat: the friction log warns when a declared check never ran (4 files)

### Cycle 4: malformed annotation_keys entries hard-fail registration  _(standard)_
- **Target:** `tddcli::tests/test_annotation_scope.py::test_malformed_annotation_key_entries_hard_fail`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `e7e4d983e` [red] test: malformed annotation key entries must hard-fail (1 files)
  - `7a8efdb2a` [green] feat: refuse malformed annotation key scopes at registration (1 files)
  - `9da3aa92d` [refactor] refactor: tidy annotation key validation (1 files)

### Cycle 3: a scoped key is required only on the cycles it applies to  _(standard)_
- **Target:** `tddcli::tests/test_annotation_scope.py::test_a_scoped_key_is_required_only_on_the_cycles_it_applies_to`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `afa986f06` [red] test: a scoped annotation key must not be demanded outside its scope (1 files)
  - `6196ac11b` [green] feat: the close gate demands each annotation key only where it applies (5 files)

### Cycle 2: annotation_keys entries resolve onto the cycles they apply to  _(standard)_
- **Target:** `tddcli::tests/test_annotation_scope.py::test_annotation_keys_resolve_onto_the_cycles_they_apply_to`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `3c3bfea4b` [red] test: scoped annotation keys must resolve onto their cycles (1 files)
  - `abb8f5409` [green] feat: annotation_keys entries may be scoped by applies_to or projects (1 files)
  - `0ab9808c7` [refactor] refactor: tidy annotation key resolution (1 files)

### Cycle 1: a contract stored before scoping still requires every key at close  _(pin)_
- **Target:** `tddcli::tests/test_annotation_scope.py::test_a_contract_stored_before_scoping_still_requires_every_key_at_close`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `KeyError: 'missing_annotations'`
- **Commits:**
  - `905191820` [pin] test: pin the annotation gate for contracts stored before scoping (1 files)

## Time

- Wall clock: 26.2 min. Suite: 18.5 min (71%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 4 | 0.1 | 1.9 |
| AWAITING_PIN | 2 | 0.1 | 2.1 |
| SENSITIVITY | 2 | 0.1 | 2.6 |
| AWAITING_IMPL | 8 | 9.0 | 67.6 |
| CLOSE_SWEEP | 4 | 9.2 | 138.7 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 2.8 | 2.4 | 3 |
| 2 | 5.2 | 4.7 | 4 |
| 3 | 4.8 | 1.8 | 3 |
| 4 | 5.3 | 4.5 | 4 |
| 5 | 5.5 | 2.6 | 3 |
| 6 | 2.8 | 2.6 | 3 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 4, ordering the nine refusals so each REJECTED row trips exactly its own rule (bool-before-int, empty scope before membership). Plan got wrong: nothing material; every probed RED matched verbatim. Deviations: cycle 2 resolved scopes with lambdas, tidied into _in_scope in its refactor; cycle 6 sensitivity mutation excluded the plain key from the warning loop. Harness friction: none; baseline 135 s cold.

