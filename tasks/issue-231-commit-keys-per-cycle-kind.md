---
closes: 231
cycles:
  - n: 1
    project: tddcli
    pin_cycle: true
    title: "every commit key a cycle kind commits under is kept"
    test: "tests/test_contract.py::test_every_commit_key_a_cycle_kind_commits_under_is_kept"
    files: ["src/tddcli/contract.py"]
    commit_pin: "test: pin the commit keys each cycle kind commits under"
  - n: 2
    project: tddcli
    title: "a commit key for a phase the cycle kind never enters is refused"
    test: "tests/test_contract.py::test_a_commit_key_for_a_phase_the_cycle_kind_never_enters_is_refused"
    files: ["src/tddcli/contract.py", "README.md", "docs/PRD.md", "CHANGELOG.md"]
    modifies_tests:
      - "tests/test_suite_scope.py::test_an_adopted_target_is_evaluated_in_the_same_advance"
      - "tests/test_suite_scope.py::test_an_adopted_targets_failure_comes_from_its_own_run"
      - "tests/test_suite_scope.py::test_red_is_not_blocked_by_a_failing_test_elsewhere"
      - "tests/test_suite_scope.py::test_red_records_others_unobserved_and_green_records_them_observed"
      - "tests/test_suite_scope.py::test_a_green_whose_target_still_fails_runs_only_the_target"
      - "tests/test_suite_scope.py::test_a_green_whose_target_passes_then_runs_the_whole_suite"
      - "tests/test_suite_scope.py::test_impl_attempts_count_one_per_green_advance"
      - "tests/test_suite_scope.py::test_impl_attempts_count_every_row_in_a_cycle_recorded_before_target_first_green"
      - "tests/test_suite_scope.py::test_a_pin_is_not_blocked_by_a_failing_test_elsewhere"
      - "tests/test_suite_scope.py::test_a_sensitivity_check_runs_only_the_target"
      - "tests/test_suite_scope.py::test_green_on_an_exec_project_is_blocked_by_a_failing_script_elsewhere"
    commit_red: "test: a commit key the cycle kind never commits under must be refused"
    commit_green: "fix(contract): refuse a commit key for a phase the cycle kind never enters"
    commit_refactor: "refactor(contract): tidy the per-kind commit key check"
  - n: 3
    project: tddcli
    pin_cycle: true
    title: "plan register refuses a pin cycle that declares commit_red"
    test: "tests/test_pin_cycles.py::test_plan_register_refuses_a_pin_cycle_that_declares_commit_red"
    files: ["src/tddcli/cli.py"]
    commit_pin: "test: pin that plan register refuses commit_red on a pin cycle"
  - n: 4
    project: tddcli
    pin_cycle: true
    title: "a pin message is left alone unless its default title leads with the word pin"
    test: "tests/test_config_and_staging.py::test_a_pin_message_is_left_alone_unless_its_default_title_leads_with_the_word_pin"
    files: ["src/tddcli/staging.py"]
    commit_pin: "test: pin the commit messages the pin-prefix strip must not touch"
  - n: 5
    project: tddcli
    title: "the default pin message drops a leading pin from the title"
    test: "tests/test_config_and_staging.py::test_the_default_pin_message_drops_a_leading_pin_from_the_title"
    files: ["src/tddcli/staging.py", "README.md", "docs/PRD.md", "CHANGELOG.md"]
    commit_red: "test: the default pin message must not double a leading pin"
    commit_green: "fix(staging): drop a leading pin from the title in the default pin message"
    commit_refactor: "refactor(staging): tidy the pin-prefix strip"
---

# A commit key a cycle never uses is refused; the default pin message does not double "pin"

## Context

[#231](https://github.com/geuben/tdd-cli/issues/231): `contract.parse_cycle` reads
`commit_red`, `commit_green`, `commit_refactor` and `commit_pin` on every cycle, whatever its
kind, and stores each one it finds in `DeclaredCycle.commit_messages`. A cycle only commits in
the phases its kind has, and `staging.default_message` looks up `commit_messages[phase]` for
that phase alone. So a key for a phase the cycle never enters registers without a word and is
never read. The commit falls back to the default message. The issue's case is a pin cycle whose
message is declared under `commit_red`: it commits as `test: pin {title}`, losing the plan's
scope and issue reference. When the title itself starts with `pin:`, the subject doubles:
`test: pin pin: …`.

The issue asks for:

1. the declared message to be used, or the plan refused at registration — "never silently
   dropped" (its **Expected** section), with a register-time refusal that names the key to use
   as the proposal and an alias of `commit_red` to `commit_pin` as a "plausible alternative";
2. the default pin message to drop a leading `pin`, `pin:` or `pin -` (any case) from the title;
3. a line in the README and PRD saying which keys a pin cycle uses.

There is no investigation report on the issue and no `investigate/issue-231` branch. Every claim
below comes from the planning probes.

### What the planning probes found (run on `origin/main` at `bd57486`)

- **The issue's premise is partly wrong.** A pin cycle runs
  `AWAITING_PIN → SENSITIVITY_REQUIRED → AWAITING_REFACTOR → CLOSED` (the `machine.py` module
  docstring; PRD §6.2), and `advance._handle_refactor` commits with `staging.REFACTOR` for
  every kind. A probe drove a pin cycle declaring `commit_refactor: "refactor(x): pin refactor
  msg"` through pin, sensitivity and a refactor edit. `git log` showed that exact subject. So
  **`commit_refactor` is used on a pin cycle**. Only `commit_red` and `commit_green` are dead
  there. Refusing `commit_refactor` on a pin, as the issue's proposal reads, would refuse a key
  that works.
- **The same silent drop exists for every kind.** A refactor cycle opens straight into
  `AWAITING_REFACTOR` (`machine.OPENING_PHASE`), so its `commit_red`, `commit_green` and
  `commit_pin` are dead. A standard or contract cycle never enters the pin phase, so its
  `commit_pin` is dead.
- **The bug is in this repo's own history.** A scan of every front-matter in `tasks/*.md` and
  `examples/plan.md` found 15 pin cycles declaring `commit_red`, across 9 plans (#107, #110,
  #115, #122, #168, #169, #179, #185, #190). Their issues are all closed, so none of them
  will be registered again. No plan declares a dead key on any other kind, and
  `examples/plan.md` declares none.
- **The doubled prefix, reproduced end to end:** a pin cycle titled `pin: greet says hello`
  with `commit_red` declared committed as `test: pin pin: greet says hello`.
- **Test blast radius:** a throwaway version of decision 1's refusal was run against the full
  suite in a scratch worktree of `origin/main`. Exactly 11 tests failed, all in
  `tests/test_suite_scope.py`. Its shared `PLAN` template declares `commit_red`, `commit_green`
  and `commit_pin` on one cycle, and the file formats it as both a standard and a pin cycle.
  Removing those three lines from the template made the full suite pass again (`869 passed`).
  No test in that file asserts a commit message. The hack was discarded.
- The suite is green at `bd57486` in a fresh worktree: `869 passed`. `uv run ruff check` and
  `uv run mypy` pass. `tdd doctor` reports `healthy: true`.

## Design decisions (locked)

1. **Refuse, do not alias.** A `commit_*` key for a phase the cycle's kind never enters fails
   registration. It is never mapped onto another key.
   *Decided by evidence and by convention.*
   - The issue proposes the refusal, and offers the alias only as an alternative.
   - PRD R7.10 makes malformed front-matter a hard failure because "that signal must surface
     rather than degrade silently". R9.17 promises that the plan's commit message is the one
     committed.
   - `parse_cycle` already refuses a field the kind cannot use rather than reinterpreting it: a
     refactor cycle that declares a test is refused ("Use a pin cycle if…"), not turned into a
     pin.
   - An alias is ambiguous when a pin cycle declares both `commit_red` and `commit_green`, and
     it would make the key's meaning depend on the kind.

2. **The keys each kind may declare** are exactly the phases it commits in:

   | Kind | Accepted keys | Refused keys | Suggested key in the refusal |
   |---|---|---|---|
   | standard | `commit_red`, `commit_green`, `commit_refactor` | `commit_pin` | `commit_red` |
   | contract | `commit_red`, `commit_green`, `commit_refactor` | `commit_pin` | `commit_red` |
   | pin | `commit_pin`, `commit_refactor` | `commit_red`, `commit_green` | `commit_pin` |
   | refactor | `commit_refactor` | `commit_red`, `commit_green`, `commit_pin` | `commit_refactor` |

   The suggested key is the one for the kind's first commit, which is where a misplaced message
   was meant to go. *Decided by evidence:* the phase lists in the `machine.py` module docstring
   and `OPENING_PHASE`, and the probe above showing `commit_refactor` used on a pin. The issue's
   **Expected** ("a declared key is never ignored without a word") covers every kind, not only
   pins. Cycle 1 pins the accepted column, so a GREEN that follows the issue's wording and
   refuses `commit_refactor` on a pin fails.

3. **A dead key is refused even beside a live one.** A pin cycle declaring both `commit_red` and
   `commit_pin` is refused naming `commit_red`. The issue's proposal says "without
   `commit_pin`", but with `commit_pin` present `commit_red` is still dropped without a word,
   which the issue's **Expected** rules out. *Decided by evidence (the issue's Expected).*

4. **The refusal is a `ContractError` raised in `contract.parse_cycle`**, after the existing
   `commits` loop. It is not a `target_lint` finding and gets no new `reason`.
   - `cmd_plan_register` already turns a `ContractError` into
     `failure(f"malformed plan contract: {exc}", plan=rel)`: `ok: false`, the text in `error`,
     `result: {"plan": <path>}`, no `result.reason`. The probe saw exactly that shape.
   - The message is, verbatim:

     ```
     cycle {n}: commit_{key} has no effect on a {kind} cycle, which commits only under {accepted}. Declare the message as commit_{suggested}.
     ```

     - `{kind}` is the `DeclaredCycle.kind` value (`standard`, `contract`, `pin`, `refactor`).
     - `{accepted}` is `commit_red, commit_green and commit_refactor` for standard and contract
       cycles, `commit_pin and commit_refactor` for pin cycles, and `commit_refactor` for
       refactor cycles.
     - `{suggested}` is the table's last column.
   - With more than one dead key, the first is named in the fixed order red, green,
     refactor, pin. That is the order of `parse_cycle`'s existing `for phase_key in (...)`
     loop, **not** the YAML order. Cycle 2's case 7 pins this.
   - A non-string value is refused first, by the existing "must be a string" check.

   *Decided by convention:* `parse_cycle` raises `ContractError` for every rule about which
   fields a kind may carry: exclusive kinds, a refactor cycle's test, one test per non-contract
   cycle, `meta` must be a mapping. `target_lint` is for rules that depend on `tdd.toml` and the
   adapters, which is why `run start` re-runs it. This rule depends only on the front-matter.
   Contracts already in a ledger are loaded through `cycles_from_json`, which does not call
   `parse_cycle`. The issue's "names the key to use" is met by the message.

5. **The default pin message drops a leading word `pin` from the title.** Only in the `PIN`
   entry of `staging.default_message`'s fallback, and only when no `commit_pin` is declared.
   - Matched case-insensitively at the very start of the title: `pin` followed by one of:
     - optional whitespace then `:`;
     - whitespace then `-`;
     - whitespace alone.

     Any whitespace after the separator goes too.
   - It is stripped only when non-whitespace text follows. `pin`, `pin:` and `pin -` on their
     own are left as they are.
   - The word must end there: `pinned …`, `pins …` and the hyphenated `pin-x` are left alone.
   - Exactly one prefix is removed.
   - The RED, GREEN and REFACTOR defaults are untouched, and so is any declared message.

   **Mechanism footgun:** if this is a regex with alternation, try the `-` form before the
   bare-whitespace form. Otherwise `PIN - x` matches the whitespace branch and leaves
   `test: pin - x`. Cycle 5's table includes `PIN - x` so a wrong order fails.
   *Decided by evidence:* the issue lists `pin`, `pin:` and `pin -`, case-insensitive. The
   word-boundary and remainder rules are the conservative reading, chosen so the strip cannot
   eat a title that only starts with the letters `pin`.

6. **Docs move with the behaviour.** In cycle 2, the README's "Per-cycle keys" paragraph gains
   the per-kind rule, `docs/PRD.md` gains R7.10a, and `CHANGELOG.md` gains a `### Fixed` entry.
   In cycle 5, the README and PRD R9.17 gain the default-message rule, and the CHANGELOG gains
   a second entry. The issue's item 3 ("the other commit keys have no effect on a pin cycle")
   becomes "registration refuses them", because of decision 1.
   *Decided by convention* (`.claude/plan-issue.md`; `RELEASING.md`; the #98 plan's docs
   decision). No `SCHEMA_VERSION` bump: no ledger table changes.

7. **This repo's planning note.** `.claude/plan-issue/contract-commit-keys-per-kind.md` is added
   in this plan's PR, not by the run. It tells planners here which keys each kind takes,
   because this repo's own plans got it wrong 15 times.

## Not in scope (not asked for)

- **Rewriting the 9 delivered plans in `tasks/` that declare `commit_red` on a pin.** Their
  issues are closed and their runs are complete. A delivered plan is never registered again
  (#97's `plan_already_delivered`), so the new rule never reads them. Rewriting them would
  change history for nothing.
- **Stripping a doubled type from the RED, GREEN and REFACTOR defaults** (a title
  `test: x` giving `test: test: x`). The issue names only the pin default.
- **Adding the issue reference to default messages.** The issue lists its loss as a
  consequence of the dropped declared message, which decision 1 fixes. It does not ask for
  defaults to carry one.

## Fake/real divergence

None. Cycles 1, 2, 4 and 5 call the real `contract.parse` and `staging.default_message`.
Cycle 3 drives the real CLI in-process (`conftest.run_cli`) over the `repo` fixture's real git
repository.

## Cycles

No cycle declares a stub: every test imports only names that exist today. `tests/test_contract.py`
already imports `ContractError` and `parse` from `tddcli.contract`. `tests/test_config_and_staging.py`
already imports `staging` and has the `declared(**kw)` helper, which builds a standard
`DeclaredCycle` and takes any field as a keyword. `tests/test_pin_cycles.py` already imports
`run_cli` and `write_plan` from `conftest`.

### Cycle 1 (pin): every commit key a cycle kind commits under is kept

- **Behaviour:** decision 2's accepted column registers and reaches
  `DeclaredCycle.commit_messages` intact.
- **Test:** `tests/test_contract.py::test_every_commit_key_a_cycle_kind_commits_under_is_kept`.
  Add it at the end of the file. Parse this body with `parse(body, "tasks/p.md")` (no config):

  ```yaml
  ---
  cycles:
    - n: 1
      project: backend
      test: "tests/a.py::test_s"
      commit_red: "r"
      commit_green: "g"
      commit_refactor: "f"
    - n: 2
      projects: ["backend", "frontend"]
      contract_cycle: true
      tests: ["backend::tests/a.py::test_c", "frontend::b.test.ts > c"]
      commit_red: "r"
      commit_green: "g"
      commit_refactor: "f"
    - n: 3
      project: backend
      pin_cycle: true
      test: "tests/a.py::test_p"
      commit_pin: "p"
      commit_refactor: "f"
    - n: 4
      project: backend
      refactor_cycle: true
      commit_refactor: "f"
  ---
  ```

  Single assertion:

  ```python
  assert {c.ordinal: c.commit_messages for c in parse(body, "tasks/p.md").cycles} == {
      1: {"red": "r", "green": "g", "refactor": "f"},
      2: {"red": "r", "green": "g", "refactor": "f"},
      3: {"pin": "p", "refactor": "f"},
      4: {"refactor": "f"},
  }
  ```

- **Why a pin:** today `parse_cycle` keeps every key it finds, so this passes on arrival
  (probed with exactly this body). It exists so that cycle 2's GREEN cannot refuse a key that
  is used, in particular `commit_refactor` on a pin, which the issue's wording invites.
- **Sensitivity mutation:** in `parse_cycle`'s commit loop, skip `"refactor"`; the test fails.
  Restore with `tdd sensitivity end`.
- **If it fails on arrival:** stop with `tdd blocker --kind plan_defect --detail '...'`. Do not
  edit production code in a pin cycle.

### Cycle 2: a commit key for a phase the cycle kind never enters is refused

- **Behaviour:** decisions 1 to 4.
- **Test:** `tests/test_contract.py::test_a_commit_key_for_a_phase_the_cycle_kind_never_enters_is_refused`.
  Add two module-level helpers above it:
  - `_one_cycle(kind: str, keys: list[str]) -> str` returns this front-matter, with the lines
    for `kind` from the table below, then one line `    <key>: "x"` per entry of `keys`, in
    list order:

    ```
    ---
    cycles:
      - n: 1
    <kind lines>
    <key lines>
    ---
    ```

    | `kind` | kind lines (4-space indent) |
    |---|---|
    | `"standard"` | `project: backend`, `test: "tests/a.py::test_x"` |
    | `"contract"` | `projects: ["backend", "frontend"]`, `contract_cycle: true`, `tests: ["backend::tests/a.py::test_c", "frontend::b.test.ts > c"]` |
    | `"pin"` | `project: backend`, `pin_cycle: true`, `test: "tests/a.py::test_x"` |
    | `"refactor"` | `project: backend`, `refactor_cycle: true` |

  - `_refusal(body: str) -> str | None` returns `str(exc)` when `parse(body, "tasks/p.md")`
    raises `ContractError`, and `None` when it does not.

  The cases, in this order. `PIN`, `REF` and `STD` stand for the three message tails below:

  | # | `kind` | `keys` | expected |
  |---|---|---|---|
  | 1 | pin | `["commit_red"]` | `cycle 1: commit_red has no effect on a pin cycle, ` + PIN |
  | 2 | pin | `["commit_green"]` | `cycle 1: commit_green has no effect on a pin cycle, ` + PIN |
  | 3 | pin | `["commit_red", "commit_pin"]` | `cycle 1: commit_red has no effect on a pin cycle, ` + PIN |
  | 4 | refactor | `["commit_red"]` | `cycle 1: commit_red has no effect on a refactor cycle, ` + REF |
  | 5 | refactor | `["commit_green"]` | `cycle 1: commit_green has no effect on a refactor cycle, ` + REF |
  | 6 | refactor | `["commit_pin"]` | `cycle 1: commit_pin has no effect on a refactor cycle, ` + REF |
  | 7 | refactor | `["commit_pin", "commit_green"]` | `cycle 1: commit_green has no effect on a refactor cycle, ` + REF |
  | 8 | standard | `["commit_pin"]` | `cycle 1: commit_pin has no effect on a standard cycle, ` + STD |
  | 9 | contract | `["commit_pin"]` | `cycle 1: commit_pin has no effect on a contract cycle, ` + STD |

  - PIN = `"which commits only under commit_pin and commit_refactor. Declare the message as commit_pin."`
  - REF = `"which commits only under commit_refactor. Declare the message as commit_refactor."`
  - STD = `"which commits only under commit_red, commit_green and commit_refactor. Declare the message as commit_red."`

  Write the expected strings out as literals in the test (or build them from these three
  literal tails), never from production code. Single assertion:
  `assert [_refusal(_one_cycle(k, keys)) for k, keys in CASES] == EXPECTED`.
- **Production target:** `contract.parse_cycle` in `src/tddcli/contract.py` (decision 4). Also:
  - **`tests/test_suite_scope.py`:** delete the three lines `commit_red: "test: t"`,
    `commit_green: "feat: t"` and `commit_pin: "test: pin"` from the module-level `PLAN`
    template, and leave `CONTRACT_PLAN` as it is. GREEN's whole-suite run fails the 11 tests in
    `modifies_tests` until this is done. No test in that file asserts a commit message, so this
    changes no assertion. Nothing else in that file changes.
  - **`README.md`,** "Plan contracts" section: after the paragraph that begins
    `**Per-cycle keys:**`, add:

    > A cycle commits only in the phases its kind has, so it may declare only those phases'
    > messages: `commit_red`, `commit_green` and `commit_refactor` on a standard or contract
    > cycle, `commit_pin` and `commit_refactor` on a pin cycle, and `commit_refactor` on a
    > refactor cycle. Any other `commit_*` key would never be used, so `tdd plan register`
    > refuses the plan as malformed and names the key to use.

  - **`docs/PRD.md`** §7.2: after R7.10, add:

    > - **R7.10a** A cycle may declare a `commit_*` message only for a phase its kind enters:
    >   `commit_red`, `commit_green` and `commit_refactor` for standard and contract cycles,
    >   `commit_pin` and `commit_refactor` for pin cycles, `commit_refactor` for refactor
    >   cycles. Any other is malformed (R7.10), even beside a valid key, because a key the run
    >   never reads breaks R9.17 without a word. The refusal names the key to use (#231).

  - **`CHANGELOG.md`:** under `## [Unreleased]`, add a `### Fixed` heading, then:

    > - **A `commit_*` key a cycle never uses is refused at registration** (#231). A pin cycle
    >   commits only under `commit_pin` and `commit_refactor`, a refactor cycle only under
    >   `commit_refactor`, and a standard or contract cycle never under `commit_pin`. A plan
    >   that declared another key, most often a pin's message under `commit_red`, registered
    >   and then committed with the default message instead. `tdd plan register` now refuses it
    >   as a malformed contract and names the key to use.
- **EXPECTED FAILURE** (probed for case 1): `AssertionError: assert [None, None, None, None,
  None, None, None, None, None] == ['cycle 1: commit_red has no effect on a pin cycle, which
  commits only under commit_pin and commit_refactor. Declare the message as commit_pin.', ...]`.
  Today `parse` raises nothing for any case.

### Cycle 3 (pin): `tdd plan register` refuses a pin cycle that declares `commit_red`

- **Behaviour:** the issue's case, at the CLI consumer. `cmd_plan_register` turns cycle 2's
  `ContractError` into the envelope a planner sees.
- **Test:** `tests/test_pin_cycles.py::test_plan_register_refuses_a_pin_cycle_that_declares_commit_red`.
  Add it at the end of the file. Plan body:

  ```yaml
  ---
  cycles:
    - n: 1
      project: backend
      pin_cycle: true
      title: "pin: greet says hello"
      test: "tests/test_greet.py::test_greet_returns_hello"
      commit_red: "test(greet): pin that greet says hello"
  ---
  ```

  `plan = write_plan(repo, body)`, then `out = run_cli(repo, "plan", "register", plan)`.
  Single assertion:

  ```python
  assert (out["ok"], out.get("error")) == (
      False,
      "malformed plan contract: cycle 1: commit_red has no effect on a pin cycle,"
      " which commits only under commit_pin and commit_refactor."
      " Declare the message as commit_pin.",
  )
  ```

- **Why a pin:** `cmd_plan_register` already catches `ContractError` and builds this envelope,
  so once cycle 2 lands it passes on arrival. The after-state was probed with a throwaway rule
  in a scratch worktree: `{'ok': False, 'error': 'malformed plan contract: cycle 1: …', 'result':
  {'plan': 'tasks/plan.md'}}`. Before cycle 2 it fails with
  `AssertionError: assert (True, None) == (False, '…')` (probed).
- **Sensitivity mutation:** comment out cycle 2's `raise` in `parse_cycle`; the test fails.
- **If it fails on arrival:** cycle 2's message differs from decision 4, or its check is
  somewhere `plan register` does not reach. File `tdd blocker --kind plan_defect --detail
  '...'`. Do not edit production code in a pin cycle.

### Cycle 4 (pin): a pin message is left alone unless its default title leads with the word `pin`

- **Behaviour:** the negative space of decision 5. Every input below keeps today's message.
- **Test:** `tests/test_config_and_staging.py::test_a_pin_message_is_left_alone_unless_its_default_title_leads_with_the_word_pin`.
  Add it directly after `test_commit_message_prefers_the_plan`. Use `declared(kind="pin", ...)`.

  | phase | `declared(...)` keywords | ordinal | expected |
  |---|---|---|---|
  | `staging.PIN` | `title="pinned x"` | 1 | `test: pin pinned x` |
  | `staging.PIN` | `title="pins x"` | 1 | `test: pin pins x` |
  | `staging.PIN` | `title="spin x"` | 1 | `test: pin spin x` |
  | `staging.PIN` | `title="pin-x"` | 1 | `test: pin pin-x` |
  | `staging.PIN` | `title="pin"` | 1 | `test: pin pin` |
  | `staging.PIN` | `title="pin:"` | 1 | `test: pin pin:` |
  | `staging.PIN` | `title=""` | 3 | `test: pin cycle 3` |
  | `staging.PIN` | `title="pin: y", commit_messages={"pin": "pin: x"}` | 1 | `pin: x` |
  | `staging.REFACTOR` | `title="pin: x"` | 1 | `refactor: pin: x` |

  Single assertion: the list of `staging.default_message(phase, declared(kind="pin", **kw),
  ordinal)` over the rows equals the list of expected strings.
- **Why a pin:** every row is today's output (`default_message` has no strip yet), so it passes
  on arrival. It stops cycle 5's GREEN from stripping too much.
- **Sensitivity mutation:** change the `PIN` fallback to `f"test: pin: {title}"`; the test
  fails.
- **If it fails on arrival:** `tdd blocker --kind plan_defect --detail '...'`.

### Cycle 5: the default pin message drops a leading `pin` from the title

- **Behaviour:** decision 5.
- **Test:** `tests/test_config_and_staging.py::test_the_default_pin_message_drops_a_leading_pin_from_the_title`.
  Add it directly after cycle 4's test. For each title,
  `staging.default_message(staging.PIN, declared(kind="pin", title=t), 1)`:

  | title | expected |
  |---|---|
  | `pin: an unknown payload routes to the default action` | `test: pin an unknown payload routes to the default action` |
  | `pin:x` | `test: pin x` |
  | `Pin x` | `test: pin x` |
  | `PIN - x` | `test: pin x` |
  | `pin -x` | `test: pin x` |
  | `pin  :  x` | `test: pin x` |

  The first row is the issue's own example. Single assertion: the list of results equals the
  list of expected strings.
- **Production target:** the `PIN` entry of the fallback in `staging.default_message`, in
  `src/tddcli/staging.py`. A module-level compiled pattern is fine; `staging.py` does not import
  `re` yet. Also:
  - **`README.md`:** at the end of the paragraph cycle 2 added, append:

    > With no message declared, a phase commits as `test: <title>`, `feat: <title>`,
    > `refactor: <title>` or `test: pin <title>`. The pin default first drops a leading `pin`,
    > `pin:` or `pin -` (any case) from the title, so `pin: x` commits as `test: pin x`.

  - **`docs/PRD.md`:** at the end of R9.17, append: *"With no message declared, a phase commits
    as `test: <title>` (RED), `feat: <title>`, `refactor: <title>` or `test: pin <title>`. The
    pin default first drops a leading `pin`, `pin:` or `pin -` (any case) from the title (#231)."*
  - **`CHANGELOG.md`:** under the `### Fixed` heading cycle 2 added, add:

    > - **The default pin commit message no longer doubles `pin`** (#231). A pin cycle with no
    >   `commit_pin` whose title starts with `pin`, `pin:` or `pin -` commits as
    >   `test: pin <rest of the title>`, not `test: pin pin: …`.
- **EXPECTED FAILURE** (probed for the first row and `Pin x`):
  `AssertionError: assert ['test: pin pin: an unknown payload routes to the default action',
  'test: pin pin:x', ...] == ['test: pin an unknown payload routes to the default action',
  'test: pin x', ...]`.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-231-commit-keys-per-cycle-kind   # first, before anything else
    tdd doctor                                  # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-231-commit-keys-per-cycle-kind.md   # captures baselines, opens cycle 1

`tdd doctor` checks every project; `tdd run start` probes only the ones the plan declares and
those downstream of them through an `[artifact]`. A failing check on a project outside that set
does not stop the run: note it and go on. Any other failing check stops it.

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is green
  at the plan's base (verified in a fresh worktree of `origin/main` at `bd57486`:
  `869 passed`). Expect `baselines: {tddcli: 0}`.
- The referee is the released `tdd` on `PATH` (the note at the top of `tdd.toml`), never
  `uv run tdd`. The released referee does not enforce this plan's rule, which is fine: this
  plan's own front-matter declares only live keys.
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`. Pins 1, 3 and 4 always need
    one; each cycle names its mutation. A standard RED that pre-passes needs one too: mutate the
    increment that cycle added.
  - `annotate_cycle` → `tdd annotate --key --value`. This plan declares no keys of its own;
    `plan_defect` and `friction_note` are reserved.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|environment> --detail '...'`. A pin
    that fails on arrival is `plan_defect`, as each pin cycle says.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.
  - `fix_regression` in cycle 2's GREEN is expected until the `tests/test_suite_scope.py`
    template edit is made. That edit belongs to cycle 2's GREEN.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- Cycle 1 is a pin. It adds only its test.
- Cycle 2 adds:
  - the per-kind check in `parse_cycle` with decision 4's exact message;
  - the `tests/test_suite_scope.py` `PLAN` template edit;
  - the README paragraph, PRD R7.10a and the first CHANGELOG entry under a new `### Fixed`.

  Nothing in `staging.py`.
- Cycles 3 and 4 are pins. They add only their test.
- Cycle 5 adds:
  - the strip in `staging.default_message`'s `PIN` fallback;
  - the README sentence, the R9.17 sentence and the second CHANGELOG entry.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-231-commit-keys-per-cycle-kind-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-231-commit-keys-per-cycle-kind-friction.md
    git commit -m "docs: friction log for issue-231-commit-keys-per-cycle-kind"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #231`. Cycles 2 and 5 own the docs:

- `git diff --stat origin/main -- README.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- docs/PRD.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.

The visible change is a registration refusal and a commit subject, so no demo recording is
required. In the PR body:
- Quote cycle 3's refusal text.
- Say that `commit_refactor` stays valid on a pin cycle, unlike the issue's wording, because a
  pin cycle commits in its refactor phase.
- Say that the refusal is new behaviour for plans that already declare a dead key: any harness
  that registers such a plan now gets `ok: false` until it moves the message to the key the
  error names.
