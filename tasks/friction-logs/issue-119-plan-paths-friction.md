# Implementation Friction Log: tasks/issue-119-plan-paths.md

- Run: 21
- Executor: claude-sonnet-4-6 (source: transcript)
- Plan blob: `811cd785d919380b05923c86a8c8c81b204cd8b5` (declared)
- Started: 2026-09-16T08:52:39.653711+00:00  Ended: 2026-09-16T09:47:17.676931+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 15
- Delivered: 15   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 15: the bare command emits no JSON envelope alongside the table  _(pin)_
- **Target:** `tddcli::tests/test_plan_paths.py::test_the_bare_command_emits_no_json_envelope`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `assert 'envelope_version' not in 'cycle  fiel... 2\n  }\n}\n'`
- **Commits:**
  - `a24271e35` [pin] test: pin that the rendered table is not followed by an envelope (1 files)
- **Event — target_named_by_agent:** tddcli::tests/test_plan_paths.py::test_the_bare_command_emits_no_json_envelope

### Cycle 14: the bare command renders a human table  _(standard)_
- **Target:** `tddcli::tests/test_plan_paths.py::test_the_bare_command_renders_a_human_table`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 6, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** not_found (**not_found**)
- **Commits:**
  - `7ce2268f7` [red] test: bare plan paths renders a human table (1 files)
  - `59b30c4ee` [green] feat: human table for plan paths; --json selects the envelope (2 files)
- **Event — multiple_new_tests:** ["tddcli::tests/test_plan_paths.py::test_a_cargo_integration_test_id_resolves_under_the_project_root", "tddcli::tests/test_plan_paths.py::test_a_cargo_lib_id_is_unresolved_with_no_path_in_id", "tddcli::tests/test_plan_paths.py::test_a_gradle_id_resolves_through_the_source_scan", "tddcli::tests/test_
- **Event — target_named_by_agent:** tddcli::tests/test_plan_paths.py::test_the_bare_command_renders_a_human_table

### Cycle 13: a plan that cannot be turned into a contract refuses cleanly  _(standard)_
- **Target:** `tddcli::tests/test_plan_paths.py::test_a_plan_that_is_not_a_contract_refuses_cleanly`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (**passed**)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `tddcli.contract.ContractError: cycle 1: unknown project 'nosuch'; registered: ['backend']`
- **Commits:**
  - `0b5a4686d` [refactor] refactor: a plan that cannot be turned into a contract refuses cleanly (1 files)
- **Event — red_first_violation:** ["tddcli::tests/test_plan_paths.py::test_a_plan_that_is_not_a_contract_refuses_cleanly"]
> **note** _(during SENSITIVITY_REQUIRED)_: cycle 1 GREEN included the OSError and ContractError handlers in cmd_plan_paths; the plan specifies these as cycle 13 minimal GREEN. Sensitivity confirms the test is sensitive to the refusal handlers.

### Cycle 12: a scan that does not match exactly one file says why  _(standard)_
- **Target:** `tddcli::tests/test_plan_paths.py::test_a_scan_that_matches_other_than_one_file_says_why`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `4c138f35d` [red] test: not_found_in_sources and ambiguous_id reasons (1 files)
  - `026bfe8ce` [green] feat: distinguish a missed scan from an ambiguous one (5 files)
> **note** _(during AWAITING_IMPL)_: cycle 12 GREEN modifies base.py, gradle_adapter.py, xctest_adapter.py (undeclared in cycle 12 files list) because ambiguity detection requires scan_target_paths to return dict[str, list[str]] instead of dict[str, str]. The plan's files list for cycle 12 is incomplete. Also updating cycle 9 and 10 test assertions to expect list values.

### Cycle 11: the resolver consults the source scan when the adapter's target_path is None  _(standard)_
- **Target:** `tddcli::tests/test_plan_paths.py::test_a_gradle_id_resolves_through_the_source_scan`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `e77a4570e` [red] test: a gradle id in a plan resolves through the source scan (1 files)
  - `64fe49b98` [green] feat: fall back to the adapter's source scan, cached per project (1 files)

### Cycle 10: the xctest adapter resolves an id to its Swift source file by scanning sources  _(standard)_
- **Target:** `tddcli::tests/test_plan_paths.py::test_xctest_scans_sources_to_map_an_id_to_its_file`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `8de3eba3f` [red] test: xctest maps a declared id to its Swift source file (1 files)
  - `77febe157` [green] feat: xctest scan_target_paths over the Swift source grep (1 files)

### Cycle 9: the gradle adapter resolves an id to its Kotlin source file by scanning sources  _(standard)_
- **Target:** `tddcli::tests/test_plan_paths.py::test_gradle_scans_sources_to_map_an_id_to_its_file`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `2cc01b40a` [red] test: gradle maps a declared id to its Kotlin source file (1 files)
  - `2f8db34b6` [green] feat: Adapter.scan_target_paths, implemented for gradle (2 files)
  - `a8872d407` [refactor] refactor: the gradle adapter resolves an id to its Kotlin source file by scanning sources (1 files)

### Cycle 8: a refactor cycle's modifies_tests are resolved although it declares no test  _(pin)_
- **Target:** `tddcli::tests/test_plan_paths.py::test_a_refactor_cycles_modifies_tests_are_resolved`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `assert 0 == 1`
- **Commits:**
  - `b13db9de4` [pin] test: pin modifies_tests resolution on a testless refactor cycle (1 files)

### Cycle 7: a cargo integration-test id resolves under the project root  _(pin)_
- **Target:** `tddcli::tests/test_plan_paths.py::test_a_cargo_integration_test_id_resolves_under_the_project_root`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert 'tests/adapte...st_catalog.rs' == 'crates/dd-br...st_catalog.rs'`
- **Commits:**
  - `e621830d2` [pin] test: pin cargo tests/<stem>.rs resolution under a nested root (1 files)

### Cycle 6: unresolved ids do not fail the command  _(pin)_
- **Target:** `tddcli::tests/test_plan_paths.py::test_unresolved_ids_do_not_fail_the_command`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `assert False is True`
- **Commits:**
  - `4964246e3` [pin] test: pin exit 0 when some ids are unresolved (1 files)

### Cycle 5: a cargo lib:: id is reported unresolved with reason no_path_in_id  _(standard)_
- **Target:** `tddcli::tests/test_plan_paths.py::test_a_cargo_lib_id_is_unresolved_with_no_path_in_id`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (**passed**)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `TypeError: join() argument must be str, bytes, or os.PathLike object, not 'NoneType'`
- **Commits:**
  - `837834032` [refactor] refactor: a cargo lib:: id is reported unresolved with reason no_path_in_id (1 files)
- **Event — red_first_violation:** ["tddcli::tests/test_plan_paths.py::test_a_cargo_lib_id_is_unresolved_with_no_path_in_id"]
> **note** _(during SENSITIVITY_REQUIRED)_: cycle 1 GREEN included the None check for target_path and the unresolved list; the plan specifies this as cycle 5 minimal GREEN. Sensitivity confirms the test is sensitive to the None guard.

### Cycle 4: a project root of '.' yields a path with no './' prefix  _(standard)_
- **Target:** `tddcli::tests/test_plan_paths.py::test_a_root_project_yields_an_unprefixed_path`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (**passed**)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert './tests/test_add.py' == 'tests/test_add.py'`
- **Commits:**
  - `906205de0` [refactor] refactor: a project root of '.' yields a path with no './' prefix (1 files)
- **Event — red_first_violation:** ["tddcli::tests/test_plan_paths.py::test_a_root_project_yields_an_unprefixed_path"]
> **note** _(during SENSITIVITY_REQUIRED)_: cycle 1 GREEN included os.path.normpath around the join; the plan specifies this as cycle 4 minimal GREEN, but it was a natural inclusion with the base join logic. Sensitivity confirms the test is sensitive to normpath.

### Cycle 3: every accepted qualification form resolves to the same path  _(pin)_
- **Target:** `tddcli::tests/test_plan_paths.py::test_every_qualification_form_resolves_to_the_same_path`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert ('backend', '.../test_add.py') == ('backend', '.../test_add.py')`
- **Commits:**
  - `231053125` [pin] test: pin the three accepted id qualification forms (1 files)

### Cycle 2: modifies_tests ids are resolved too, labelled with their field  _(standard)_
- **Target:** `tddcli::tests/test_plan_paths.py::test_resolves_modifies_tests_ids_labelled_with_their_field`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (**passed**)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert [] == [{'cycle': 1,...ackend', ...}]`
- **Commits:**
  - `8eb7b0df7` [refactor] refactor: modifies_tests ids are resolved too, labelled with their field (1 files)
- **Event — red_first_violation:** ["tddcli::tests/test_plan_paths.py::test_resolves_modifies_tests_ids_labelled_with_their_field"]
> **note** _(during SENSITIVITY_REQUIRED)_: cycle 1 GREEN walked both cycle.tests and cycle.modifies_tests; the plan specifies minimal GREEN per cycle but modifies_tests iteration was a natural two-liner alongside the test walk, so it landed in cycle 1 instead of cycle 2. Sensitivity check confirms the test is sensitive to the modifies_tests iteration.

### Cycle 1: plan paths resolves a pytest cycle's test id to a repository-relative path  _(standard)_
- **Target:** `tddcli::tests/test_plan_paths.py::test_resolves_a_pytest_target_to_a_repository_path`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `3680267df` [red] test: plan paths resolves a pytest target to a repository path (1 files)
  - `9822f4f8e` [green] feat: tdd plan paths — resolve a plan's test ids to file paths (2 files)
  - `7029efe90` [refactor] refactor: plan paths resolves a pytest cycle's test id to a repository-relative path (1 files)

## Executor narrative

_Claims from the executor, unverified by design._

> Hardest cycle: 1 (over-implemented — added scan fallback, normpath, and error handlers in one shot, causing 6 cycles to pre-pass and need sensitivity checks). Plan inaccuracy: scan_target_paths return type in the plan was dict[str,str], which cannot detect duplicate-id ambiguity; changed to dict[str,list[str]]|None with None meaning adapter has no scan path. Plan also listed only plan_paths.py in cycle 12 files but adapter files needed the change too. Deviation: cycle 15 test was added alongside cycle 14's test then removed to avoid false regression; re-added at the right moment.

