# Implementation Friction Log: tasks/issue-68-sensitivity-evidence.md

- Run: 12
- Executor: claude-sonnet-4-6 (source: transcript)
- Plan blob: `34ede538eab3a01b75b9d9cdfde5c86000318fe0` (declared)
- Started: 2026-08-28T16:04:38.652188+00:00  Ended: 2026-08-28T17:21:10.569424+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 11
- Delivered: 11   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 11: a long observed line is capped keeping the tail, not the head  _(standard)_
- **Target:** `tddcli::tests/test_sensitivity_evidence.py::test_long_evidence_is_capped_keeping_the_tail`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `e6d5235ad` [red] test: an over-long observed line keeps its tail (1 files)
  - `146e15314` [green] feat: tail-keeping cap on the observed evidence line (1 files)

### Cycle 10: legacy rows with NULL evidence keep the first-line fallback  _(standard)_
- **Target:** `tddcli::tests/test_sensitivity_evidence.py::test_null_evidence_falls_back_to_first_observed_line`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (**passed**)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `repo = PosixPath('/private/var/folders/zl/3010c_557g5_2rm9tyqsc03h0000gp/T/pytest-of-headless-coding/pytest-239/test_null_evidence_falls_back_0/workspace')`
- **Commits:**
  - `a7004cc9f` [refactor] refactor: legacy rows with NULL evidence keep the first-line fallback (1 files)
- **Event — red_first_violation:** ["tddcli::tests/test_sensitivity_evidence.py::test_null_evidence_falls_back_to_first_observed_line"]

### Cycle 9: empty evidence renders an explicit no-assertion-line sentinel  _(standard)_
- **Target:** `tddcli::tests/test_sensitivity_evidence.py::test_empty_evidence_renders_the_sentinel`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `8e68e09f0` [red] test: empty evidence renders <no assertion line captured> (1 files)
  - `8e0308820` [green] feat: render the no-assertion-line sentinel instead of wire noise (1 files)

### Cycle 8: friction log observed line renders the stored evidence line  _(standard)_
- **Target:** `tddcli::tests/test_sensitivity_evidence.py::test_friction_log_observed_line_is_the_evidence_line`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `b2dc16f52` [red] test: observed line shows evidence_line, not the raw first line (1 files)
  - `ddc60246f` [green] feat: friction log prefers evidence_line for the observed snippet (1 files)

### Cycle 7: sensitivity check stores the adapter's evidence line in the ledger  _(standard)_
- **Target:** `tddcli::tests/test_sensitivity_evidence.py::test_sensitivity_check_records_the_evidence_line`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `53ad9734d` [red] test: sensitivity check persists evidence_line on its ledger row (1 files)
  - `619c0bd3d` [green] feat: schema v7 — sensitivity_check.evidence_line stored at check time (2 files)
  - `739ed8a0f` [refactor] refactor: sensitivity check stores the adapter's evidence line in the ledger (1 files)

### Cycle 6: exec evidence falls back to the last non-empty output line  _(standard)_
- **Target:** `tddcli::tests/test_evidence_extraction.py::test_exec_evidence_is_the_last_nonempty_output_line`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `1df55d55d` [red] test: exec evidence is the last non-empty combined-output line (1 files)
  - `78771ff01` [green] feat: exec evidence falls back to the last non-empty line (1 files)
  - `9012b32fe` [refactor] refactor: exec evidence falls back to the last non-empty output line (1 files)

### Cycle 5: gradle evidence is the first line of the junit failure message  _(standard)_
- **Target:** `tddcli::tests/test_evidence_extraction.py::test_gradle_evidence_is_the_first_failure_message_line`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `e0a5301d1` [red] test: gradle evidence is the junit failure message line (1 files)
  - `bebee75f9` [green] feat: gradle evidence extracted from the failure element's message (1 files)

### Cycle 4: vitest evidence is the first line of the first failure message  _(standard)_
- **Target:** `tddcli::tests/test_evidence_extraction.py::test_vitest_evidence_is_the_first_failure_message_line`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `3c0c01982` [red] test: vitest evidence is the first failureMessage line (1 files)
  - `248e55040` [green] feat: vitest evidence extracted from failureMessages[0] (1 files)

### Cycle 3: xctest evidence is the error line, not interleaved console noise  _(standard)_
- **Target:** `tddcli::tests/test_evidence_extraction.py::test_xctest_evidence_is_the_error_line_not_console_noise`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `e04e0098a` [red] test: xctest evidence line ignores console noise in the test window (1 files)
  - `5817c6ab2` [green] feat: xctest evidence is the first ': error:' line of the test's window (1 files)
  - `1f1b40b52` [refactor] refactor: xctest evidence is the error line, not interleaved console noise (1 files)

### Cycle 2: pytest evidence is empty when longrepr has no assertion line  _(pin)_
- **Target:** `tddcli::tests/test_evidence_extraction.py::test_pytest_evidence_is_empty_when_no_assertion_line_exists`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `tmp_path = PosixPath('/private/var/folders/zl/3010c_557g5_2rm9tyqsc03h0000gp/T/pytest-of-headless-coding/pytest-162/test_pytest_evidence_is_empty_0')`
- **Commits:**
  - `dad64c656` [pin] test: pin empty pytest evidence when no E-line exists (1 files)

### Cycle 1: pytest evidence is the assertion line, not the xdist worker header  _(standard)_
- **Target:** `tddcli::tests/test_evidence_extraction.py::test_pytest_evidence_is_the_assertion_line_not_the_xdist_header`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 2, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `a4be0c744` [red] test: pytest evidence line skips the xdist worker header (1 files)
  - `a2b7ecb47` [green] feat: Verdict.target_evidence — pytest extracts the first E-line of longrepr (2 files)
  - `b464cf742` [refactor] refactor: pytest evidence is the assertion line, not the xdist worker header (1 files)

