---
closes: 129
cycles:
  - n: 1
    project: tddcli
    pin_cycle: true
    title: "a failing gate at close still replies fix_regression with that gate's entry"
    test: "tests/test_close_sweep_gates.py::test_failing_lint_replies_fix_regression_with_the_lint_gate"
    files: []
    commit_pin: "test: pin the fix_regression reply a failing close-sweep gate produces"
  - n: 2
    project: tddcli
    pin_cycle: true
    title: "a gate that ran records a gate_result row"
    test: "tests/test_close_sweep_gates.py::test_a_failing_lint_records_its_gate_result_row"
    files: []
    commit_pin: "test: pin the gate_result row a failing lint writes"
  - n: 3
    project: tddcli
    title: "_gate stops at the first failing command"
    test: "tests/test_close_sweep_gates.py::test_gate_stops_at_the_first_failing_command"
    files: ["src/tddcli/adapters/base.py"]
    commit_red: "test: _gate stops at the first failing command"
    commit_green: "feat: _gate returns at the first failing command"
    commit_refactor: "refactor: tidy _gate"
  - n: 4
    project: tddcli
    title: "a failing lint means typecheck is never run"
    test: "tests/test_close_sweep_gates.py::test_a_failing_lint_stops_the_gate_pass_before_typecheck"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: a failing lint stops the gate pass before typecheck"
    commit_green: "feat: the close-sweep gate pass stops at the first failing gate"
    commit_refactor: "refactor: tidy the gate pass"
  - n: 5
    project: tddcli
    title: "a failing gate short-circuits the sweep before any suite runs"
    test: "tests/test_close_sweep_gates.py::test_a_failing_gate_runs_no_suite"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: a failing close-sweep gate runs no suite"
    commit_green: "feat: close-sweep gates run before the suite and short-circuit"
    commit_refactor: "refactor: tidy sweep"
  - n: 6
    project: tddcli
    title: "every sweep project's gates run before any project's suite"
    test: "tests/test_close_sweep_gates.py::test_a_later_projects_failing_gate_runs_no_earlier_suite"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: a later project's failing gate runs no earlier suite"
    commit_green: "feat: the whole gate pass precedes the whole suite pass"
    commit_refactor: "refactor: tidy sweep passes"
  - n: 7
    project: tddcli
    title: "the gate-failure reply no longer claims the sweep is green"
    test: "tests/test_close_sweep_gates.py::test_the_gate_failure_reply_does_not_claim_the_sweep_is_green"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: the gate-failure reply does not claim the sweep is green"
    commit_green: "feat: reword the gate-failure reply for the short-circuit"
    commit_refactor: "refactor: tidy the refactor handler"
  - n: 8
    project: tddcli
    pin_cycle: true
    title: "a gate that failed is re-run on the next close at the same tree"
    test: "tests/test_close_sweep_gates.py::test_a_failed_gate_is_rerun_at_the_same_tree"
    files: []
    commit_pin: "test: pin that a failed gate is re-run at the same tree"
  - n: 9
    project: tddcli
    pin_cycle: true
    title: "a gate is re-run when its project tree changed"
    test: "tests/test_close_sweep_gates.py::test_a_gate_is_rerun_when_the_tree_changed"
    files: []
    commit_pin: "test: pin that a changed tree re-runs the gate"
  - n: 10
    project: tddcli
    title: "gate_result carries the tree hash a gate ran at, and whether it was skipped"
    test: "tests/test_release_surface.py::test_gate_result_gains_tree_hash_and_skipped_columns"
    files: ["src/tddcli/ledger.py"]
    commit_red: "test: gate_result carries tree_hash and skipped"
    commit_green: "feat: schema v11 adds gate_result.tree_hash and gate_result.skipped"
    commit_refactor: "refactor: tidy the schema"
  - n: 11
    project: tddcli
    title: "a gate that passed at this tree hash is not re-executed"
    test: "tests/test_close_sweep_gates.py::test_a_passing_gate_is_not_reexecuted_at_an_unchanged_tree"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: a passing gate is not re-executed at an unchanged tree"
    commit_green: "feat: skip a gate whose tree hash is unchanged since it passed"
    commit_refactor: "refactor: tidy the gate memo"
  - n: 12
    project: tddcli
    title: "a skipped gate still records a gate_result row, marked skipped"
    test: "tests/test_close_sweep_gates.py::test_a_skipped_gate_records_a_skipped_row"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: a skipped gate records a skipped gate_result row"
    commit_green: "feat: record the skipped gate_result row"
    commit_refactor: "refactor: tidy the gate memo"
  - n: 13
    project: tddcli
    refactor_cycle: true
    title: "amend the PRD and changelog for the new close-sweep order and schema v11"
    files: ["docs/PRD.md", "CHANGELOG.md"]
    commit_refactor: "docs: close-sweep gates run before the suite (R9.2, R9.11, schema v11)"
---

# Issue 129 — close-sweep gates run before the suite and short-circuit

## Context

[Issue #129](https://github.com/geuben/tdd-cli/issues/129): `Engine.sweep()` runs each
project's full suite first and only then that project's `lint` / `typecheck` gates. The
gates are cheap and are often what fails on a close; the suite is the expensive part. A
gate failure is therefore discovered *after* the suite has already run, and the suite's
green verdict is thrown away. Fixing the gate changes the tree, which makes the next
`tdd advance` produce a refactor commit, which disables `skip_own` — so the retry pays
for a second full suite run. One formatting slip costs two suite runs that told the
executor nothing a gate alone would not have.

Inside `Adapter._gate()` every command runs to completion even after an earlier one has
failed, so a failed lint also pays for what follows it.

This is adapter-agnostic engine code (`src/tddcli/machine.py`, `src/tddcli/adapters/base.py`),
so every adapter pays it; cargo and gradle pay most, their suite cost being dominated by
rebuild and relink.

The issue asks for three things: (1) gates before the suite with a short-circuit,
(2) first-failure stop inside `_gate()`, (3) optionally, skipping a gate whose project
tree is unchanged since that gate last passed. All three are planned here.

## Design decisions (locked)

1. **The gate pass precedes the suite pass, across all sweep projects — not per project.**
   `sweep()` runs lint and typecheck for every project in the close-sweep set first; only
   if every gate passes does it run any suite. A lint slip in `svc` therefore costs
   `backend` nothing. *(User, Phase C.)* The alternative — per-project gates-then-suite —
   still pays for every suite ordered before the failing project.

2. **The gate pass stops at the first failing gate.** A failing lint means typecheck is
   not run, for that project or any later one; `SweepOutcome.gates` then carries exactly
   one entry where today it carries every failing gate. *(User, Phase C.)* This is the
   cost the issue names ("a failed lint still pays for the typecheck that follows it")
   and it is what the empirically-probed envelope changes: today a close with a failing
   lint and a failing typecheck returns `gates: [lint, typecheck]`; after this plan it
   returns `gates: [lint]`. Cycles 1 and 2 pin the *surviving* behaviour only — they
   assert on the lint entry and the lint `gate_result` row, and must not assert that a
   typecheck entry or row is also present, or cycle 4 cannot go green without weakening
   a pin.

3. **`Adapter._gate()` returns at the first failing command; no run-all flag.** *(User,
   Phase C.)* `GateResult.output` then carries the one failing command's `$ cmd` block.
   No caller wants the full list, and a flag would be surface with no consumer.

4. **A gate is skipped when the latest `gate_result` row for `(run_id, project, kind)`
   has `ok = 1` and a `tree_hash` equal to the project's current tree hash.** *(User chose
   to build issue item 3 now; shape decided from the code.)* Notes that make this exact:
   - The key is `Engine.tree_hash([project])` — `gitutil.tree_hash` hashes tracked content,
     the working diff *and* untracked file contents under the project's roots, so it
     already answers "is this project's tree the one the gate saw?". Verified empirically:
     two consecutive closes with no edit between them record the identical
     `invocation.tree_hash`, and lint ran twice.
   - **Scoped to the run** (`run_id` in the lookup). Cross-run reuse would let a gate
     result from another branch or worktree suppress a gate here; the ledger is
     per-repository, not per-branch.
   - **Only a passing gate memoises.** A row with `ok = 0` never suppresses a later run —
     pinned by cycle 8.
   - **A gate whose project tree changed re-runs** — pinned by cycle 9.
   - A project root that does not contain the gate's own configuration (e.g. a repo-root
     `pyproject.toml` configuring `ruff` for a project rooted at `backend/`) can change
     without changing the project's tree hash, so the gate is not re-run in that window.
     This matches `skip_own`, which keys the suite skip on exactly the same hash, and is
     stated in the PRD amendment (cycle 13) rather than worked around.

5. **The skipped gate still writes its `gate_result` row**, with `ok = 1`, `skipped = 1`,
   the current `tree_hash` and empty `output`. The ledger's record of a close must not
   become sparser than the close itself; nothing else reads `gate_result` today
   (verified: the only reads are in tests), so the new columns break no consumer.

6. **Ledger schema goes to v11** with `MIGRATIONS[10]` adding both columns by
   `ALTER TABLE`, following the `artifact_check.regenerate_failed` and `run.start_sha`
   precedents. Consequence, accepted: tdd-cli 0.11.0 refuses to open a v11 ledger, so the
   released-referee doctrine in `tdd.toml` again needs the frozen-snapshot referee
   (`uv venv /tmp/tdd-referee-129 && uv pip install --python /tmp/tdd-referee-129/bin/python .`)
   built at the plan commit. The bump does not affect *this* run: the referee writes the
   repo ledger at its own schema version, and the working-tree code under test only ever
   opens the temporary ledgers its own tests create.

7. **Ledger semantics otherwise unchanged.** When the gate pass short-circuits, no
   `invocation` row is written for that attempt (the suite did not run) — this is the
   observable the tests assert. `resume --accept-failures` reads the *latest* CLOSE_SWEEP
   invocation per project; a gate-failing attempt simply leaves the previous one in place,
   and there is no failure set to accept when no suite ran.

8. **The reply wording changes.** `"Close sweep is green but lint/typecheck gates failed."`
   becomes `"Close sweep stopped before the suite: lint/typecheck gates failed."` — the
   old sentence asserts a green sweep that no longer happened. Verb stays `fix_regression`,
   `result.gates` keeps its `{project, kind, output}` shape, and `result.commit` still
   carries the refactor commit sha.

9. **Tests drive the real engine through `run_cli`.** No fakes, no doubles, no
   monkeypatching of the adapter — every cycle's test builds a real git repo from the
   `repo` / `repo_three` fixtures, writes a `tdd.toml` whose gate commands are shell
   one-liners, and drives `plan register` → `run start` → `advance`. Whether a gate
   command actually executed is observed by having it append a line to a counter file
   **outside the repository** (under `tmp_path`), so counting is independent of any
   production code path and the counter cannot perturb any project's tree hash.

## Deliberate scope cuts (do not build)

None. Every item in the issue, including the optional item 3, is built in this plan.

## Cycles

Every test below lives in `tests/test_close_sweep_gates.py` unless stated. All of them
use this shape: write `tdd.toml` with the gate commands under test, commit, register the
plan, `run start`, advance through RED and GREEN, then advance once or twice more at
`AWAITING_REFACTOR` — the transition that runs the close sweep.

### Cycle 1 — pin: a failing gate replies `fix_regression` with that gate's entry

`test_failing_lint_replies_fix_regression_with_the_lint_gate`. Single project with
`lint = ["sh -c 'exit 1'"]`. One assertion: the close envelope's
`next_action.verb` is `fix_regression` and `result.gates` contains an entry whose
`project` is `backend` (the fixture project) and whose `kind` is `lint` — expressed as one
`assert` over `(verb, [(g["project"], g["kind"]) for g in gates])`. It must **not**
assert the list length or that typecheck appears (decision 2).

EXPECTED: passes on arrival — this is existing behaviour, verified by probe: the close
returns `verb: fix_regression`, `result.gates[0] == {"project": "backend", "kind": "lint",
"output": "$ sh -c ...\n..."}`.

### Cycle 2 — pin: a gate that ran records a `gate_result` row

`test_a_failing_lint_records_its_gate_result_row`. Same scenario; assert the ledger holds
a `gate_result` row for `(project='backend', kind='lint')` with `ok = 0`. Must not assert
the total row count (decision 2).

EXPECTED: passes on arrival — probe observed `gate_result` rows `{project: backend,
kind: lint, ok: 0}` and `{kind: typecheck, ok: 0}` after a close with both gates failing.

### Cycle 3 — `_gate` stops at the first failing command

`test_gate_stops_at_the_first_failing_command`. `lint = ["sh -c 'echo LINT-BOOM; exit 1'",
"sh -c 'echo SECOND-RAN; exit 1'"]`. Assert `"SECOND-RAN" not in` the lint gate's output in
`result.gates`.

Production target: `Adapter._gate` in `src/tddcli/adapters/base.py` — `return
GateResult(ok=False, output=...)` inside the loop on the first non-zero exit code.

EXPECTED FAILURE: `AssertionError: assert 'SECOND-RAN' not in "$ sh -c 'echo LINT-BOOM;
exit 1'\nLINT-BOOM\n\n$ sh -c 'echo SECOND-RAN; exit 1'\nSECOND-RAN"` — probe-verified:
today both commands run and both blocks appear in the output.

### Cycle 4 — a failing lint means typecheck is never run

`test_a_failing_lint_stops_the_gate_pass_before_typecheck`. `lint` fails; `typecheck`
appends to a counter file under `tmp_path` and exits 1. Assert the counter file does not
exist after the close.

Production target: the gate loop in `Engine.sweep`, `src/tddcli/machine.py` — break out of
`for kind, gate in (("lint", ...), ("typecheck", ...))` as soon as a gate is not ok, and
stop the pass over projects too. Note the gates must become *lazily* evaluated: today the
tuple literal calls `adapter.lint()` and `adapter.typecheck()` before the loop body runs,
so an early `break` alone changes nothing.

EXPECTED FAILURE: `AssertionError: assert False` on `assert not counter.exists()` —
probe-verified: today a close with both gates failing produces `TYPECHECK-RAN` in the
envelope, i.e. typecheck ran after lint failed.

### Cycle 5 — a failing gate short-circuits the sweep before any suite runs

`test_a_failing_gate_runs_no_suite`. Single project, `lint` fails. Assert the ledger holds
no `invocation` row with `phase_at = 'CLOSE_SWEEP'`.

Production target: `Engine.sweep` — run the gate pass first and return
`SweepOutcome(failures=[], gates=[...])` before the suite loop.

EXPECTED FAILURE: `assert 1 == 0` — probe-verified: today a gate-failing close leaves
`invocation` row `{phase_at: CLOSE_SWEEP, project: backend, total_passed: 2}`.

### Cycle 6 — every sweep project's gates run before any project's suite

`test_a_later_projects_failing_gate_runs_no_earlier_suite`. Uses the `repo_three` fixture
(`backend`, `svc`, `other`, with artifact `schema` produced by `backend` and consumed by
`svc`). `svc` gets a failing `lint`; `backend`'s gates pass. The cycle writes
`backend/schema.json` during the refactor phase, which pulls `svc` into the close sweep.
Sweep order is `sorted(names)`, so `backend` is visited before `svc`. Assert the ledger
holds no `invocation` row with `phase_at = 'CLOSE_SWEEP' AND project = 'backend'`.

Production target: `Engine.sweep` — one loop over projects for gates, then a separate loop
for suites.

EXPECTED FAILURE: `assert 1 == 0` — probe-verified on `repo_three`: today that close
records CLOSE_SWEEP invocations for **both** `backend` and `svc`, and
`result.gates == [{"project": "svc", "kind": "lint", ...}]`.

### Cycle 7 — the gate-failure reply no longer claims the sweep is green

`test_the_gate_failure_reply_does_not_claim_the_sweep_is_green`. Assert
`next_action.detail == "Close sweep stopped before the suite: lint/typecheck gates failed."`

Production target: `_handle_refactor` in `src/tddcli/advance.py`, the `_reply(...
Verb.FIX_REGRESSION, "Close sweep is green but lint/typecheck gates failed.", gates=gates)`
call — the branch reached when `outcome.gates` is non-empty.

EXPECTED FAILURE: `AssertionError: assert 'Close sweep is green but lint/typecheck gates
failed.' == 'Close sweep stopped before the suite: lint/typecheck gates failed.'` —
probe-verified as today's exact string.

### Cycle 8 — pin: a gate that failed is re-run on the next close at the same tree

`test_a_failed_gate_is_rerun_at_the_same_tree`. `lint` appends to a counter and exits 1.
Advance twice at `AWAITING_REFACTOR` with nothing edited between the two. Assert the
counter holds two lines.

EXPECTED: passes on arrival — probe-verified (`PIN-8 lint runs: 2`), and the second
advance is accepted (`ok: true`, `verb: fix_regression`) rather than refused as
`no_change_since_last_run`. This pin is what stops cycle 11's memo from suppressing the
re-run of a gate that has never passed.

### Cycle 9 — pin: a gate is re-run when its project tree changed

`test_a_gate_is_rerun_when_the_tree_changed`. `lint` appends to a counter and passes. A
failing test file written during the refactor phase makes the first close fail on the
suite; the file is then made to pass, and the second advance closes the run. Assert the
counter holds two lines.

EXPECTED: passes on arrival — probe-verified (`PIN-9 lint runs: 2`, second advance returns
`verb: complete`). This pin is the guard on cycle 11: a memo keyed on anything but the
tree hash breaks it.

### Cycle 10 — `gate_result` carries the tree hash and the skipped flag

`tests/test_release_surface.py::test_gate_result_gains_tree_hash_and_skipped_columns`,
written in the shape the two neighbouring tests already use
(`test_artifact_check_gains_regenerate_failed_column`, `test_run_gains_start_sha_column`):
a fresh ledger has both columns, and a ledger forced back to `schema_version = '10'` with
the columns dropped has them again after reopening. One schema change, one test — the
repo's own convention for this exact kind of cycle.

Production target: `src/tddcli/ledger.py` — `SCHEMA_VERSION = 11`, the `gate_result`
`CREATE TABLE` gains `tree_hash TEXT` and `skipped INTEGER NOT NULL DEFAULT 0`, and
`MIGRATIONS[10]` is the two `ALTER TABLE gate_result ADD COLUMN` statements.

EXPECTED FAILURE: `AssertionError: assert 'tree_hash' in {'at', 'cycle_id', 'id', 'kind',
'ok', 'output', 'project', 'run_id'}` — the column set of `gate_result` today.

### Cycle 11 — a gate that passed at this tree hash is not re-executed

`test_a_passing_gate_is_not_reexecuted_at_an_unchanged_tree`. `lint` appends to a counter
and passes. A failing test file written during the refactor phase makes the first close
fail on the **suite** (not the gate); the second advance is issued with nothing edited, so
the tree hash is identical. Assert the counter holds exactly one line.

Production target: `Engine.sweep`'s gate pass in `src/tddcli/machine.py` — before running a
gate, look up the latest `gate_result` for `(run_id, project, kind)` and skip when it has
`ok = 1` and `tree_hash` equal to `self.tree_hash([name])`.

EXPECTED FAILURE: `assert 2 == 1` — probe-verified: today lint runs on both closes, and
both CLOSE_SWEEP invocations record the identical `tree_hash`
(`adcac50b2288...`), which is what makes the skip sound.

### Cycle 12 — a skipped gate still records a `gate_result` row, marked skipped

`test_a_skipped_gate_records_a_skipped_row`. Same scenario as cycle 11. Assert
`[r["skipped"] for r in gate_result rows where project='backend' and kind='lint'] == [0, 1]`
— the first close ran the gate, the second skipped it.

Production target: `Engine.sweep` — the skip path inserts `gate_result` with `ok = 1`,
`skipped = 1`, the current `tree_hash`, empty `output`.

EXPECTED FAILURE: `assert [0] == [0, 1]` once cycle 11's skip suppresses the second row.
If cycle 11's implementation already wrote the row, this test passes on arrival and the
tool's sensitivity check applies — do not reclassify the cycle as a pin.

### Cycle 13 — refactor: amend the PRD and the changelog

No test; the suite is the guard. `docs/PRD.md` is normative here ("changes to specified
behaviour amend this document in the same PR"):

- **R9.2** — state that the close sweep runs lint and typecheck for every project in
  scope **before** any suite, and returns without running a suite when a gate fails.
- **R9.11** — state that the gate pass stops at the first failing gate, that
  `Adapter._gate` stops at the first failing command, and that a gate whose project tree
  hash is unchanged since that gate last passed within the run is skipped and recorded
  with `skipped = 1`. Name the limit from decision 4 (gate configuration outside the
  project's roots does not invalidate the memo).
- **§5 ledger table listing** — `gate_result` gains `tree_hash` and `skipped`.
- `CHANGELOG.md` — a `## [Unreleased]` entry under `### Changed` covering the reorder,
  the short-circuit, the wording change to the `fix_regression` detail, and schema v11.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-129-gates-before-suite   # first, before anything else
    tdd doctor                                     # must report healthy: true
    tdd run start --plan tasks/issue-129-gates-before-suite.md

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

**Referee.** This plan changes `src/tddcli/ledger.py`'s `SCHEMA_VERSION` to 11, and the
released 0.11.0 tool understands up to 10. Build the frozen snapshot referee from the plan
commit *before the first cycle edit* and never rebuild it mid-run:

    uv venv /tmp/tdd-referee-129
    uv pip install --python /tmp/tdd-referee-129/bin/python .
    /tmp/tdd-referee-129/bin/tdd doctor

Use that binary as `tdd` for every command in this plan.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is
  green at the plan commit; expect `baselines: {tddcli: 0}` and no standing failures.
- Verbs this plan will hit: `write_test`, `write_implementation`, `refactor_or_advance`,
  `create_stub` (none expected — no cycle declares a stub), `run_sensitivity_check` →
  `tdd sensitivity begin|check|end` (cycles 1, 2, 8, 9 are pin cycles and will ask for it),
  `resolve_blocker` → `tdd blocker --kind <no_baseline_for_project|plan_defect|environment> --detail '...'`,
  `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`. This plan
  declares no annotation keys, so `annotate_cycle` should not appear.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- cycle 3 adds the early `return` inside `_gate`'s loop, and nothing else.
- cycle 4 makes the two gates lazy and stops the gate pass at the first failing gate —
  the suite still runs first at this point, and nothing about ordering changes.
- cycle 5 moves the gate pass ahead of the suite loop and returns early on failure, for
  the cycle's own single project — no memo, no new columns.
- cycle 6 splits the sweep into one loop over all projects' gates and a second loop over
  all projects' suites — no wording change.
- cycle 7 changes the one detail string in `advance.py`, and nothing else.
- cycle 10 changes `SCHEMA_VERSION`, the `gate_result` DDL and `MIGRATIONS` — `sweep()`
  does not yet write or read either new column.
- cycle 11 writes `tree_hash` on every gate row and skips a gate whose latest row for
  `(run_id, project, kind)` is `ok = 1` at that hash — the skip path writes no row yet.
- cycle 12 adds the `skipped = 1` row on the skip path, and nothing else.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-129-gates-before-suite-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-129-gates-before-suite-friction.md
    git commit -m "docs: friction log for issue-129-gates-before-suite"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

Docs are deliverables, not hopes — cycle 13 owns them:

- `git diff --stat origin/main -- docs/PRD.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.

Nothing a user *sees* changes outside the JSON envelope, so no demo recording is required;
quote the new `fix_regression` envelope in the PR body instead.
