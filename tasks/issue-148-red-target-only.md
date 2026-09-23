---
closes: 148
cycles:
  - n: 1
    project: tddcli
    refactor_cycle: true
    title: "Adapter.run and Engine.run_projects accept an unused target_only keyword"
    files:
      - "src/tddcli/adapters/base.py"
      - "src/tddcli/adapters/pytest_adapter.py"
      - "src/tddcli/adapters/vitest_adapter.py"
      - "src/tddcli/adapters/cargo_adapter.py"
      - "src/tddcli/adapters/gradle_adapter.py"
      - "src/tddcli/adapters/xctest_adapter.py"
      - "src/tddcli/adapters/exec_adapter.py"
      - "src/tddcli/machine.py"
    commit_refactor: "refactor: Adapter.run and run_projects take a target_only keyword"
  - n: 2
    project: tddcli
    title: "the invocation table gains others_observed, fresh and migrated"
    test: "tests/test_release_surface.py::test_invocation_gains_others_observed_column"
    files: ["src/tddcli/ledger.py"]
    commit_red: "test: invocation rows carry others_observed"
    commit_green: "feat: schema 12 adds invocation.others_observed"
    commit_refactor: "refactor: tidy the v11 migration"
  - n: 3
    project: tddcli
    title: "an adopted target is evaluated in the same advance when the run only ran the declared target"
    test: "tests/test_suite_scope.py::test_an_adopted_target_is_evaluated_in_the_same_advance"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: adoption on a target-only run is judged in one advance"
    commit_green: "fix: re-run an adopted target the run did not execute"
    commit_refactor: "refactor: one helper evaluates an adopted target"
  - n: 4
    project: tddcli
    title: "a target-only pytest run executes only the target, even with a path-scoped test_command"
    test: "tests/test_target_only_runs.py::test_a_target_only_pytest_run_executes_only_the_target"
    files: ["src/tddcli/adapters/pytest_adapter.py"]
    commit_red: "test: a target-only pytest run executes one node id"
    commit_green: "feat: pytest runs only the target when asked"
    commit_refactor: "refactor: tidy the pytest target-only invocation"
  - n: 5
    project: tddcli
    pin_cycle: true
    title: "a target-only pytest run uses the owning override's command and env"
    test: "tests/test_target_only_runs.py::test_a_target_only_pytest_run_uses_the_owning_override"
    files: []
    commit_pin: "test: pin that a target-only pytest run keeps the override's env"
  - n: 6
    project: tddcli
    pin_cycle: true
    title: "a target-only pytest run reports an uncollectable target file as not_collected"
    test: "tests/test_target_only_runs.py::test_a_target_only_pytest_run_reports_an_uncollectable_file_as_not_collected"
    files: []
    commit_pin: "test: pin that a collection error in the target's file is still not_collected"
  - n: 7
    project: tddcli
    pin_cycle: true
    title: "a target-only pytest run of a missing file is not_found, not a tooling error"
    test: "tests/test_target_only_runs.py::test_a_target_only_pytest_run_of_a_missing_file_is_not_found"
    files: []
    commit_pin: "test: pin that a missing target file is not_found on a target-only run"
  - n: 8
    project: tddcli
    title: "a target-only vitest run selects the file and an anchored, escaped full name"
    test: "tests/test_target_only_runs.py::test_a_target_only_vitest_run_selects_the_file_and_an_anchored_name"
    files: ["src/tddcli/adapters/vitest_adapter.py"]
    commit_red: "test: a target-only vitest run filters to one test"
    commit_green: "feat: vitest runs only the target when asked"
    commit_refactor: "refactor: tidy the vitest name pattern"
  - n: 9
    project: tddcli
    pin_cycle: true
    title: "a target-only vitest run uses the owning override's command and env, once"
    test: "tests/test_target_only_runs.py::test_a_target_only_vitest_run_uses_the_owning_override"
    files: []
    commit_pin: "test: pin that a target-only vitest run uses only the owning suite"
  - n: 10
    project: tddcli
    title: "RED is not blocked by a failing test outside the cycle"
    test: "tests/test_suite_scope.py::test_red_is_not_blocked_by_a_failing_test_elsewhere"
    files: ["src/tddcli/advance.py", "src/tddcli/machine.py"]
    commit_red: "test: RED ignores failures it did not observe"
    commit_green: "feat: RED runs only the target"
    commit_refactor: "refactor: tidy the target-only plumbing"
  - n: 11
    project: tddcli
    title: "a RED invocation records others_observed = 0 and a GREEN one records 1"
    test: "tests/test_suite_scope.py::test_red_records_others_unobserved_and_green_records_them_observed"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: invocations record whether they observed other failures"
    commit_green: "feat: record others_observed on every invocation"
    commit_refactor: "refactor: tidy the invocation row"
  - n: 12
    project: tddcli
    pin_cycle: true
    title: "a pin is not blocked by a failing test outside the cycle"
    test: "tests/test_suite_scope.py::test_a_pin_is_not_blocked_by_a_failing_test_elsewhere"
    files: []
    commit_pin: "test: pin that AWAITING_PIN runs only the target"
  - n: 13
    project: tddcli
    title: "a sensitivity check runs only the target"
    test: "tests/test_suite_scope.py::test_a_sensitivity_check_runs_only_the_target"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: the sensitivity check does not observe other failures"
    commit_green: "feat: the sensitivity check runs only the target"
    commit_refactor: "refactor: tidy the sensitivity run"
  - n: 14
    project: tddcli
    title: "GREEN on an exec project runs every script and is blocked by one failing elsewhere"
    test: "tests/test_suite_scope.py::test_green_on_an_exec_project_is_blocked_by_a_failing_script_elsewhere"
    files: ["src/tddcli/adapters/exec_adapter.py"]
    modifies_tests:
      - "tests/test_exec_adapter.py::test_targeting_runs_only_that_script"
    commit_red: "test: exec GREEN sees a regression in another script"
    commit_green: "fix: exec narrows to the target only when asked"
    commit_refactor: "refactor: tidy the exec run loop"
  - n: 15
    project: tddcli
    title: "a cargo run with a target, not target-only, runs the whole suite"
    test: "tests/test_cargo_adapter.py::test_a_run_with_a_target_but_not_target_only_runs_the_whole_suite"
    files: ["src/tddcli/adapters/cargo_adapter.py"]
    commit_red: "test: cargo GREEN runs the whole suite"
    commit_green: "fix: cargo narrows to the target only when asked"
    commit_refactor: "refactor: tidy the cargo run"
  - n: 16
    project: tddcli
    title: "a gradle run with a target, not target-only, has no --tests filter"
    test: "tests/test_gradle_adapter.py::test_a_run_with_a_target_but_not_target_only_has_no_tests_filter"
    files: ["src/tddcli/adapters/gradle_adapter.py"]
    modifies_tests:
      - "tests/test_gradle_adapter.py::test_targeted_run_appends_tests_filter"
    commit_red: "test: gradle GREEN runs the whole suite"
    commit_green: "fix: gradle narrows to the target only when asked"
    commit_refactor: "refactor: tidy the gradle run"
  - n: 17
    project: tddcli
    title: "an xctest run with a target, not target-only, has no -only-testing flag"
    test: "tests/test_xctest_adapter.py::test_a_run_with_a_target_but_not_target_only_has_no_only_testing"
    files:
      - "src/tddcli/adapters/xctest_adapter.py"
      - "docs/PRD.md"
      - "docs/harness-integration.md"
      - "CHANGELOG.md"
    modifies_tests:
      - "tests/test_xctest_adapter.py::test_targeted_run_appends_only_testing_flag"
    commit_red: "test: xctest GREEN runs the whole suite"
    commit_green: "fix: xctest narrows to the target only when asked"
    commit_refactor: "docs: PRD R9.1a-d, harness table and changelog for target-only RED"
---

# Issue 148 — confirm RED by running only the target test

## Context

Issue #148 (part of #145). Every RED confirmation runs the whole suite to learn one test's
outcome. In #145's run that was 29 runs of about 33 s, or 16 minutes. The decision was settled
on the issue on 2026-09-23. RED runs only the target. GREEN runs the whole suite for **every**
adapter, and that is the condition that makes a target-only RED safe.

What the code does today:

- **pytest and vitest** ignore the target. They run every suite and look the target up in the
  report (`PytestAdapter.run`, `VitestAdapter.run`).
- **cargo, gradle, xctest and exec** narrow `run(target)` to the target whenever they are given
  one, at RED **and at GREEN**. So their GREEN never sees a regression elsewhere. The close
  sweep can then skip the cycle's own project (the §6.1 `skip_own` in `advance.py`'s
  AWAITING_REFACTOR handler), so a cycle can close without the whole suite ever running. That is
  #153, and this plan fixes it (cycle 14 and cycles 15–17).
- `Engine.run_projects` is the single path for AWAITING_TEST and AWAITING_PIN
  (`_handle_test_phase`), AWAITING_IMPL (`_handle_impl`) and `tdd sensitivity check`
  (`cli.py`, the `args.step == "check"` branch).

**Done when** (from the issue):
- `docs/PRD.md` carries the amendment below, in the same PR.
- The ledger migration adds `invocation.others_observed`.
- RED runs only the target for pytest and vitest, is not blocked by failures elsewhere, and
  records `others_observed = 0`.
- A collection error in the target's own file is still `not_collected`.
- GREEN runs the whole suite for cargo, gradle, xctest and exec, and a failure elsewhere
  blocks it.
- The sensitivity check runs only the target.
- #153 is closed.

## Design decisions (locked)

1. **One keyword, default whole suite.** `Adapter.run(target=None, *, target_only=False)`.
   `target_only=True` with a target runs as little as the adapter can while still observing the
   target. `False` runs the whole suite and reads the target's outcome from it. The default is
   the safe one: a caller that forgets the flag gets a correct, slower run.
   `Engine.run_projects(..., retried=False, target_only=False)` forwards it. Decided by the #148
   decision (R9.1a, R9.1b).

2. **Who passes `target_only=True`:** AWAITING_TEST and AWAITING_PIN (both through
   `_handle_test_phase`), the adoption re-run (decision 5), and `tdd sensitivity check`.
   AWAITING_IMPL and the close sweep never do. Pin cycles were decided by the user on
   2026-09-23: a pin only checks that the target passes, and the close sweep still runs the
   project in full afterwards.

3. **"Not observed" is a column, not NULL.** `invocation.others_observed INTEGER NOT NULL
   DEFAULT 1`, `SCHEMA_VERSION` 11 → 12, and `MIGRATIONS[11] = "ALTER TABLE invocation ADD
   COLUMN others_observed INTEGER NOT NULL DEFAULT 1;"`.
   - `other_failures` is `TEXT NOT NULL`, and SQLite cannot relax that without rebuilding the
     table.
   - Old rows default to 1, which is correct: they observed the whole suite.
   - In `run_projects`: `observed = not (target_only and target is not None)`. When it is
     false, `other = []` and the row gets `others_observed = 0`.
   - The close sweep's own insert in `Engine.sweep` is untouched. It takes the default 1.
   - The only code that reads `other_failures` is `--accept-failures` (`cli.py`,
     `_accept_failures_into_baseline`). It reads CLOSE_SWEEP rows only, so it is unaffected.

   Decided by: #148 and the ledger's migration convention.

4. **pytest target-only command: the owning suite's collect command plus the node id.** Decided
   by the user on 2026-09-23. `base, env = self._collect_cmd_for(<file part of the id>)`.
   - That gives the owning override's `collect_command or test_command` and its env, else the
     project's `collect_command or` the plain runner command with the project env.
   - Run exactly one invocation, `f"{base} {shlex.quote(native)}"`, through `_suite_report`. No
     union across suites and no overlap check.
   - **Footgun, named:** appending the node id to `test_command` does not narrow when
     `test_command` is scoped to a path. Probed: `pytest tests/ tests/test_ok.py::test_a` ran
     both tests in the file. The collect command is the one the registry already uses with a
     path (per-file collection, R10.3).
   - Probed with pytest-json-report:
     - A lone node id in a file that fails to import: exit 4, a report is written, `tests`
       is empty, and `collectors` holds the failing file. The existing lookup gives
       `not_collected`.
     - A missing test in an existing file: exit 4, a report is written, and both lists are
       empty, so `not_found`.
     - A missing file: the same, so `not_found`.

5. **An adopted target the run did not execute is run in the same advance** (cycle 3). When
   `_outcome_from_verdicts` returns None, call `engine.run_projects(projects, kept + [adopted],
   cycle, phase, retried, target_only=True)` and take the adopted target's outcome and failure
   from it. Do not reply "Run `tdd advance` again".
   - Evidence: `tasks/issue-72-adopt-on-first-run.md` found that the "advance again" reply
     runs straight into `no_change_since_last_run`.
   - A target-only RED makes that path the normal one for pytest. In the simulation,
     `test_single_new_test_is_adopted_and_evaluated_in_one_advance`,
     `test_unique_same_file_candidate_is_adopted_and_evaluated` and
     `test_adopted_passing_test_demands_sensitivity_in_one_advance` in
     `tests/test_advance_adoption.py` all failed without this and passed with it.
   - Route **both** adoption branches (the single candidate and the `_disambiguate`-resolved
     one) through one helper. The resolved branch cannot be reached with exec ids, so its
     guard is the existing `test_unique_same_file_candidate_is_adopted_and_evaluated`, which
     starts exercising this path at cycle 10.

6. **vitest target-only command.**
   - `file, _, _ = native.partition(" > ")`.
   - `name` is the part after `file + " > "` in `self.strip(self.normalise_id(target))`. That
     is vitest's `fullName`: describe titles and the test title joined by a space.
   - Owning suite: `ov = self.project.override_for(file)`. Use `ov.test_command` with
     `self._suite_env(ov)` when there is one, else `self._test_cmd()` with
     `self._suite_env(None)`.
   - One invocation: `f"{base} --reporter=json {shlex.quote(file)} -t {shlex.quote(pattern)}"`,
     where `pattern = "^" + js_escape(name) + "$"`.
   - **Footguns, named:**
     - `-t` is an **unanchored regex**. Probed: without `^…$`, `outer adds (1+1)` also ran
       `outer adds (1+1) twice`.
     - Escape exactly the JavaScript metacharacters `\ ^ $ . * + ? ( ) [ ] { } |` with a
       backslash. **Do not use `re.escape`**: it also escapes spaces and other characters,
       which a JavaScript regex compiled with the `u` flag rejects.
     - The positional file argument is a substring filter. That is acceptable, because the
       anchored `-t` still selects one name.
   - Probed with vitest 4.1.11:
     - The anchored, escaped pattern ran only the target and marked its siblings `skipped`.
     - A target file that fails to import gives a suite with `status: failed`, a `message`,
       and no assertions. The existing lookup gives `not_collected`.
     - A missing file emits JSON with `testResults: []`, so `not_found`.

7. **cargo, gradle, xctest and exec narrow only when `target_only`.** The target's outcome is
   read from the whole run by the existing lookups:
   - cargo: header-attributed ids;
   - gradle: the JUnit XML;
   - xctest: case lines;
   - exec: every script runs.

   In the simulation, every existing test that reads a target from canned full output kept
   passing. A cargo full-run id comes from the artifact name, just as a collected id does, so
   declared ids still match.

8. **Test blast radius**, found by simulating decisions 1–7 in a scratch worktree (discarded).
   With the adoption re-run in place, only these three failed, and each is in the breaking
   cycle's `modifies_tests`. The **only** change allowed is adding `, target_only=True` to
   the `run(...)` call. No assertion changes.
   - `tests/test_exec_adapter.py::test_targeting_runs_only_that_script` (cycle 14)
   - `tests/test_gradle_adapter.py::test_targeted_run_appends_tests_filter` (cycle 16)
   - `tests/test_xctest_adapter.py::test_targeted_run_appends_only_testing_flag` (cycle 17)

   **Re-evaluation trigger:** if any other existing test fails at a GREEN in this plan, stop
   and raise `tdd blocker --kind plan_defect`. Do not edit it. The one exception is the
   adoption guard named in decision 5: if it fails at cycle 10, route the resolved branch
   through cycle 3's helper. That is a production change, and it is allowed in cycle 10's
   GREEN.

9. **Where the tests live.**
   - `tests/test_target_only_runs.py` is new, created by cycle 4. It holds adapter-level tests
     that run real pytest in `tmp_path`, and vitest tests with `_run_suite` patched.
   - `tests/test_suite_scope.py` is new, created by cycle 3. It holds end-to-end tests
     through `conftest.run_cli`.
   - The cargo, gradle and xctest cycles extend those adapters' existing test files, reusing
     `make_adapter` and the canned outputs there.

10. **PRD amendment** (cycle 17's refactor commit). This text is from #148, with two
    additions: pin cycles in R9.1a (decision 2), and R7.12's "only reporting flags", which a
    target-only run no longer satisfies.
    - **§5 Invocation table**, a row after `other_failures`:
      `| \`others_observed\` | \`1\` when the run could see failures outside the target;
      \`0\` for a target-only run (R9.1a), whose \`other_failures\` is \`[]\` because nothing
      else ran, not because nothing else failed |`
    - **§6.1 phase table:** the `AWAITING_TEST` row's pass condition becomes "target
      **fails**; only the target runs (R9.1a)". The `AWAITING_IMPL` row's becomes "target
      **passes**, no new failures elsewhere; the whole suite runs (R9.1b)".
    - **§9.1:** replace R9.1 with the R9.1 and R9.1a–R9.1d text in #148's "PRD amendment"
      section. In R9.1a, write "`AWAITING_TEST` and `AWAITING_PIN` run **only the target
      tests**".
    - **§9.2 R9.6:** append "A target-only invocation (R9.1a) has nothing to subtract from: it
      records `others_observed = 0`, and its empty `other_failures` must not be read as a clean
      run."
    - **R7.12:** after "Adapters append only reporting flags", add "— and, for a target-only
      run (R9.1a), the selector that picks the target".

    Also update the `fix_regression` row in `docs/harness-integration.md`'s verb table to
    "tests outside the cycle are failing at GREEN, or the close sweep / lint / typecheck gates
    failed". Add a `### Changed` entry to `CHANGELOG.md` under `## [Unreleased]`. It says RED
    and pin phases run only the target (#148), GREEN runs the whole suite for every adapter
    (fixes #153), and the ledger is schema 12.

## Deliberate scope cuts (do not build)

None. #149 (at GREEN, run the target first and stop if it fails) is a separate open issue that
builds on this one. It is not asked for here.

## Cycles

### Cycle 1 — refactor: the keyword exists and does nothing

`Adapter.run` in `base.py` and each of the six adapters gain `*, target_only: bool = False`.
`Engine.run_projects` gains `target_only: bool = False` after `retried`. Neither is read, and no
caller changes. The whole suite is the guard. Nothing else changes, and above all no narrowing
logic.

### Cycle 2 — the invocation table gains `others_observed`

- **Test** `tests/test_release_surface.py::test_invocation_gains_others_observed_column`
  (`tmp_path, ledger_home`). It follows `test_gate_result_gains_tree_hash_and_skipped_columns`:
  - `ledger = Ledger(tmp_path / "somerepo")`, then
    `fresh = {r[1] for r in ledger.db.execute("PRAGMA table_info(invocation)").fetchall()}`.
  - Set `schema_version` to `'11'` through `ledger._write`.
  - `if "others_observed" in fresh:` drop that column with `ALTER TABLE`. The guard keeps the
    RED an assertion rather than an `OperationalError`.
  - `ledger.db.close()`, reopen, and take `migrated` the same way.
  - Single assertion: `assert "others_observed" in fresh & migrated`.
- **Production target:** `src/tddcli/ledger.py`: `SCHEMA_VERSION`, the `invocation` DDL, and
  `MIGRATIONS[11]` (decision 3), with a comment line in the existing style.
- **EXPECTED FAILURE:** `AssertionError: assert 'others_observed' in {…}`. The set is the
  current column names.

### Cycle 3 — an adopted target is judged in the same advance

The shared fixture for `tests/test_suite_scope.py`. Cycle 3 writes it:

```python
import stat

from conftest import git, run_cli, write_plan

PLAN = """---
cycles:
  - n: 1
    project: {project}
    {kind}title: "t"
    test: "{test}"
    commit_red: "test: t"
    commit_green: "feat: t"
    commit_pin: "test: pin"
---
"""


def _sh(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/bash\n" + body + "\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _exec_repo(repo):
    """`repo`, re-registered as one exec project `gates` whose committed
    check-mode.sh passes while lib/mode.txt says `old`."""
    (repo / "tdd.toml").write_text(
        '[project.gates]\nroot = "gates"\nadapter = "exec"\n'
        'test_paths = ["scripts/check-*.sh"]\nlint = []\ntypecheck = []\n'
    )
    (repo / "gates" / "lib").mkdir(parents=True)
    (repo / "gates" / "lib" / "mode.txt").write_text("old\n")
    _sh(repo / "gates" / "scripts" / "check-mode.sh", 'test "$(cat lib/mode.txt)" = old')
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "exec project")
    return repo
```

For a standard cycle, format `PLAN` with `kind=""`. For a pin, use
`kind="pin_cycle: true\n    "`. Both forms registered and started in the probes.

- **Test** `test_an_adopted_target_is_evaluated_in_the_same_advance(repo)`:
  - `_exec_repo(repo)`, and register and start
    `PLAN.format(project="gates", kind="", test="scripts/check-answer.sh")`.
  - Write `gates/scripts/check-reply.sh` with `_sh`, body
    `test "$(cat lib/answer.txt)" = 42`. It is a new script, and the declared one is never
    written.
  - `out = run_cli(repo, "advance")`.
  - Single assertion: `assert out["next_action"]["verb"] == "write_implementation"`.
- **Production target:** `src/tddcli/advance.py`, `_handle_test_phase`'s adoption branches
  (decision 5). Extract one helper, used by both branches, that returns the adopted target's
  outcome and failure text, re-running it with `target_only=True` when the verdicts in hand do
  not contain it.
- **EXPECTED FAILURE** (probed): `AssertionError: assert 'refactor_or_advance' ==
  'write_implementation'`. The reply today is "Adopted gates::scripts/check-reply.sh as the
  target (declared gates::scripts/check-answer.sh was not collected). Run `tdd advance` again
  to evaluate it." The after-state was simulated: the same advance answered
  `write_implementation`.

### Cycle 4 — pytest runs one node id

The shared fixture for `tests/test_target_only_runs.py`. Cycle 4 writes it:

```python
from unittest.mock import patch

from tddcli import config as config_mod
from tddcli.adapters.pytest_adapter import PytestAdapter
from tddcli.adapters.vitest_adapter import VitestAdapter

PY_TOML = """
[project.backend]
root         = "backend"
adapter      = "pytest"
test_paths   = ["tests/"]
test_command = "pytest tests/"
"""


def _pytest(tmp_path, extra=""):
    (tmp_path / "tdd.toml").write_text(PY_TOML + extra)
    tests = tmp_path / "backend" / "tests"
    tests.mkdir(parents=True)
    (tests / "test_two.py").write_text(
        "def test_a():\n    assert False\n\n\ndef test_b():\n    assert False\n"
    )
    return PytestAdapter(config_mod.load(tmp_path).project("backend"), tmp_path)
```

`tmp_path` has no `uv.lock`, so the command is bare `pytest`. Under `uv run pytest` that is
the project venv's, which has pytest-json-report. The `repo`-fixture tests already rely on
this.

- **Test** `test_a_target_only_pytest_run_executes_only_the_target(tmp_path)`:
  `a = _pytest(tmp_path)`, then `v = a.run("backend::tests/test_two.py::test_a",
  target_only=True)`. Single assertion: `assert sorted(v.passed + v.failed) ==
  ["backend::tests/test_two.py::test_a"]`.
- **Production target:** `src/tddcli/adapters/pytest_adapter.py`, `PytestAdapter.run`. When
  `target_only and target is not None`, run the single invocation from decision 4, using
  `_collect_cmd_for` so the owning override is used from the start (cycle 5 pins that).
  Everything after the report loop is unchanged.
- **EXPECTED FAILURE** (probed): `AssertionError: assert
  ['backend::tests/test_two.py::test_a', 'backend::tests/test_two.py::test_b'] ==
  ['backend::tests/test_two.py::test_a']`. The path-scoped `test_command` is deliberate: it
  pins decision 4's footgun.

### Cycles 5–7 — pins on the pytest target-only run

Each passes on arrival once cycle 4 is in place (cycles 5–7 also pass on today's whole-suite
path). If one fails on arrival, stop and raise `tdd blocker --kind plan_defect`. Each has one
assertion.

- **Cycle 5** `test_a_target_only_pytest_run_uses_the_owning_override(tmp_path)`:
  - `a = _pytest(tmp_path, extra='\n[[project.backend.override]]\npattern = "tests/special/"\ntest_command = "pytest tests/special/"\nenv = { FLAG = "on" }\n')`.
  - Write `backend/tests/special/test_flag.py`:
    `import os\n\n\ndef test_flag():\n    assert os.environ.get("FLAG") == "on"\n`.
  - Assert `a.run("backend::tests/special/test_flag.py::test_flag",
    target_only=True).target_outcome == "passed"`.
  - Sensitivity: drop `_suite_env`'s override from the target-only invocation, and it fails.
- **Cycle 6** `test_a_target_only_pytest_run_reports_an_uncollectable_file_as_not_collected`:
  - `a = _pytest(tmp_path)`, then write `backend/tests/test_broken.py` as
    `import nosuchmod\n\n\ndef test_c():\n    pass\n`.
  - Assert `a.run("backend::tests/test_broken.py::test_c", target_only=True).target_outcome ==
    "not_collected"`.
  - This is the issue's done-when test. End to end, the existing
    `tests/test_end_to_end.py::test_uncollectable_target_asks_for_a_stub_not_a_human` covers
    it too, and it runs target-only from cycle 10.
- **Cycle 7** `test_a_target_only_pytest_run_of_a_missing_file_is_not_found`:
  - `a = _pytest(tmp_path)`, then
    `v = a.run("backend::tests/test_nofile.py::test_x", target_only=True)`.
  - Assert `(v.target_outcome, v.error) == ("not_found", None)`.
  - This guards adoption: a wrong declared file must be `not_found`, never a
    `tooling_defect`.

### Cycle 8 — vitest filters to one test

Add to `tests/test_target_only_runs.py`:

```python
VT_TOML = """
[project.frontend]
root       = "frontend"
adapter    = "vitest"
test_paths = ["**/*.test.ts"]
"""


def _vitest(tmp_path, extra=""):
    (tmp_path / "tdd.toml").write_text(VT_TOML + extra)
    (tmp_path / "frontend").mkdir()
    return VitestAdapter(config_mod.load(tmp_path).project("frontend"), tmp_path)


def _captured_vitest_run(adapter, target):
    seen = []

    def capture(cmd, env=None, timeout=None):
        seen.append((cmd, env))
        return (0, '{"testResults": []}', "")

    with patch.object(VitestAdapter, "_run_suite", side_effect=capture):
        adapter.run(target, target_only=True)
    return seen
```

- **Test** `test_a_target_only_vitest_run_selects_the_file_and_an_anchored_name(tmp_path)`:
  - `seen = _captured_vitest_run(_vitest(tmp_path), "frontend::src/a.test.ts > outer > adds
    (1+1)")`. Nested `>` is deliberate: it pins that the name is normalised to vitest's
    space-joined `fullName`.
  - Single assertion: `assert [c for c, _ in seen] == ["npx vitest run --reporter=json
    src/a.test.ts -t '^outer adds \\(1\\+1\\)$'"]`. That is a Python string literal, so `\\(`
    is one backslash.
- **Production target:** `src/tddcli/adapters/vitest_adapter.py`, `VitestAdapter.run`
  (decision 6). Add a small module-level `_js_escape(name)`, and use the owning suite from the
  start (cycle 9 pins that).
- **EXPECTED FAILURE** (probed): `AssertionError: assert ['npx vitest run --reporter=json'] ==
  ["npx vitest run --reporter=json src/a.test.ts -t '^outer adds \\(1\\+1\\)$'"]`. The
  after-state was probed against real vitest 4.1.11: that exact pattern ran only
  `outer adds (1+1)`.

### Cycle 9 — pin: a vitest target in an override uses only that suite

- **Test** `test_a_target_only_vitest_run_uses_the_owning_override(tmp_path)`:
  - `extra` declares an override: `pattern = "src/__contract__/"`, `test_command = "npx vitest
    run --config c.ts"`, `collect_command = "npx vitest list --config c.ts"` and
    `env = { API_URL = "x" }`.
  - `seen = _captured_vitest_run(adapter, "frontend::src/__contract__/x.test.ts > works")`.
  - Single assertion: `assert seen == [("npx vitest run --config c.ts --reporter=json
    src/__contract__/x.test.ts -t '^works$'", {"API_URL": "x"})]`.
- **Kind: pin.** It passes once cycle 8 uses the owning suite. Before cycle 8 it fails: two
  invocations and no `-t`. If it fails on arrival, stop and raise `tdd blocker --kind
  plan_defect`.

### Cycle 10 — RED is not blocked by a failure elsewhere

- **Test** `tests/test_suite_scope.py::test_red_is_not_blocked_by_a_failing_test_elsewhere(repo)`:
  - Register and start `PLAN.format(project="backend", kind="",
    test="tests/test_add.py::test_adding")`.
  - Write `backend/tests/test_other.py` (`def test_other():\n    assert False\n`) and
    `backend/tests/test_add.py` (`def test_adding():\n    assert False\n`).
  - `out = run_cli(repo, "advance")`.
  - Single assertion: `assert out["next_action"]["verb"] == "write_implementation"`.
- **Production target:**
  - `src/tddcli/advance.py`, `_handle_test_phase`: pass `target_only=True` to
    `run_projects`. This covers AWAITING_TEST and AWAITING_PIN. Cycle 12 pins the latter.
  - `src/tddcli/machine.py`, `Engine.run_projects`: forward `target_only` to
    `adapter.run`, and set `other = []` when `target_only and target is not None`.
  - Decision 5's adoption guard applies here.
- **EXPECTED FAILURE** (probed): `AssertionError: assert 'fix_regression' ==
  'write_implementation'`. The reply today is "1 test(s) outside this cycle are failing". The
  after-state was simulated: `write_implementation`.

### Cycle 11 — invocations record what they observed

- **Test** `test_red_records_others_unobserved_and_green_records_them_observed(repo)`:
  - Before `write_plan`, write and commit `backend/app/calc.py`
    (`def add(a, b):\n    raise NotImplementedError\n`).
  - Register and start the plan for `tests/test_add.py::test_adding`.
  - Write the test (`from app.calc import add\n\n\ndef test_adding():\n    assert add(2, 3) ==
    5\n`) and advance.
  - Implement `add` and advance.
  - Query with `Ledger(gitutil.repo_identity(repo))`, as `tests/test_concurrent_advance.py`
    does: `SELECT phase_at, others_observed FROM invocation WHERE phase_at IN
    ('AWAITING_TEST', 'AWAITING_IMPL') ORDER BY id`.
  - Single assertion: `assert [tuple(r) for r in rows] == [("AWAITING_TEST", 0),
    ("AWAITING_IMPL", 1)]`. Pinning both rows stops a GREEN that writes 0 everywhere.
- **Production target:** `src/tddcli/machine.py`, `Engine.run_projects`: add
  `others_observed=int(observed)` to the insert (decision 3).
- **EXPECTED FAILURE:** `AssertionError: assert [('AWAITING_TEST', 1), ('AWAITING_IMPL', 1)] ==
  [('AWAITING_TEST', 0), ('AWAITING_IMPL', 1)]`. The column defaults to 1 from cycle 2.

### Cycle 12 — pin: AWAITING_PIN runs only the target

- **Test** `test_a_pin_is_not_blocked_by_a_failing_test_elsewhere(repo)`:
  - Register and start `PLAN.format(project="backend", kind="pin_cycle: true\n    ",
    test="tests/test_smoke.py::test_smoke")`.
  - Write the failing `backend/tests/test_other.py` and advance.
  - Single assertion: `assert out["next_action"]["verb"] == "run_sensitivity_check"`.
- **Kind: pin.** It passes on arrival because cycle 10 changed the shared handler. Probed
  before cycle 10: `fix_regression`. After, simulated: `run_sensitivity_check`. If it fails on
  arrival, stop and raise `tdd blocker --kind plan_defect`.

### Cycle 13 — the sensitivity check runs only the target

- **Test** `test_a_sensitivity_check_runs_only_the_target(repo)`:
  - Before `write_plan`, write and commit `backend/app/calc.py`
    (`def add(a, b):\n    return a + b\n`) and the passing
    `backend/tests/test_add.py::test_adding`.
  - Register and start a pin plan on it, then advance. The reply is `run_sensitivity_check`.
  - Run `run_cli(repo, "sensitivity", "begin")`, then rewrite `calc.py` to `return a - b`,
    then `run_cli(repo, "sensitivity", "check")`. This is the flow in
    `tests/test_pin_cycles.py`.
  - Query `SELECT others_observed FROM invocation WHERE phase_at = 'SENSITIVITY'`.
  - Single assertion: `assert [r[0] for r in rows] == [0]`.
- **Production target:** `src/tddcli/cli.py`, the `args.step == "check"` branch: pass
  `target_only=True` to `run_projects`.
- **EXPECTED FAILURE:** `AssertionError: assert [1] == [0]`.

### Cycle 14 — exec GREEN runs every script (#153)

- **Test**
  `test_green_on_an_exec_project_is_blocked_by_a_failing_script_elsewhere(repo)`:
  - `_exec_repo(repo)`, and register and start the plan for `scripts/check-answer.sh`.
  - Write `check-answer.sh` (`test "$(cat lib/answer.txt)" = 42`) and advance. The reply is
    `write_implementation`.
  - Write `gates/lib/answer.txt` = `42\n` **and** `gates/lib/mode.txt` = `new\n`, then advance.
    `mode.txt` breaks the committed `check-mode.sh`.
  - Single assertion: `assert out["next_action"]["verb"] == "fix_regression"`.
- **Production target:** `src/tddcli/adapters/exec_adapter.py`, `ExecAdapter.run`: skip the
  other scripts only when `target_only`.
- **Test modified:** `tests/test_exec_adapter.py::test_targeting_runs_only_that_script`. The
  only change is `adapter.run("gates::scripts/check-a.sh", target_only=True)`.
- **EXPECTED FAILURE** (probed): `AssertionError: assert 'refactor_or_advance' ==
  'fix_regression'`. The reply today is "GREEN confirmed". The after-state was simulated:
  `fix_regression` with "The implementation broke 1 test(s) elsewhere."

### Cycles 15–17 — cargo, gradle and xctest narrow only when asked

Each test captures the command through `_run_suite`, as the neighbouring tests in its file do,
and calls `run(<target>)` **without** `target_only`. Each has one assertion.

- **Cycle 15**
  `tests/test_cargo_adapter.py::test_a_run_with_a_target_but_not_target_only_runs_the_whole_suite`:
  - `a = make_adapter(tmp_path)`, then `with patch.object(CargoAdapter, "_run_suite",
    return_value=(101, FULL_RUN, "")) as rs: a.run(INT_PASS)`.
  - `assert "--exact" not in rs.call_args.args[0]`.
  - **Target:** `CargoAdapter.run`: use `_targeted_cmd` and `default=` only when
    `target_only`.
  - **EXPECTED FAILURE:** `AssertionError: assert '--exact' not in 'cargo test --test roundtrip
    -- --exact renders_cover_only 2>&1'`.
- **Cycle 16**
  `tests/test_gradle_adapter.py::test_a_run_with_a_target_but_not_target_only_has_no_tests_filter`:
  - Use the `capture` side effect from `test_targeted_run_appends_tests_filter` and call
    `adapter.run(PASS)`.
  - `assert "--tests" not in commands_run[0]`.
  - **Target:** `GradleAdapter.run`: append `--tests` only when `target_only`.
  - **Test modified:** `test_targeted_run_appends_tests_filter`, with `adapter.run(PASS,
    target_only=True)` only.
  - **EXPECTED FAILURE:** `AssertionError: assert '--tests' not in '… --tests
    com.example.PollCadenceTest.scalesOnlyUnderE2E'`.
- **Cycle 17**
  `tests/test_xctest_adapter.py::test_a_run_with_a_target_but_not_target_only_has_no_only_testing`:
  - Use the `capture_suite` side effect from `test_targeted_run_appends_only_testing_flag`,
    with target `"native-ios::AppTests/PollCadenceTests/testFoo"`.
  - `assert "-only-testing:" not in commands_run[0]`.
  - **Target:** `XCTestAdapter.run`: append `-only-testing:` only when `target_only`.
  - **Test modified:** `test_targeted_run_appends_only_testing_flag`, with
    `adapter.run(target, target_only=True)` only.
  - **EXPECTED FAILURE:** `AssertionError: assert '-only-testing:' not in '…
    -only-testing:AppTests/PollCadenceTests/testFoo'`.
  - **Refactor phase:** the docs from decision 10: `docs/PRD.md`,
    `docs/harness-integration.md` and `CHANGELOG.md`.

The existing tests in these three files that read a target from canned output kept passing in
the simulation with narrowing off. That is how decision 7's claim, that the target's outcome
is read from the whole run, is checked.

### Behaviour census

| Promise | Test |
|---|---|
| the keyword exists and changes nothing by default | cycle 1: the whole suite |
| `others_observed` column, fresh and migrated | cycle 2 |
| adopted target judged in one advance (single-candidate branch) | cycle 3 |
| adopted target judged in one advance (resolved branch) | existing `test_unique_same_file_candidate_is_adopted_and_evaluated`, exercising this path from cycle 10 |
| pytest target-only runs one node, even with a path-scoped `test_command` | cycle 4 |
| pytest target-only uses the owning override's command and env | cycle 5 |
| collection error in the target's file stays `not_collected` | cycle 6; end to end `test_uncollectable_target_asks_for_a_stub_not_a_human` |
| missing target file is `not_found`, not an error | cycle 7 |
| vitest target-only: file, anchored and escaped full name, nested ids normalised | cycle 8 |
| vitest target-only uses the owning override, once | cycle 9 |
| RED not blocked by failures elsewhere | cycle 10 |
| RED records 0, GREEN records 1 | cycle 11 |
| pin runs only the target | cycle 12 |
| sensitivity check runs only the target | cycle 13 |
| GREEN runs the whole suite on a narrowing adapter (#153) | cycle 14 (exec, end to end); cycles 15–17 (unit) |
| GREEN still blocked by failures elsewhere on pytest | existing `_handle_impl` tests (unchanged path) |
| `--accept-failures` unaffected | existing `tests/test_late_baseline.py` (reads CLOSE_SWEEP rows only) |

**Fakes:** `_run_suite` is patched for vitest, cargo, gradle and xctest.

| Method | Fake behaviour | Real behaviour | Left untested | Ruling |
|---|---|---|---|---|
| `VitestAdapter._run_suite` | records the command, returns empty JSON | runs vitest | that vitest's `-t` selects exactly one test | acceptable: probed against vitest 4.1.11 at planning time |
| `Cargo/Gradle/XCTestAdapter._run_suite` | canned output | runs the tool | real CLI flag semantics | acceptable: existing practice, and the change removes a flag rather than adding one |

pytest runs for real in cycles 4–7. There is no `docs/INVARIANTS.md`, no generated artifact,
no mirror (each adapter is its own implementation), and no numeric target.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-148-red-target-only        # first, before anything else
    tdd doctor                                       # must report healthy: true
    tdd run start --plan tasks/issue-148-red-target-only.md

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

**Referee.** Cycle 2 changes `src/tddcli/ledger.py`'s `SCHEMA_VERSION` to 12, and the released
0.12.2 understands up to 11. Build the frozen snapshot referee from the plan commit *before the
first cycle edit*, and never rebuild it mid-run:

    uv venv /tmp/tdd-referee-148
    uv pip install --python /tmp/tdd-referee-148/bin/python .
    /tmp/tdd-referee-148/bin/tdd doctor

Use that binary as `tdd` for every command in this plan, including the three above. The referee
predates this change, so it runs the whole suite at every RED of this run. Do not cite this
run's timings as evidence of the saving.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is
  green at the plan's base in a fresh worktree (613 passed, 2026-09-23); expect
  `baselines: {tddcli: 0}`.
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`;
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`. Cycles 5, 6, 7, 9 and 12 are
    pins and will ask for it.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|regression|bad_red|tooling|pre_existing_failure>
    --detail '...'`;
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.

  This plan declares no annotation keys beyond the reserved `plan_defect` and `friction_note`.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- cycle 1 adds the two keywords and reads neither.
- cycle 2 changes `SCHEMA_VERSION`, the `invocation` DDL and `MIGRATIONS[11]`. Nothing writes
  the column yet.
- cycle 3 adds the adoption re-run helper and routes both adoption branches through it. No
  caller passes `target_only` except the re-run.
- cycle 4 makes `PytestAdapter.run` honour `target_only` via `_collect_cmd_for`. No engine or
  handler change.
- cycles 5–7 are pins: write the test, and change no production code.
- cycle 8 makes `VitestAdapter.run` honour `target_only`, using the owning suite.
- cycle 9 is a pin.
- cycle 10 passes `target_only=True` from `_handle_test_phase` and makes `run_projects` forward
  it and empty `other`. It does not write `others_observed`.
- cycle 11 writes `others_observed` on the `run_projects` insert, and nothing else.
- cycle 12 is a pin.
- cycle 13 passes `target_only=True` from `tdd sensitivity check`, and nothing else.
- cycle 14 changes the exec adapter's skip condition, and nothing in the other adapters.
- cycles 15, 16 and 17 each change one adapter's narrowing condition. Cycle 17's refactor phase
  carries the docs.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-148-red-target-only-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-148-red-target-only-friction.md
    git commit -m "docs: friction log for issue-148-red-target-only"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #148` and `Closes #153`.

Docs are deliverables. Each of these must be non-empty (cycle 17), or the PR body says which
cycle dropped it and why:
- `git diff --stat origin/main -- docs/PRD.md`
- `git diff --stat origin/main -- docs/harness-integration.md`
- `git diff --stat origin/main -- CHANGELOG.md`

Nothing a user sees changes outside the JSON envelope, so no demo recording is required.
