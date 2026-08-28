---
closes: 72
cycles:
  - n: 1
    project: tddcli
    title: "outcome lookup returns None for an id absent from every verdict"
    test: "tests/test_advance_adoption.py::test_outcome_lookup_returns_none_for_unexecuted_id"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: verdict outcome lookup admits it cannot judge an unexecuted id"
    commit_green: "feat: _outcome_from_verdicts helper (None when the id never ran)"

  - n: 2
    project: tddcli
    title: "a single adopted test that failed is evaluated as RED in the same advance"
    test: "tests/test_advance_adoption.py::test_single_new_test_is_adopted_and_evaluated_in_one_advance"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: adoption of the one new failing test reaches RED without a re-run"
    commit_green: "feat: evaluate the adopted target from the suite run that already happened"

  - n: 3
    project: tddcli
    title: "a single adopted test that passed drives sensitivity in the same advance"
    test: "tests/test_advance_adoption.py::test_adopted_passing_test_demands_sensitivity_in_one_advance"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: an adopted pre-passing test hits red_first_violation without a re-run"
    commit_green: "feat: adopted-target evaluation covers the passed-on-arrival path"

  - n: 4
    project: tddcli
    title: "disambiguation picks the candidate that normalise-matches the declared id"
    test: "tests/test_advance_adoption.py::test_disambiguate_picks_the_normalisation_match"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: _disambiguate resolves a vitest separator-only mismatch"
    commit_green: "feat: _disambiguate — unique normalise-equal candidate wins"

  - n: 5
    project: tddcli
    title: "the unique candidate in the declared file is adopted among several new tests"
    test: "tests/test_advance_adoption.py::test_unique_same_file_candidate_is_adopted_and_evaluated"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: same-file disambiguation adopts and evaluates without asking"
    commit_green: "feat: wire _disambiguate into the multiple-new-tests branch (same-file rule)"

  - n: 6
    project: tddcli
    pin_cycle: true
    title: "genuinely ambiguous new tests still ask the agent"
    test: "tests/test_advance_adoption.py::test_ambiguous_new_tests_still_ask_the_agent"
    commit_pin: "test: pin that two same-file candidates still demand tdd target"
---

# Issue #72 — adopt the declared target on the first `multiple_new_tests`, without extra suite runs

https://github.com/geuben/tdd-cli/issues/72
Task file: `tasks/issue-72-adopt-on-first-run.md`

## Context

When a RED phase introduces a test whose id differs from the declared target, the first
suite run returns `not_found` and adoption costs extra full suite runs — expensive on
simulator-backed XCTest and Gradle instrumentation suites (an observed real run burned
five AWAITING_TEST runs on cycle 1). Probing the current flow shows it is worse than the
issue states: after the single-candidate "Adopted … Run `tdd advance` again" reply, the
next advance hits the `no_change_since_last_run` guard (nothing changed since the run
that already executed the adopted test) and answers `write_test`, so the executor must
also discover `--retry`.

The suite run that produced `not_found` **already executed the new test** — its verdict
(`Verdict.passed` / `Verdict.failed`) is returned by `Engine.run_projects` and currently
discarded by `_handle_test_phase`. This plan evaluates the adopted target from that run:
single new candidate → adopt and judge immediately (RED commit or
`red_first_violation` + sensitivity, in the same advance); several candidates → adopt
only when exactly one normalise-matches the declared id (#57) or exactly one lives in
the declared target's file, else keep the ask-the-agent round-trip. The compile-failure
(`not_collected`) fast path is deliberately not built (see scope cuts).

## Design decisions (locked)

- **Evaluate from the run that already happened** (the issue's core ask; evidence: the
  verdicts are in hand at the adoption site). `_handle_test_phase` binds the `verdicts`
  element of `run_projects`'s return (currently `_`) and a new helper
  `_outcome_from_verdicts(verdicts, test_id)` maps the adopted id to `FAILED`/`PASSED`
  membership — or `None` when the id was never executed (collected between run and
  `_adopt_target`'s re-collect), in which case the **existing** "Run `tdd advance`
  again" reply is kept as the fallback. The fallback is today's code, not new untested
  behaviour.
- **After adoption, the evaluation re-enters the normal branch flow** with `targets`,
  `outcomes`, and `others` updated: the adopted id is removed from `others` (a failing
  new non-target test lands there via baseline subtraction — probed) and its outcome
  inserted, so the existing `not_collected` / regression / `passed_all` / `failed_all`
  logic judges it unchanged. The `declared_test_mismatch` event and `target_tests`
  update are recorded exactly as today, before evaluation.
- **Disambiguation rules — normalisation match and same-file only** (user decision):
  `_disambiguate(candidates, declared_id, adapter)` returns the single candidate whose
  `adapter.normalise_id` equals the declared id's normalised form, else the single
  candidate whose file part (the portion before the first `::`, then before any ` > `,
  after the `project::` prefix) equals the declared target's, else `None`. Fuzzy
  closest-name adoption is excluded (user decision): `cmd_target` doctrine suggests
  near-misses via difflib but refuses to auto-pick, and a silently wrong adoption would
  evaluate RED against the wrong behaviour.
- **Ambiguity still asks** — `_disambiguate` returning `None` preserves today's
  `multiple_new_tests` event + `NAME_TARGET_TEST` reply verbatim (pinned by cycle 6).
- **Pin cycles get the same mechanics for free**: `AWAITING_PIN` shares
  `_handle_test_phase`, and the re-entered flow's `expect_pass` branch judges the
  adopted outcome. No pin-specific code.
- **The compile-failure fast path is not built** (user decision; see scope cuts).

## Verified repo facts

*Anchors are symbol names — grep for them; no line numbers in this plan.*

- **Probed current behaviour (throwaway test on the conftest `repo` fixture, deleted;
  tree clean).** Single new test named differently from the declared target, failing on
  a `NotImplementedError` stub: first `advance` → `ok: True`,
  `result.adopted == ["backend::tests/test_add.py::test_adding"]`, verb
  `refactor_or_advance`, detail "Adopted … Run `tdd advance` again to evaluate it";
  **second advance → verb `write_test` with `no_change_since_last_run`** (the guard
  fires because the tree is unchanged). Two new tests (one in the declared file, one in
  a new file): first advance → verb `name_target_test`, `result.candidates` lists both.
- **The adoption site.** `_handle_test_phase` (`advance.py`): `outcomes, others, _,
  failure = engine.run_projects(...)` — the discarded third element is the list of
  `Verdict`s (dataclass in `adapters/base.py` with `passed: list[str]`,
  `failed: list[str]`, ids qualified `project::native`). The `missing` branch calls
  `_adopt_target` (re-collects per project, returns new-since-run-start candidates),
  then splits on `len(candidates)` — `1`: event `declared_test_mismatch`, update
  `cycle.target_tests`, reply "advance again"; `>1`: event `multiple_new_tests`, verb
  `NAME_TARGET_TEST`; `0`: `WRITE_TEST`.
- **Why `others` must be adjusted**: `run_projects` computes
  `other = [f for f in verdict.failed if f not in base and f not in targets]` — a
  failing adopted-to-be test is in `others` at adoption time; left there, the re-entered
  flow would answer `FIX_REGRESSION`.
- **Collected and executed ids share one format per adapter** — both come from the same
  adapter (`qualify`), and the vitest module docstring pins that `vitest list` output is
  parsed "into ids matching those `run()` produces". Membership lookup needs no
  cross-format translation; `normalise_id` is used only for the disambiguation match.
- **`cmd_target` / `target_named_by_agent`** (`cli.py`) is the surviving ambiguous-case
  flow and is untouched; `tests/test_target_validation.py` pins it.
- **Blast radius: empty.** No existing test asserts the single-candidate two-step reply,
  the `declared_test_mismatch` event, or the `multiple_new_tests` flow
  (`grep -rn "declared_test_mismatch\|multiple_new_tests\|Adopted" tests/` → comments
  only). `modifies_tests` is empty for every cycle.
- **Fixture inheritance.** All e2e cycles use the conftest `repo` fixture +
  `write_plan`/`run_cli`, the declared target `tests/test_add.py::test_add_two_numbers`,
  and a stub `app/calc.py` — the exact setup of `tests/test_end_to_end.py` and the
  probe. Nothing novel to verify at execution time.
- **Suite is green now**: 406 passed on this branch. Expected `run start` baseline:
  `{"tddcli": 0}` — anything else means a moved branch; stop.
- **Lint is ruff-only, no typecheck.** Unit cycles (1, 4) must import the module and
  access the helper **inside the test body** (`from tddcli import advance` then
  `advance._outcome_from_verdicts(...)`) so a missing helper is an in-test
  `AttributeError`, never a collection error — **no cycle needs `stub_expected`**.

## Cycle detail

*Single project `tddcli`; tests in a new `tests/test_advance_adoption.py`. Minimum GREEN
throughout. Helper-first ordering: cycle 1 fixes the helper's "cannot judge" contract
before cycle 2 wires evaluation, so neither cycle's kind is ambiguous.*

**Cycle 1 — outcome lookup admits ignorance.** Test (unit): build two `Verdict`s (one
per project) whose `passed`/`failed` do not contain `"backend::tests/test_x.py::test_y"`;
assert `advance._outcome_from_verdicts(verdicts, id) is None`. *EXPECTED FAILURE:*
`AttributeError: module 'tddcli.advance' has no attribute '_outcome_from_verdicts'`.
*GREEN:* the helper — walk verdicts, return `FAILED` on `failed` membership, `PASSED` on
`passed` membership, else `None`. (Minimal GREEN may legitimately be `return None`;
cycle 2 forces the real lookup.) Production target:
`advance._outcome_from_verdicts`.

**Cycle 2 — single adopted failing test reaches RED in one advance.** Test (e2e):
declared `tests/test_add.py::test_add_two_numbers`; write `test_add.py` containing only
`test_adding` (imports `app.calc.add`, asserts a sum) and the `calc.py` stub raising
`NotImplementedError`; one `advance`; assert `next_action.verb ==
"write_implementation"` and `run.phase == "AWAITING_IMPL"`. *EXPECTED FAILURE (probed):*
verb is `refactor_or_advance` ("Adopted … Run `tdd advance` again"). *GREEN:* bind
`verdicts` in `_handle_test_phase`; in the `len(candidates) == 1` branch, after the
existing event + `target_tests` update, `outcome = _outcome_from_verdicts(verdicts,
candidates[0])`; on `None` keep the existing reply; otherwise replace `targets`, set
`outcomes` to the adopted id's outcome, drop the adopted id from `others`, and fall
through to the existing branch flow (which here commits RED and transitions to
`AWAITING_IMPL`). Production target: `advance._handle_test_phase`.

**Cycle 3 — single adopted passing test demands sensitivity in one advance.** Test
(e2e): same shape but `calc.py` already implements `add`; one `advance`; assert
`next_action.verb == "run_sensitivity_check"`. *EXPECTED FAILURE:* verb is
`refactor_or_advance` (the adoption reply — same probed shape as cycle 2). *GREEN:*
nothing beyond cycle 2's fall-through reaching the `passed_all` branch
(`red_first_violation` + `SENSITIVITY_REQUIRED`); if cycle 2's minimal GREEN
special-cased `FAILED`, generalise it here. Production target:
`advance._handle_test_phase`.

**Cycle 4 — `_disambiguate` resolves a normalisation match.** Test (unit): build a
`VitestAdapter` via the `tests/test_id_normalisation.py` pattern; candidates
`["frontend::a.test.ts > helper formats a value", "frontend::b.test.ts > other case"]`,
declared `"frontend::a.test.ts > helper > formats a value"`; assert
`advance._disambiguate(candidates, declared, adapter) == candidates[0]`. *EXPECTED
FAILURE:* `AttributeError: module 'tddcli.advance' has no attribute '_disambiguate'`.
*GREEN:* the helper's normalisation rule — the unique candidate with
`adapter.normalise_id(candidate) == adapter.normalise_id(declared)`. Production target:
`advance._disambiguate`.

**Cycle 5 — unique same-file candidate is adopted and evaluated.** Test (e2e): declared
`tests/test_add.py::test_add_two_numbers`; write `test_add.py` with the single
`test_adding` (failing on the stub) **and** a new `tests/test_other.py` with a passing
`test_other_thing`; one `advance`; assert `next_action.verb == "write_implementation"`.
*EXPECTED FAILURE (probed):* verb is `name_target_test` with both candidates. *GREEN:*
add the same-file rule to `_disambiguate` (file part = portion before the first `::`,
then before any ` > `, after `project::`), and in the `len(candidates) > 1` branch call
it: a resolved candidate takes the cycle-2 adopt-and-evaluate path (recording
`declared_test_mismatch` with the full candidate list in the detail); `None` keeps the
existing ask. Note: pytest's `normalise_id` is the identity, so this test cannot be
satisfied by the normalisation rule — it forces same-file. Production targets:
`advance._disambiguate`, `advance._handle_test_phase`.

**Cycle 6 (pin) — genuine ambiguity still asks.** Test (e2e): write `test_add.py`
containing **two** new tests (neither named the declared target, both failing on the
stub); one `advance`; assert `next_action.verb == "name_target_test"` and
`result.candidates` lists both. Passes on arrival against cycles 1–5 (two same-file
candidates → `_disambiguate` returns `None` → the preserved ask path — the probed
behaviour). The mandatory sensitivity check proves it bites: mutate `_disambiguate` to
return `candidates[0]` unconditionally, observe the pin fail (the advance adopts and
evaluates instead of asking), restore.

## Deliberate scope cuts (do not build)

- **No compile-failure-as-RED fast path** (user decision). Premise: stub-first is
  load-bearing doctrine — R10.2 and the xctest adapter docstring pin that an
  import/build error is `not_collected`, *not* RED, so a cycle can never go green
  without observing the assertion itself fail; accepting "fails to compile referencing
  a missing symbol" as RED evidence would sanction exactly that. The issue only says
  "consider". *Re-evaluation trigger:* if a future slow-suite friction log shows the
  stub round-trip dominating even after this plan's adoption fix, open a dedicated
  issue for a symbol-matched compile-RED with its own guard design — do not absorb it
  here.
- **No fuzzy closest-name adoption** (user decision). `cmd_target` remains the place
  where near-misses are *suggested* (difflib) but a human/agent choice is required.
- **No change to `_adopt_target`'s re-collect cost.** The per-adoption `adapter.collect()`
  pass stays; on slow collectors it is still far cheaper than the suite runs this plan
  removes. Separate optimisation if it ever shows up in a friction log.
- **No `xfail-batch` mode** — the issue names it as a separate proposal; this plan
  covers classic mode only.
- **`cmd_target`, `no_change_since_last_run`, and the stub-directive flow are
  untouched** — the ambiguous path still routes through `tdd target`, and the
  `not_collected` branch keeps its `CREATE_STUB` round-trip (see the first cut).
- **Mirrors: none** — the adoption logic lives once in `advance.py`; no
  `docs/INVARIANTS.md` registry exists in this repo.
- **README/PRD documentation** is a post-run doc follow-up, not a cycle (see
  Done-criteria).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do
not ask the user to start the run. `tdd run start` records which model is executing,
resolved from your own session; a run started by anyone else attributes this work to the
wrong agent.

**Referee rule:** run the *released* tdd-cli **0.8.0** at `~/.local/bin/tdd` (the
`uv tool` install), never a working-tree editable install. On this machine plain `tdd`
on PATH resolves to an editable venv importing from this working tree — check
`which tdd` and use the full path `~/.local/bin/tdd` in every command below if it is not
already first. Verify: `~/.local/bin/tdd --version` → `tdd-cli 0.8.0`. This plan adds no
ledger schema and uses only 0.8.0-supported front-matter keys. (The released referee
still uses the *old* two-step adoption if your own declared ids miss — declare them
exactly as written in this contract.)

    git checkout -b feat/72-adopt-on-first-run     # first, before anything else
    ~/.local/bin/tdd doctor                        # must report healthy: true
    ~/.local/bin/tdd run start --plan tasks/issue-72-adopt-on-first-run.md

If the branch already exists, do not force-checkout and do not pick another name: check
it out only if it carries this plan's commit and no unrelated work, otherwise stop and
ask. If `tdd doctor` fails on *other* uncommitted `tasks/issue-*.md` files (sibling
plans), commit, stash, or gitignore them before `run start`.

Then repeat until done: read `next_action.verb`, do exactly what it says, run
`~/.local/bin/tdd advance`. Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit
it, and raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase; the tool stages and commits from
  the phase — do not `git add`/`git commit` yourself.
- Expected baseline for this repo: `{"tddcli": 0}` — anything else means a moved branch;
  stop.
- This plan declares **no `annotation_keys`**, so `annotate_cycle` will not appear.
  Verbs it will hit: standard cycles (1–5) drive `write_test` → `write_code` → optional
  refactor; **cycle 6 (pin)** passes on arrival and drives `run_sensitivity_check` →
  `~/.local/bin/tdd sensitivity begin|check|end` (mutate `_disambiguate` to return
  `candidates[0]` unconditionally, observe the pin fail, restore). If blocked,
  `resolve_blocker` → `tdd blocker --kind --detail` (kinds: `plan_defect`, `tooling`,
  `regression`, `pre_existing_failure`); `confirm_cycle_applicable` on a cycle the code
  has outgrown → `tdd cycle skip --reason`.

## Done-criteria

**Before finishing:** run
`~/.local/bin/tdd log render --out tasks/friction-logs/issue-72-adopt-on-first-run-friction.md`
(the `tasks/friction-logs/` at the **repository root**) and `~/.local/bin/tdd metrics`.
Report the plan-fidelity section — declared vs delivered vs skipped — and every
integrity event. Do not narrate what the ledger already records.

Then the documentation follow-up, committed as ordinary commits after the run is
terminal: in `docs/PRD.md`, update the R8.9 adoption text and the
`declared_test_mismatch` / `multiple_new_tests` event descriptions to reflect
same-advance evaluation and the two disambiguation rules (and that ambiguity still
routes through `tdd target`).

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-72-adopt-on-first-run-friction.md
    git commit -m "docs: friction log for issue-72-adopt-on-first-run"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes
the branch and opens the PR against `main`. Do not push or call the GitHub API by hand.
If a gate fails, fix it and re-run the skill — a failed gate is work, not a reason to
hand back.
