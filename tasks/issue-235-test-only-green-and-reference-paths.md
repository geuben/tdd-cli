---
closes: 235
cycles:
  - n: 1
    project: tddcli
    title: "a GREEN whose staged set is only test files records green_without_implementation"
    test: "tests/test_green_without_implementation.py::test_green_without_implementation_fires_only_when_every_staged_path_is_a_test"
    files: ["src/tddcli/advance.py", "docs/PRD.md"]
    commit_red: "test: a GREEN of only test files must record green_without_implementation"
    commit_green: "feat: record green_without_implementation when GREEN stages only test files"
    commit_refactor: "refactor: tidy the test-only GREEN check"
  - n: 2
    project: tddcli
    title: "green_without_implementation is a nudge: the GREEN reply asks for a tdd note"
    test: "tests/test_green_without_implementation.py::test_a_green_of_only_test_files_asks_for_a_note"
    files: ["src/tddcli/advance.py", "README.md", "CHANGELOG.md"]
    commit_red: "test: a GREEN of only test files must ask for a tdd note"
    commit_green: "feat: green_without_implementation is a nudge"
    commit_refactor: "refactor: tidy the nudge kinds"
  - n: 3
    project: tddcli
    pin_cycle: true
    title: "the friction log shows green_without_implementation in the cycle's section"
    test: "tests/test_green_without_implementation.py::test_the_friction_log_shows_green_without_implementation_in_the_cycle_section"
    files: ["src/tddcli/render.py"]
    commit_pin: "test: pin — the friction log shows green_without_implementation beside the cycle's commits"
  - n: 4
    project: tddcli
    title: "reference_paths parses as a list of strings, and anything else is a contract error"
    test: "tests/test_reference_paths.py::test_reference_paths_parse_as_a_list_of_strings_or_fail"
    stub_expected: ["src/tddcli/contract.py"]
    files: ["src/tddcli/contract.py", "docs/PRD.md", "README.md"]
    commit_red: "test: reference_paths must parse as a list of strings or fail"
    commit_green: "feat: parse the plan-level reference_paths key"
    commit_refactor: "refactor: tidy the front-matter path-list parsing"
  - n: 5
    project: tddcli
    title: "plan register stores the contract's reference_paths in the ledger"
    test: "tests/test_reference_paths.py::test_plan_register_stores_reference_paths"
    stub_expected: ["src/tddcli/ledger.py"]
    files: ["src/tddcli/ledger.py", "src/tddcli/cli.py"]
    commit_red: "test: plan register must store reference_paths"
    commit_green: "feat: store a contract's reference_paths in a new ledger table"
    commit_refactor: "refactor: tidy the reference path ledger methods"
  - n: 6
    project: tddcli
    title: "an uncommitted change to a reference path blocks the run, in every phase"
    test: "tests/test_reference_paths.py::test_touching_a_reference_path_blocks_the_run_in_every_phase"
    files: ["src/tddcli/advance.py", "src/tddcli/machine.py", "docs/PRD.md", "README.md", "CHANGELOG.md"]
    commit_red: "test: touching a reference path must block the run in every phase"
    commit_green: "feat: a changed reference path is a reference_path_touched blocker"
    commit_refactor: "refactor: tidy the reference path gate"
  - n: 7
    project: tddcli
    title: "a reference path committed behind the tool's back blocks the next advance"
    test: "tests/test_reference_paths.py::test_a_reference_path_committed_behind_the_tool_blocks_the_next_advance"
    files: ["src/tddcli/gitutil.py", "src/tddcli/machine.py"]
    commit_red: "test: a reference path committed since run start must block"
    commit_green: "feat: reference paths are compared with the run's start commit"
    commit_refactor: "refactor: tidy the committed-since lookup"
  - n: 8
    project: tddcli
    title: "a reference path an artifact regenerates at close blocks the run"
    test: "tests/test_reference_paths.py::test_a_reference_path_regenerated_at_close_blocks_the_run"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: a reference path regenerated at close must block"
    commit_green: "feat: re-check reference paths after a close regenerates artifacts"
    commit_refactor: "refactor: tidy the post-regeneration reference check"
  - n: 9
    project: tddcli
    title: "the friction log shows reference_path_touched in the cycle's section"
    test: "tests/test_reference_paths.py::test_the_friction_log_shows_reference_path_touched_in_the_cycle_section"
    files: ["src/tddcli/advance.py", "docs/PRD.md"]
    commit_red: "test: the friction log must show reference_path_touched beside the cycle's commits"
    commit_green: "feat: record reference_path_touched as an integrity event on the cycle"
    commit_refactor: "refactor: tidy the reference path blocker reply"
---

# A test-only GREEN is flagged, and a plan's reference paths are read-only to its run

## Context

[#235](https://github.com/geuben/tdd-cli/issues/235): a GREEN commit is supposed to hold the
implementation that turns the target green, and nothing checks that it does. In a real
agent-driven run, three cycles of one plan went like this:

1. RED created empty expected-output files under `tests/expected/` beside a test comparing a
   producer's output with them.
2. GREEN filled them with the producer's own current output and changed no source.
3. The ledger recorded a clean red to green. The test now only asserted that the producer
   agreed with itself, and a real rendering defect shipped.

The issue asks for three things:

1. **Event:** at GREEN, with no implementation in a non-empty staged set, emit
   `green_without_implementation` (a nudge in `NUDGE_KINDS`) listing the paths. The reply asks
   the executor to `tdd note` why. It is a nudge, not a gate, because a cycle whose fix really
   is a test helper is legitimate (#141).
2. **Read-only reference paths:** an optional plan front-matter key, "for example
   `reference_paths: [...]`", lists golden or reference files the run must not write. Touching
   one in any phase is a typed blocker, which gives a plan built on independently produced
   expectations "a hard guarantee".
3. **Rendering:** both appear in the friction log next to the cycle's commits.

[#141](https://github.com/geuben/tdd-cli/issues/141) is the RED-side twin. It is open and
waiting on a person's decision (its `needs-decision` comment, 2026-10-29). Nothing here depends
on it. If #141 later lets a cycle declare a test-path file as its implementation, that file is
classified `implementation`, and this plan's event then does not fire for it (decision 1), which
is the right outcome.

There is no investigation report on the issue and no `investigate/issue-235` branch. Every claim
below comes from the planning probes.

### What the planning probes found (E-2, run in a fresh worktree of `origin/main`)

| Probe | Result |
|---|---|
| Full suite in a fresh `git worktree` of `origin/main`, no setup script | `869 passed`. `uv run ruff check` and `uv run mypy` both clean. |
| The issue's scenario: RED writes an empty `backend/tests/expected/out.txt` and a test comparing it with `"42\n"`; GREEN writes `42` into it | GREEN confirmed. `staging.classify` gave `tests=['backend/tests/expected/out.txt']`, `implementation=[]`. No integrity event. **The issue, reproduced.** |
| An ordinary stub-then-fill cycle (`stub_expected: ["app/calc.py"]`, GREEN fills `calc.py`) | GREEN's classification is `stubs=['backend/app/calc.py']`, **`implementation=[]`**. A declared stub is classified `stubs` in every phase, not only in RED. |
| The issue's literal rule (`not classification.implementation` and non-empty staged set), hacked in | Fires on the stub-filled cycle (`[['backend/app/calc.py']]`) and on an ancillary-only GREEN (`[['docs/notes.md']]`): both are implementation. **The literal rule is wrong** (decision 1). |
| A flaky target (fails on its first execution only), GREEN with nothing changed and a plain `advance` | GREEN confirmed with `staged` empty and `commit: null`: the no-change guard compares invocations of the same phase only. So "staged set non-empty" is a real condition. |
| A plan with an unknown top-level `reference_paths` key on 0.17.0 | Registers and runs: `contract.parse` ignores unknown top-level keys. |
| A regenerate-only `[artifact.openapi]` (no `check`) whose path is a plan's reference path | `run start` regenerates it and commits `chore(openapi): regenerate` **after** `start_sha`. |
| The same artifact with `check = "test ! -f <marker>"` and `regenerate = "printf 'v2\n' > schema/openapi.json && rm -f <marker>"`, marker created after `run start`, one refactor cycle | The first `advance` regenerates and commits during the close and ends the run `complete`: `result.regenerated == ["openapi"]`. |
| A throwaway version of decisions 1 and 2 plus a ledger read on every `advance`, full suite | `869 passed`. **No existing test breaks; no cycle declares `modifies_tests`.** The hack was discarded. |

## Design decisions (locked)

Each decision says what settled it. None was settled by a person; the plan PR's review is where a
person can disagree.

1. **`green_without_implementation` fires when GREEN's staged set is non-empty and every staged
   path is classified as a test.** In `advance._handle_impl`, after GREEN's `_stage_and_commit`,
   the condition is `staged and set(staged) <= set(classification.tests)`. A declared stub, an
   implementation file or an ancillary file in the staged set means it does not fire.
   *Settled by evidence.* The issue's literal wording ("`classification.implementation` is
   empty") also fires on every stub-then-fill cycle, because `staging.classify` puts a declared
   `stub_expected` file in `stubs` in every phase, and on an ancillary-only GREEN (both probed
   above). That would make the nudge fire on correct work, which an executor learns to ignore.
   The issue's title ("touches only test_paths files") and its scenario both describe exactly
   "every staged path is a test". **Mechanism footgun:** `set() <= anything` is `True`, so the
   `staged and` guard is what keeps an empty GREEN quiet. The `nothing_staged` case pins it.
2. **The event is recorded on the cycle, with `detail = json.dumps(staged)`,** where `staged` is
   the list `_stage_and_commit` returns (sorted paths, repo-relative). *Settled by convention:*
   `implementation_during_red` and `undeclared_file_touched` carry their path list as a JSON
   array on the cycle, via `engine.ledger.event(run_id, cycle_id, kind, json.dumps(paths))`.
3. **It is a nudge: `green_without_implementation` joins `NUDGE_KINDS`.** The existing
   `_note_nudge` then appends its note request to the GREEN reply, and to every later reply on
   that cycle until a `tdd note` exists. No new reply field and no new wording. *Settled by the
   issue* ("a nudge in `NUDGE_KINDS`", "the reply asks the executor to `tdd note` why", "not a
   gate") *and by convention* (how the other three nudges work).
4. **Only GREEN is checked.** That is `_handle_impl`, which standard and contract cycles reach.
   Pin and refactor cycles have no GREEN. *Settled by evidence* (`advance.HANDLERS`).
5. **`reference_paths` is a top-level front-matter key: a list of repo-relative paths, matched
   exactly.** Absent means none. Anything that is not a list of strings fails registration with
   `ContractError("reference_paths must be a list of strings")`, so `plan register` replies
   `malformed plan contract: reference_paths must be a list of strings` (R7.10). There are no
   globs and no directory prefixes. *Settled by the issue* (the name it proposes; "lists golden
   or reference files") *and by convention:* `ancillary_files`, the other plan-level path list,
   holds exact repo-relative paths, and is validated in `contract.parse` with this same message
   shape.
6. **The ledger stores them in a new table, with no `SCHEMA_VERSION` bump.** The table is
   `plan_reference_path (id INTEGER PRIMARY KEY, contract_id INTEGER NOT NULL REFERENCES
   plan_contract(id), path TEXT NOT NULL)`, added to `SCHEMA` as `CREATE TABLE IF NOT EXISTS`.
   It has two `Ledger` methods, both keyed by `contract_id`:
   - `add_reference_paths(self, contract_id: int, paths: list[str]) -> None`, in
     `GUEST_WRITES`;
   - `reference_paths(self, contract_id: int) -> list[str]`, in `GUEST_READS`, in insertion
     order (`ORDER BY id`).

   `cmd_plan_register` calls `add_reference_paths` only when it inserts a new contract **and**
   `parsed.reference_paths` is non-empty. A re-registered blob reuses its contract and its rows.
   *Settled by convention:*
   - a new table needs no bump or frozen referee (`.claude/plan-issue.md`, #150; `abandonment`
     was added the same way);
   - a column on `plan_contract` would be an `ALTER TABLE` and a bump;
   - `contract_id` is already one of the owners `service._Session._foreign` checks
     (`.claude/plan-issue/ledger-guest-ownership.md`), so no service change is needed;
   - `register_contract`'s signature is unchanged, because a new keyword argument on an existing
     guest write breaks a socket-mode host on the previous release.

   The new read is made on every `advance`, so a 0.17.0 ledger-service host refuses a newer
   guest's advance with `method_not_allowed`. That is the upgrade note #97 already set for
   `delivered_run` (CHANGELOG 0.17.0): upgrade the host with or before its guests. The
   CHANGELOG entry says so.
7. **"Touched" means the path differs from the run's start.** The touched set is
   `reference_paths ∩ (engine.authored_changes(cycle) ∪ gitutil.committed_since(worktree,
   run["start_sha"]))`:
   - `authored_changes` is uncommitted worktree changes, less pre-existing dirt (R9.21);
   - `committed_since` (new, cycle 7) is `git diff --name-only <start_sha> HEAD`, through
     `gitutil.git`, so the actor runs the spawn;
   - a run with no `start_sha` (it predates the column) uses the worktree part only.

   A deleted reference path counts, because `git status` lists deletions.
   *Settled by evidence:* `authored_changes` sees only uncommitted changes. A reference path can
   reach `HEAD` without passing through it, in three probed or read ways: a manual
   `git commit`; `run start`'s own artifact regeneration, which commits after `start_sha`; and a
   close's regeneration. The issue asks for "a hard guarantee" that the run does not write
   them. A path changed and then restored to its start content is not touched, which is right:
   the run did not change it.
8. **Where it is checked:**
   - at the top of `advance.advance`, after `_check_config_drift` and the open-sensitivity
     early return, and before the no-change guard and the phase handler;
   - again in `_handle_refactor`, right after the artifact `failed`/`stale` returns and before
     the sweep, because a close's regeneration happens after the top check (cycle 8).

   *Settled by evidence:* every phase is left through `advance`, so the top check covers RED,
   pin, GREEN and the close. It runs before anything is staged, so a touched path is never
   committed by the tool. A sensitivity mutation is deliberate and is restored byte-identical
   by `sensitivity end`, and `advance` already refuses while a check is open, so mutating a
   golden file to prove a pin bites is never a block.
9. **The consequence is a typed blocker raised by the tool: `reference_path_touched`.** When the
   touched set is non-empty, `advance`:
   - records an integrity event `reference_path_touched` on the cycle, with `detail =
     json.dumps(touched)` (cycle 9);
   - adds a blocker of the same kind with the same detail (`ledger.add_blocker`);
   - ends the run `blocked` (`ledger.end_run(run_id, "blocked")`);
   - replies with an envelope shaped like the run-close gate's: `run.phase == "BLOCKED"`,
     `result == {"kind": "reference_path_touched", "paths": touched}`, `next_action.verb ==
     "blocked"`.

   The detail names the paths, says that the plan declares them read-only, and says to restore
   them to the run's start and `tdd resume --unblock --note "..."`. Nothing is staged. A later
   `advance` with the path still touched blocks again.

   The kind is not added to `cli.BLOCKER_KINDS`: those are the kinds an executor files with
   `tdd blocker`, and the tool's own `undeclared_file_uncommitted` is not in that list either.
   *Settled by the issue* ("a typed blocker", "a hard guarantee"), *by PRD P2* (a plan-declared
   read-only path is unambiguous, which is P2's exception for enforcement), *and by convention*
   (`undeclared_file_uncommitted`: an event that names the paths, a tool-raised blocker of the
   same family, `outcome = blocked`, and the `blocked` verb).
10. **Rendering needs no change to `render.py`.** `render.friction_log` already prints every
    cycle event, as `- **Event — <kind>:** <detail>`, right after that cycle's `Commits` lines.
    Blockers render only in the closing `## Blockers` section, which is why decision 9 also
    records the event on the cycle. *Settled by evidence* (the `render.friction_log` loop; the
    probe's rendered log) *and by convention* (`undeclared_file_touched` beside
    `undeclared_file_uncommitted`).
11. **Docs move with the behaviour, and `CHANGELOG.md` gets two `### Added` lines under
    `## [Unreleased]`.** The PRD gains:
    - R9.14b (the event), after R9.14a;
    - R7.11a (the key, and its gate), after R7.11;
    - both kinds in §5's IntegrityEvent list, and `reference_path_touched` in §5's Blocker list;
    - a §12 hard-gate bullet.

    `README.md` gains a `reference_paths` paragraph under **Top-level keys**, a new subsection
    after "Run-close gate for undeclared file touches", a sentence in "What the tool does", and
    a hard-gate clause in "Enforcement boundary". The exact text is in the cycles. *Settled by
    convention* (`RELEASING.md`; #98's and #70's plans).

## Not in scope (not asked for)

These are not cuts of anything the issue asks for. Rule 4 (no future-proofing) keeps them out:

- **A register-time check that `reference_paths` exist, or do not overlap a cycle's `files`,
  `stub_expected` or `ancillary_files`.** The issue does not ask for one, and the run-time
  blocker already makes such a plan stop the first time the path changes.
- **Directory or glob entries in `reference_paths`** (decision 5).
- **A `green_without_implementation` field in the GREEN reply's `result`.** The issue asks for
  an event and a note request, and both are built.
- **Documenting `reference_paths` in `examples/plan.md` or `examples/skills/tdd-handoff/`.**
  Neither documents `ancillary_files`, and `tests/test_example_plan.py` does not require
  top-level keys.

## Fake/real divergence

None. Every end-to-end test drives the real CLI in-process (`conftest.run_cli`) over a real git
repository (the `repo` fixture), with real pytest suites and real artifact hooks.

## Invariants, mirrors, sweeps

- There is no `docs/INVARIANTS.md` in this repo, and no `perturb/` ledger.
- **Mirrors:** none. `staging.classify` and `advance` have no counterpart implementation.
- **Guard tests that constrain this plan's files:**
  - `tests/test_ledger_surface.py::test_every_ledger_method_is_classified_and_scoped` forces
    both new `Ledger` methods into `GUEST_READS`/`GUEST_WRITES` with a `contract_id`
    parameter (cycle 5).
  - `tests/test_actor_seams.py` forces the new git call through `gitutil.git` (cycle 7).
  - Neither changes, so neither is in `modifies_tests`.
- **Sweeps:** none.

## Cycles

Two new test files hold every test:

- **`tests/test_green_without_implementation.py`** (cycles 1–3). Module docstring: `"""A GREEN
  whose staged set is only test files is flagged, not silently accepted (#235)."""`. Imports:
  `from __future__ import annotations`, `json`, `shutil`, `from conftest import run_cli,
  run_cli_text, write_plan`, `from tddcli import gitutil`, `from tddcli.ledger import Ledger`.
- **`tests/test_reference_paths.py`** (cycles 4–9). Module docstring: `"""A plan's
  reference_paths are read-only to its run: changing one blocks it (#235)."""`. Imports:
  `from __future__ import annotations`, `shutil`, `from conftest import git, run_cli,
  run_cli_text, write_plan`, `from tddcli import gitutil`, `from tddcli.contract import
  ContractError, parse`, `from tddcli.ledger import Ledger`.

Every name imported exists today, so neither file fails to collect in any cycle. Cycle 1 creates
the first file and cycle 4 the second. Each later cycle appends its test and any helper it is
the first to need. A test runs one end-to-end setup per case by copying the `repo` fixture with
`shutil.copytree(repo, tmp_path / name)` before any run starts. Each copy has its own ledger
(`.claude/plan-issue/testing-execution-counter-flake.md`), so each copy's run id is 1. Read it
from `run start`'s envelope anyway.

### Fixture values: every cycle uses exactly these

`tests/test_green_without_implementation.py`:

```python
EXPECTED = "backend/tests/expected/out.txt"

GOLDEN_TEST = '''import pathlib


def test_output_matches_golden():
    expected = (pathlib.Path(__file__).parent / "expected" / "out.txt").read_text()
    assert expected == "42\\n"
'''
```

Five one-cycle plans (front-matter only, then a blank line and `# Plan`), all `project: backend`:

| Plan | `title` | `test` | Extra keys |
|---|---|---|---|
| `PLAN_GOLDEN` | `"output matches the golden file"` | `tests/test_golden.py::test_output_matches_golden` | — |
| `PLAN_STUB` | `"adding two numbers"` | `tests/test_add.py::test_add_two_numbers` | `stub_expected: ["app/calc.py"]` |
| `PLAN_VALUE` | `"the package exposes VALUE"` | `tests/test_value.py::test_value` | — |
| `PLAN_NOTES` | `"the notes say 42"` | `tests/test_notes.py::test_notes` | top-level `ancillary_files: ["docs/notes.md"]` |
| `PLAN_FLAKY` | `"flaky"` | `tests/test_flaky.py::test_flaky` | — |

Helpers. Each `_case(repo, scratch)` returns `(run_id, green_envelope)`:

- `_start(repo, plan_text)`:
  1. `write_plan`, then `plan register`;
  2. `run start --plan`, asserting `ok`;
  3. return `run["id"]`.
- `_golden_red(repo)`:
  1. create `backend/tests/expected/` and write an **empty** `out.txt`;
  2. write `GOLDEN_TEST` to `backend/tests/test_golden.py`;
  3. `advance`, asserting the verb is `write_implementation`.
- `_tests_only`: `_start(PLAN_GOLDEN)`, `_golden_red`, write `"42\n"` to `EXPECTED`, `advance`.
- `_tests_and_implementation`: as `_tests_only`, also writing `"VALUE = 1\n"` to
  `backend/app/__init__.py` before the `advance`.
- `_stub_filled`:
  1. `_start(PLAN_STUB)`;
  2. write `backend/tests/test_add.py` (`from app.calc import add` / `def
     test_add_two_numbers(): assert add(2, 3) == 5`) and the stub `backend/app/calc.py` (`def
     add(a, b): raise NotImplementedError`);
  3. `advance` (asserting `write_implementation`);
  4. write `return a + b` into `calc.py`;
  5. `advance`.
- `_implementation`:
  1. `_start(PLAN_VALUE)`;
  2. write `backend/tests/test_value.py` (`import app` / `def test_value(): assert
     getattr(app, "VALUE", None) == 1`);
  3. `advance` (asserting `write_implementation`);
  4. write `"VALUE = 1\n"` to `backend/app/__init__.py`;
  5. `advance`.
- `_ancillary_only`:
  1. `_start(PLAN_NOTES)`;
  2. write `backend/tests/test_notes.py`, which reads `pathlib.Path(__file__).parents[2] /
     "docs" / "notes.md"` (`""` when it is absent) and asserts it equals `"42\n"`;
  3. `advance` (asserting `write_implementation`);
  4. create `docs/` and write `"42\n"` to `docs/notes.md`;
  5. `advance`.
- `_nothing_staged`:
  1. `_start(PLAN_FLAKY)`;
  2. write `backend/tests/test_flaky.py`. It counts its executions in `scratch / "flaky-count"`,
     a directory **outside** the repo, with its absolute path written into the source, and
     asserts `n > 1`;
  3. `advance` (RED, execution 1, asserting `write_implementation`);
  4. `advance` again with **no change** (GREEN: the target run is execution 2 and the suite run
     is execution 3; both pass, and nothing is staged).

`tests/test_reference_paths.py`:

```python
REFERENCE = "backend/tests/expected/out.txt"
TEST_ADD = "from app.calc import add\n\n\ndef test_add_two_numbers():\n    assert add(2, 3) == 5\n"
STUB = "def add(a, b):\n    raise NotImplementedError\n"
REAL = "def add(a, b):\n    return a + b\n"
```

- `PLAN_ADD`: one standard cycle (`title: "adding two numbers"`, `test:
  "tests/test_add.py::test_add_two_numbers"`, `stub_expected: ["app/calc.py"]`) and top-level
  `reference_paths: ["backend/tests/expected/out.txt"]`.
- `PLAN_PIN`: one cycle (`pin_cycle: true`, `title: "smoke still passes"`, `test:
  "tests/test_pin.py::test_pin"`) and the same `reference_paths`.
- `PLAN_REFACTOR`: one cycle (`refactor_cycle: true`, `title: "behaviour-preserving cleanup"`)
  and `reference_paths: ["schema/openapi.json"]`.
- Helpers:
  - `_commit_reference(repo)`: create `backend/tests/expected/`, write `"reference\n"` to
    `REFERENCE`, then `git add -A` and commit `"an independently produced reference file"`.
    Call it **before** `write_plan`, so the path is clean at `run start`.
  - `_start(repo, plan_text)`: as above, returning the envelope.
  - `_red(repo)`: write `TEST_ADD` to `backend/tests/test_add.py` and `STUB` to
    `backend/app/calc.py`.
  - `_touch(repo)`: write `"overwritten by the run\n"` to `REFERENCE`.

### Cycle 1: a GREEN whose staged set is only test files records `green_without_implementation`

- **Behaviour:** decisions 1, 2 and 4. The event fires exactly when every staged path is a test.
- **Test:** `test_green_without_implementation_fires_only_when_every_staged_path_is_a_test(repo,
  tmp_path)`. For each case in this table, copy `repo` to `tmp_path / name`, make `tmp_path /
  f"{name}-scratch"`, and call the case helper:

  | Case | Helper |
  |---|---|
  | `tests_only` | `_tests_only` |
  | `tests_and_implementation` | `_tests_and_implementation` |
  | `stub_filled` | `_stub_filled` |
  | `implementation` | `_implementation` |
  | `ancillary_only` | `_ancillary_only` |
  | `nothing_staged` | `_nothing_staged` |

  For each case, record `seen[name] = (green["next_action"]["verb"], [json.loads(d) for d in
  Ledger(gitutil.repo_identity(copy)).event_details(run_id,
  "green_without_implementation")])`. Single assertion:

  ```python
  assert seen == {
      "tests_only": ("refactor_or_advance", [[EXPECTED]]),
      "tests_and_implementation": ("refactor_or_advance", []),
      "stub_filled": ("refactor_or_advance", []),
      "implementation": ("refactor_or_advance", []),
      "ancillary_only": ("refactor_or_advance", []),
      "nothing_staged": ("refactor_or_advance", []),
  }
  ```

  The verb in each tuple proves that GREEN was confirmed, so an absent event is never vacuous.
  The expected paths come from the fixture constant, not from production code.
- **Production target:**
  - `advance._handle_impl`: keep `_stage_and_commit`'s classification (today it is discarded as
    `_`) and record the event under decision 1's condition, before `engine.transition`;
  - `docs/PRD.md`:
    - add `green_without_implementation` to §5's IntegrityEvent typed list;
    - add after R9.14a: *"**R9.14b** If GREEN's staged set is non-empty and every path in it is
      a test (R9.13's `test_paths`), the cycle records `green_without_implementation` with the
      staged paths. A declared stub, an implementation file or an ancillary file in the set is
      implementation, so it does not fire. It is a nudge, not a gate: a cycle whose fix really
      is test support is legitimate (#141), so the reply asks for a `tdd note` saying why. A
      GREEN that fills golden files with the producer's own output looks exactly like this
      (#235)."*
- **EXPECTED FAILURE** (probed with exactly this test on `origin/main`): `AssertionError` on the
  dict. Five items are identical, and the one differing item is `{'tests_only':
  ('refactor_or_advance', [])} != {'tests_only': ('refactor_or_advance',
  [['backend/tests/expected/out.txt']])}`. Probed after-states (hacked, then discarded): the
  issue's literal rule fails this test on `stub_filled` and `ancillary_only`, and decision 1's
  rule passes it.

### Cycle 2: `green_without_implementation` is a nudge, so the GREEN reply asks for a note

- **Behaviour:** decision 3.
- **Test:** `test_a_green_of_only_test_files_asks_for_a_note(repo, tmp_path)`: `_, green =
  _tests_only(repo, tmp_path)`. Single assertion: `assert "tdd note" in
  green["next_action"]["detail"]`. Nothing else in this flow records a nudge: RED staged only
  test files.
- **Production target:**
  - `advance.NUDGE_KINDS` gains `"green_without_implementation"`;
  - `README.md`, "What the tool does, that agents do not": add to the **Stages and commits**
    bullet: *"A GREEN that stages only test files (golden files filled with the producer's own
    output look exactly like this) records a `green_without_implementation` nudge, and the
    reply asks for a `tdd note` saying why."*;
  - `CHANGELOG.md`, under `## [Unreleased]`, `### Added`: *"**A GREEN that stages only test
    files is flagged** (#235). When every path GREEN commits is a test, as when golden files
    are filled with the producer's own output, the cycle records a
    `green_without_implementation` integrity event listing them. It is a nudge: the reply asks
    for a `tdd note` saying why, and nothing is blocked. A declared stub, an implementation
    file or an ancillary file in the commit means implementation was written, so it does not
    fire."*
- **EXPECTED FAILURE** (probed: on `origin/main`, and with cycle 1's increment hacked in):
  `AssertionError: assert 'tdd note' in 'GREEN confirmed. Refactor if the plan calls for it,
  then `tdd advance` to close the cycle.'`

### Cycle 3 (pin): the friction log shows `green_without_implementation` in the cycle's section

- **Behaviour:** the issue's third item, for the event (decision 10).
- **Test:** `test_the_friction_log_shows_green_without_implementation_in_the_cycle_section(repo,
  tmp_path)`:
  1. `_tests_only(repo, tmp_path)`;
  2. `run_cli(repo, "advance")`, which closes the cycle;
  3. `text = run_cli_text(repo, "log", "render")`;
  4. `section = text.split("### Cycle 1", 1)[1].split("\n## ", 1)[0]`, which is the cycle's
     block, holding its `Commits` lines.

  Single assertion: `assert f'- **Event — green_without_implementation:** ["{EXPECTED}"]' in
  section`.
- **Why a pin:** `render.friction_log` prints every cycle event after the commits. Once cycle 1
  records the event, this passes on arrival (probed with cycles 1–2 hacked in: passed). Before
  cycle 1 it fails with `assert '- **Event — green_without_implementation:**
  ["backend/tests/expected/out.txt"]' in ': output matches the golden file _(standard)_ ...'`
  (probed). For the sensitivity check, mutate the event loop in `render.friction_log` (for
  example skip events of this kind), confirm the failure, then `tdd sensitivity end`.
- **If it fails on arrival:** do not edit production code in a pin cycle. File `tdd blocker
  --kind plan_defect --detail '...'`, quoting the rendered cycle section.

### Cycle 4: `reference_paths` parses as a list of strings, and anything else is a contract error

- **Behaviour:** decision 5. The accepted form, the absent default and every rejected form go in
  one table, so the validation cannot pre-pass a later cycle. It sits next to `ancillary_files`
  in the same function.
- **Stub (RED):** `PlanContract` gains `reference_paths: list[str] =
  field(default_factory=list)`, declared after `ancillary_files`. `parse` is unchanged. That is
  the whole stub.
- **Test:** `test_reference_paths_parse_as_a_list_of_strings_or_fail()`. Each case's
  front-matter is `cycles: [{n: 1, project: backend, test: "tests/test_a.py::test_a"}]`, plus
  the line `reference_paths: <value>` (no line for `absent`):

  | Case | `<value>` |
  |---|---|
  | `absent` | — |
  | `list` | `["backend/tests/expected/out.txt", "docs/ref.bin"]` |
  | `string` | `"docs/ref.bin"` |
  | `number` | `[1]` |
  | `mapping` | `{a: b}` |

  Record `seen[name] = parse(text, "tasks/plan.md").reference_paths`, or `str(exc)` on
  `ContractError`. Single assertion:

  ```python
  assert seen == {
      "absent": [],
      "list": ["backend/tests/expected/out.txt", "docs/ref.bin"],
      "string": "reference_paths must be a list of strings",
      "number": "reference_paths must be a list of strings",
      "mapping": "reference_paths must be a list of strings",
  }
  ```
- **Production target:**
  - `contract.parse`: read `data.get("reference_paths", [])`, validate it as `ancillary_files`
    is validated, and pass it to `PlanContract`;
  - `docs/PRD.md` §7.2, after R7.11: *"**R7.11a** `reference_paths` (top-level, optional) lists
    repo-relative paths the run must not write: golden or reference files produced
    independently of the code under test. Paths match exactly. A value that is not a list of
    strings fails registration (R7.10). At every `advance`, and again after a close regenerates
    artifacts, a listed path that differs from the run's start (changed in the worktree, or
    committed since `start_sha`) records `reference_path_touched` on the cycle, adds a blocker
    of that kind and ends the run `blocked`, before anything is staged. Pre-existing dirt
    (R9.21) is not counted. A sensitivity mutation is never checked: `advance` refuses while
    one is open, and `sensitivity end` restores the tree (#235)."*;
  - `README.md`, **Top-level keys**, after the `ancillary_files` paragraph: *"`reference_paths`
    — a plan-level list of repo-root-relative paths the run must not write: golden or reference
    files produced independently of the code under test, which a test compares against. Paths
    match exactly. Changing one in any phase blocks the run (see "Reference paths are read-only"
    below)."*
- **EXPECTED FAILURE** (probed on `origin/main` without the stub: `AttributeError:
  'PlanContract' object has no attribute 'reference_paths'`; with the stub, from the code):
  `AssertionError` on the dict, with `absent` identical and four differing items:
  `{'list': []}`, and `{'string': []}`, `{'number': []}`, `{'mapping': []}` against their error
  strings.

### Cycle 5: `plan register` stores the contract's `reference_paths`

- **Behaviour:** decision 6.
- **Stub (RED), all in `src/tddcli/ledger.py`:**
  - `def reference_paths(self, contract_id: int) -> list[str]: return []`;
  - `"reference_paths"` added to `GUEST_READS`.

  Nothing else: no table and no write method.
- **Test:** `test_plan_register_stores_reference_paths(repo)`:
  1. `plan = write_plan(repo, PLAN_ADD)`;
  2. `registered = run_cli(repo, "plan", "register", plan)`.

  Single assertion: `assert Ledger(gitutil.repo_identity(repo)).reference_paths(registered["result"]["contract_id"]) == [REFERENCE]`.
- **Production target:**
  - `src/tddcli/ledger.py`: the `plan_reference_path` table in `SCHEMA`;
    `add_reference_paths` (inserting one row per path, through `self.insert`) in
    `GUEST_WRITES`; and `reference_paths` reading them `ORDER BY id`;
  - `cli.cmd_plan_register`: after `register_contract` inserts a **new** contract, call
    `ledger.add_reference_paths(contract_id, parsed.reference_paths)` when that list is
    non-empty.

  `SCHEMA_VERSION` and `MIGRATIONS` are unchanged. GREEN's whole-suite run includes
  `tests/test_ledger_surface.py::test_every_ledger_method_is_classified_and_scoped`, which
  fails until `add_reference_paths` is classified.
- **EXPECTED FAILURE** (probed on `origin/main` without the stub: `AttributeError: 'Ledger'
  object has no attribute 'reference_paths'`; with the stub, from the code): `AssertionError:
  assert [] == ['backend/tests/expected/out.txt']`.

### Cycle 6: an uncommitted change to a reference path blocks the run, in every phase

- **Behaviour:** decisions 7 (worktree part only), 8 (the top check) and 9 (blocker, end,
  reply). There is **no** integrity event yet: that is cycle 9.
- **Test:** `test_touching_a_reference_path_blocks_the_run_in_every_phase(repo, tmp_path)`:
  1. `_commit_reference(repo)`;
  2. for each case, copy `repo` to `tmp_path / name` and drive it;
  3. record `head = git(copy, "rev-parse", "HEAD")`;
  4. `out = run_cli(copy, "advance")`;
  5. record `seen[name] = (out["next_action"]["verb"], out["result"].get("kind"),
     out["result"].get("paths"), git(copy, "rev-parse", "HEAD") == head,
     run_cli(copy, "metrics")["result"]["runs"][0]["outcome"])`.

  | Case | Drive |
  |---|---|
  | `red` | `_start(PLAN_ADD)`, `_red`, `_touch` |
  | `green` | `_start(PLAN_ADD)`, `_red`, `advance` (asserting `write_implementation`), write `REAL` to `calc.py`, `_touch` |
  | `refactor` | as `green` but with no touch, then `advance` (asserting `refactor_or_advance`), then `_touch` |
  | `pin` | `_start(PLAN_PIN)`, write `backend/tests/test_pin.py` (`def test_pin(): assert True`), `_touch` |

  Single assertion:

  ```python
  blocked = ("blocked", "reference_path_touched", [REFERENCE], True, "blocked")
  assert seen == {"red": blocked, "green": blocked, "refactor": blocked, "pin": blocked}
  ```

  `HEAD` unchanged proves nothing was staged or committed. `outcome == "blocked"` proves the
  run ended, so the stop hook releases (R8.7).
- **Production target:**
  - `src/tddcli/machine.py`: `Engine.touched_reference_paths(self, cycle_row) -> list[str]`,
    which reads `self.ledger.reference_paths(self.contract_row["id"])`, returns `[]` when
    there are none (so no git call is made), and otherwise returns `sorted(set(refs) &
    self.authored_changes(cycle_row))`;
  - `src/tddcli/advance.py`: in `advance`, after the open-sensitivity return and before the
    no-change guard, call it. When non-empty, add the blocker, end the run `blocked`, and return
    decision 9's envelope (shape it like `_handle_refactor`'s `undeclared_file_uncommitted`
    envelope: `run` with `phase: "BLOCKED"`, `result: {"kind": ..., "paths": ...}`). Put this
    in one helper, `_reference_paths_blocked(engine, cycle, touched) -> Envelope`; cycles 8 and
    9 reuse it;
  - `docs/PRD.md`:
    - §5 Blocker typed list: add `reference_path_touched`, with the sentence *"`reference_path_touched`
      is raised by the tool, not filed with `tdd blocker`: the run changed a path its plan
      declares read-only (R7.11a)."*;
    - §12 "Hard gates inside the CLI": add *"A plan's `reference_paths` cannot change during its
      run (R7.11a)."*;
  - `README.md`:
    - a new subsection after "Run-close gate for undeclared file touches", titled `### Reference
      paths are read-only`, holding *"A plan that lists `reference_paths` relies on files
      produced independently of the code under test. At every `tdd advance`, any of them that
      differs from the run's start (changed in the worktree, or committed since the run
      started) stops the run before anything is staged. The cycle records a
      `reference_path_touched` integrity event and a blocker of the same kind, the run outcome
      is `blocked`, and `next_action.verb` is `"blocked"`, with `result.kind` and `result.paths`.
      The same check runs again after a close regenerates artifacts. To go on, restore the
      paths to their content at the run's start, then `tdd resume --unblock --note "..."`; while
      a path still differs, the next `advance` blocks again. A sensitivity check may mutate a
      reference file: `advance` is refused while the check is open, and `sensitivity end`
      restores it."*;
    - in "Enforcement boundary", **Hard gates here**, add *"a path in the plan's
      `reference_paths` cannot change during its run;"*;
  - `CHANGELOG.md`, under `### Added`: *"**Plan-level `reference_paths` are read-only to the
    run** (#235). A plan can list golden or reference files its tests compare against. If one
    differs from the run's start at any `tdd advance` (edited, deleted, committed by hand, or
    rewritten by an artifact regeneration), the run is blocked before anything is staged, with
    a `reference_path_touched` blocker and integrity event naming the paths. Restore them, then
    `tdd resume --unblock`. Plans without the key behave as before. With a ledger service,
    upgrade the host with or before its guests: a 0.17.0 host refuses the new
    `reference_paths` read, made on every `advance`, with `method_not_allowed`."*

  The CHANGELOG line describes the finished feature. Cycles 7–9 make it true, and the PR does
  not ship before they do.
- **EXPECTED FAILURE** (probed with exactly this test on `origin/main`): `AssertionError` on the
  dict, with all four items differing: `red` → `('write_implementation', None, None, False,
  None)`, `green` → `('refactor_or_advance', None, None, False, None)`, `refactor` →
  `('complete', None, None, False, 'complete')`, `pin` → `('run_sensitivity_check', None, None,
  False, None)`. After cycles 4–5 the plan's paths are stored, but nothing reads them in
  `advance`, so the dict is the same.

### Cycle 7: a reference path committed behind the tool's back blocks the next advance

- **Behaviour:** decision 7's committed part.
- **Test:** `test_a_reference_path_committed_behind_the_tool_blocks_the_next_advance(repo)`:
  1. `_commit_reference`, then `_start(PLAN_ADD)`, then `_red`;
  2. `advance` (asserting `write_implementation`);
  3. `_touch`, then `git add <REFERENCE>`, then `git commit -q -m "regenerate the golden from
     the producer"`;
  4. write `REAL` to `calc.py`;
  5. `out = advance`.

  Single assertion: `assert (out["next_action"]["verb"], out["result"].get("kind"),
  out["result"].get("paths")) == ("blocked", "reference_path_touched", [REFERENCE])`.
- **Production target:**
  - `src/tddcli/gitutil.py`: `committed_since(worktree: Path, base: str) -> set[str]`, built on
    `git(worktree, "diff", "--name-only", base, "HEAD")`, with one path per non-empty line;
  - `Engine.touched_reference_paths` unions it with `authored_changes` when
    `self.run["start_sha"]` is set.
- **EXPECTED FAILURE** (probed on `origin/main`: `AssertionError: assert ('refactor_or_advance',
  None, None) == ('blocked', 'reference_path_touched', ['backend/tests/expected/out.txt'])`).
  After cycle 6 the committed path is no longer in `authored_changes`, so GREEN is confirmed and
  the same assertion fails. This is reasoned from cycle 6's increment, not probed in that state.

### Cycle 8: a reference path an artifact regenerates at close blocks the run

- **Behaviour:** decision 8's second check point.
- **Test:** `test_a_reference_path_regenerated_at_close_blocks_the_run(repo, tmp_path)`:
  1. `marker = tmp_path / "stale-marker"`;
  2. write `"v1\n"` to `schema/openapi.json`;
  3. append to `tdd.toml`:

     ```toml
     [artifact.openapi]
     path        = "schema/openapi.json"
     produced_by = "backend"
     check       = "test ! -f <marker>"
     regenerate  = "printf 'v2\n' > schema/openapi.json && rm -f <marker>"
     ```

     with `<marker>` being `marker`'s absolute path. In Python source, write the regenerate line
     as `f"regenerate  = \"printf 'v2\\\\n' > schema/openapi.json && rm -f {marker}\"\n"`, the
     escaping `tests/test_artifact_regeneration.py` uses;
  4. `git add -A`, then commit `"declare the openapi artifact"`;
  5. `_start(PLAN_REFACTOR)`: the check passes, because there is no marker yet, so `run start`
     regenerates nothing;
  6. `marker.write_text("")`;
  7. `out = run_cli(repo, "advance")`.

  Single assertion: `assert (out["next_action"]["verb"], out["result"].get("kind"),
  out["result"].get("paths")) == ("blocked", "reference_path_touched",
  ["schema/openapi.json"])`.
- **Production target:** `advance._handle_refactor`: after the `artifact_outcome.failed` and
  `.stale` returns and before the sweep, call `engine.touched_reference_paths(cycle)` again,
  and return `_reference_paths_blocked(...)` when it is non-empty.
- **EXPECTED FAILURE** (probed on `origin/main`): `AssertionError: assert ('complete', None,
  None) == ('blocked', 'reference_path_touched', ['schema/openapi.json'])`. The close
  regenerated and committed `chore(openapi): regenerate`, then completed the run. After cycles
  6–7 the top-of-advance check runs **before** the regeneration and finds nothing, so the same
  assertion fails.

### Cycle 9: the friction log shows `reference_path_touched` in the cycle's section

- **Behaviour:** the issue's third item, for the blocker (decisions 9 and 10).
- **Test:** `test_the_friction_log_shows_reference_path_touched_in_the_cycle_section(repo)`:
  1. `_commit_reference`, then `_start(PLAN_ADD)`, `_red` and `_touch`;
  2. `run_cli(repo, "advance")`, which blocks;
  3. `text = run_cli_text(repo, "log", "render")`;
  4. `section = text.split("### Cycle 1", 1)[1].split("\n## ", 1)[0]`.

  Single assertion: `assert f'- **Event — reference_path_touched:** ["{REFERENCE}"]' in
  section`. The `## Blockers` line reads `- **reference_path_touched** (cycle …)`, which is
  different text and outside the section, so it cannot satisfy the assertion.
- **Production target:**
  - `_reference_paths_blocked` records `engine.ledger.event(run_id, cycle_id,
    "reference_path_touched", json.dumps(touched))` before the blocker;
  - `docs/PRD.md` §5 IntegrityEvent typed list: add `reference_path_touched`.
- **EXPECTED FAILURE:** `AssertionError: assert '- **Event — reference_path_touched:**
  ["backend/tests/expected/out.txt"]' in ': adding two numbers _(standard)_ ...'`. On
  `origin/main` this was probed: the section holds a RED commit and no event. After cycle 6 it
  holds `- **Commits:** none` and still no event (reasoned from cycle 6's increment).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-235-test-only-green-and-reference-paths   # first, before anything else
    tdd doctor                                  # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-235-test-only-green-and-reference-paths.md   # captures baselines, opens cycle 1

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
  tool stages and commits, deriving the file set from the phase. (Cycle 7's test runs `git
  commit` inside its own temporary fixture repo. That is test code, not you committing.)
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is green
  at the plan's base (verified in a fresh worktree of `origin/main`: `869 passed`). Expect
  `baselines: {tddcli: 0}`.
- The referee is the released `tdd` on `PATH` (the note at the top of `tdd.toml`), never
  `uv run tdd`. It is 0.17.0 and has none of this plan's behaviour. This run's own ledger
  records no `green_without_implementation` or `reference_path_touched`, and the friction log
  will not show them.
- Every stub and GREEN must pass `uv run ruff check` and `uv run mypy` (the close sweep's gates).
- Verbs this plan will hit:
  - `write_test`, `create_stub` (cycles 4 and 5: write exactly the stub the cycle names),
    `write_implementation`, `refactor_or_advance`.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`. This is cycle 3, the pin
    (mutate the event loop in `render.friction_log`), or any standard RED that pre-passes
    (mutate the increment that cycle added).
  - `annotate_cycle` → `tdd annotate --key --value`. This plan declares no keys of its own;
    `plan_defect` and `friction_note` are reserved.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|tooling> --detail '...'`. A pin that
    fails on arrival (cycle 3) is `plan_defect`.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- **Cycle 1:**
  - the event in `_handle_impl`, under decision 1's condition;
  - PRD R9.14b and the IntegrityEvent entry.

  Not `NUDGE_KINDS`.
- **Cycle 2:** `NUDGE_KINDS`, plus the README sentence and the first CHANGELOG entry.
- **Cycle 3:** a pin. Only its test.
- **Cycle 4:**
  - the parse and validation of `reference_paths` in `contract.parse`;
  - PRD R7.11a and the README key paragraph.

  Nothing in `ledger.py` or `cli.py`.
- **Cycle 5:** the table, both `Ledger` methods with their classification, and the
  `cmd_plan_register` call. Nothing in `machine.py` or `advance.py`.
- **Cycle 6:**
  - `Engine.touched_reference_paths` on **`authored_changes` only**;
  - the top-of-`advance` check;
  - `_reference_paths_blocked`, writing the blocker, the run end and the envelope only, with
    **no integrity event**;
  - the PRD Blocker entry and §12 bullet, the README subsection and hard-gate clause, and the
    second CHANGELOG entry.

  No `gitutil` change.
- **Cycle 7:** `gitutil.committed_since` and its union in `touched_reference_paths`. Nothing in
  `_handle_refactor`.
- **Cycle 8:** the second check in `_handle_refactor`.
- **Cycle 9:** the `reference_path_touched` event in `_reference_paths_blocked`, plus the PRD
  IntegrityEvent entry.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-235-test-only-green-and-reference-paths-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-235-test-only-green-and-reference-paths-friction.md
    git commit -m "docs: friction log for issue-235-test-only-green-and-reference-paths"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #235`. Cycles 1, 2, 4, 6 and 9 own the docs:

- `git diff --stat origin/main -- docs/PRD.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- README.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.
- `git diff origin/main -- src/tddcli/ledger.py | grep -c SCHEMA_VERSION` must print `0`. This
  plan adds a table and does not bump the schema (decision 6).

The visible change is ledger and friction-log content, so no demo recording is required. In the
PR body:

- quote the `- **Event — green_without_implementation:** …` line from cycle 3's render and the
  `- **Event — reference_path_touched:** …` line from cycle 9's;
- say that the trigger is "every staged path is a test", not the issue's literal "no
  implementation", and why (decision 1);
- repeat the ledger-service upgrade note from the CHANGELOG.
