# Implementation Friction Log: tasks/issue-72-adopt-on-first-run.md

- Run: 14
- Executor: claude-sonnet-4-6 (source: transcript)
- Plan blob: `a93211d4ed71c1c73fa1c12447c48495efb0262a` (declared)
- Started: 2026-08-29T07:05:11.715696+00:00  Ended: 2026-08-29T07:46:47.353961+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 6
- Delivered: 6   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 6: genuinely ambiguous new tests still ask the agent  _(pin)_
- **Target:** `tddcli::tests/test_advance_adoption.py::test_ambiguous_new_tests_still_ask_the_agent`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `repo = PosixPath('/private/var/folders/zl/3010c_557g5_2rm9tyqsc03h0000gp/T/pytest-of-headless-coding/pytest-283/test_ambiguous_new_tests_still0/workspace')`
- **Commits:**
  - `d4c0d1e1d` [pin] test: pin that two same-file candidates still demand tdd target (1 files)

### Cycle 5: the unique candidate in the declared file is adopted among several new tests  _(standard)_
- **Target:** `tddcli::tests/test_advance_adoption.py::test_unique_same_file_candidate_is_adopted_and_evaluated`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `537bd6e2a` [red] test: same-file disambiguation adopts and evaluates without asking (1 files)
  - `88cb4d3cf` [green] feat: wire _disambiguate into the multiple-new-tests branch (same-file rule) (1 files)

### Cycle 4: disambiguation picks the candidate that normalise-matches the declared id  _(standard)_
- **Target:** `tddcli::tests/test_advance_adoption.py::test_disambiguate_picks_the_normalisation_match`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `f9813f282` [red] test: _disambiguate resolves a vitest separator-only mismatch (1 files)
  - `add252586` [green] feat: _disambiguate — unique normalise-equal candidate wins (1 files)
  - `e3c694fd7` [refactor] refactor: disambiguation picks the candidate that normalise-matches the declared id (1 files)

### Cycle 3: a single adopted test that passed drives sensitivity in the same advance  _(standard)_
- **Target:** `tddcli::tests/test_advance_adoption.py::test_adopted_passing_test_demands_sensitivity_in_one_advance`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (**passed**)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `repo = PosixPath('/private/var/folders/zl/3010c_557g5_2rm9tyqsc03h0000gp/T/pytest-of-headless-coding/pytest-262/test_adopted_passing_test_dema0/workspace')`
- **Commits:**
  - `8df5166dc` [refactor] refactor: a single adopted test that passed drives sensitivity in the same advance (1 files)
- **Event — red_first_violation:** ["tddcli::tests/test_advance_adoption.py::test_adopted_passing_test_demands_sensitivity_in_one_advance"]

### Cycle 2: a single adopted test that failed is evaluated as RED in the same advance  _(standard)_
- **Target:** `tddcli::tests/test_advance_adoption.py::test_single_new_test_is_adopted_and_evaluated_in_one_advance`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `e6de7826b` [red] test: adoption of the one new failing test reaches RED without a re-run (1 files)
  - `14aea5202` [green] feat: evaluate the adopted target from the suite run that already happened (2 files)
  - `7eb1bfeb0` [refactor] refactor: a single adopted test that failed is evaluated as RED in the same advance (1 files)

### Cycle 1: outcome lookup returns None for an id absent from every verdict  _(standard)_
- **Target:** `tddcli::tests/test_advance_adoption.py::test_outcome_lookup_returns_none_for_unexecuted_id`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `e24012204` [red] test: verdict outcome lookup admits it cannot judge an unexecuted id (1 files)
  - `e60c9e5e3` [green] feat: _outcome_from_verdicts helper (None when the id never ran) (2 files)
  - `6d97ea080` [refactor] refactor: outcome lookup returns None for an id absent from every verdict (1 files)

