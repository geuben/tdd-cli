# Implementation Friction Log: tasks/issue-231-commit-keys-per-cycle-kind.md

- Run: 15
- Executor: claude-opus-5-5 (source: claimed)
- Plan blob: `b92386b2d6a42772f2bb5348a1fdba41b6f44eb3` (declared)
- Started: 2026-11-01T11:26:04.621462+00:00  Ended: 2026-11-01T11:41:25.324084+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 5
- Delivered: 5   Skipped: 0
- Never reached: none
- Unblocks: 0

### Cycle 5: the default pin message drops a leading pin from the title  _(standard)_
- **Target:** `tddcli::tests/test_config_and_staging.py::test_the_default_pin_message_drops_a_leading_pin_from_the_title`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `bc5e0e314` [red] test: the default pin message must not double a leading pin (1 files)
  - `b93ded89f` [green] fix(staging): drop a leading pin from the title in the default pin message (4 files)

### Cycle 4: a pin message is left alone unless its default title leads with the word pin  _(pin)_
- **Target:** `tddcli::tests/test_config_and_staging.py::test_a_pin_message_is_left_alone_unless_its_default_title_leads_with_the_word_pin`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert ['test: pin: ...n: pin:', ...] == ['test: pin p...in pin:', ...]`
- **Commits:**
  - `7d3b94b99` [pin] test: pin the commit messages the pin-prefix strip must not touch (1 files)

### Cycle 3: plan register refuses a pin cycle that declares commit_red  _(pin)_
- **Target:** `tddcli::tests/test_pin_cycles.py::test_plan_register_refuses_a_pin_cycle_that_declares_commit_red`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert (True, None) == (False, 'malf... commit_pin.')`
- **Commits:**
  - `294bcf730` [pin] test: pin that plan register refuses commit_red on a pin cycle (1 files)
> **note** _(during SENSITIVITY_REQUIRED)_: cycle 3: first sensitivity mutation (commenting out the raise) left a syntax error, so its failure was an import error, not the assertion; re-ran sensitivity with 'if False and ...' guarding the refusal, which fails the assertion (True, None) == (False, ...) as intended.

### Cycle 2: a commit key for a phase the cycle kind never enters is refused  _(standard)_
- **Target:** `tddcli::tests/test_contract.py::test_a_commit_key_for_a_phase_the_cycle_kind_never_enters_is_refused`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `705015e3a` [red] test: a commit key the cycle kind never commits under must be refused (1 files)
  - `8dfd4127b` [green] fix(contract): refuse a commit key for a phase the cycle kind never enters (5 files)

### Cycle 1: every commit key a cycle kind commits under is kept  _(pin)_
- **Target:** `tddcli::tests/test_contract.py::test_every_commit_key_a_cycle_kind_commits_under_is_kept`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `AssertionError: assert {1: {'red': '...: 'p'}, 4: {}} == {1: {'red': '...factor': 'f'}}`
- **Commits:**
  - `4429e99bf` [pin] test: pin the commit keys each cycle kind commits under (1 files)

## Time

- Wall clock: 15.3 min. Suite: 12.8 min (83%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 2 | 0.0 | 0.9 |
| AWAITING_PIN | 3 | 0.1 | 1.3 |
| SENSITIVITY | 4 | 0.1 | 1.0 |
| AWAITING_IMPL | 4 | 5.3 | 78.9 |
| CLOSE_SWEEP | 3 | 7.4 | 147.3 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 2.7 | 2.4 | 3 |
| 2 | 3.8 | 2.8 | 3 |
| 3 | 3.1 | 2.6 | 4 |
| 4 | 2.7 | 2.5 | 3 |
| 5 | 3.1 | 2.4 | 3 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 5, the pin-prefix regex: beyond the plan's footgun (try '-' before bare whitespace), the bare-whitespace branch also needs a lookahead excluding ':' and '-' or 'pin  -' with nothing after gets stripped to '-'; per-branch lookaheads handle it. plan got wrong: nothing material; its probes (11 test_suite_scope failures, expected messages) matched exactly. harness friction: cycle 3's first sensitivity mutation was a syntax-breaking comment-out that 'bit' via an import error; redone with a guard mutation.

