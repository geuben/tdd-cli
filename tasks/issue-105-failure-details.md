---
closes: 105
cycles:
  - n: 1
    project: tddcli
    title: "an invocation keeps the failure details it was recorded with"
    test: "tests/test_failure_details.py::test_an_invocation_keeps_the_failure_details_it_was_recorded_with"
    stub_expected: ["src/tddcli/ledger.py"]
    files: ["src/tddcli/ledger.py", "docs/PRD.md"]
    commit_red: "test: an invocation keeps its failure details"
    commit_green: "feat: record failure details with each invocation"
    commit_refactor: "refactor: tidy the failure_detail table"
  - n: 2
    project: tddcli
    title: "a guest naming another source's invocation is refused"
    test: "tests/test_ledger_service.py::test_a_guest_naming_another_sources_invocation_is_refused"
    files: ["src/tddcli/ledger.py", "src/tddcli/service.py", "docs/split-runner.md"]
    modifies_tests: ["tests/test_ledger_surface.py::test_every_ledger_method_is_classified_and_scoped"]
    commit_red: "test: a guest cannot read another source's invocation"
    commit_green: "feat: the ledger service owns invocations by their run's source"
    commit_refactor: "refactor: tidy invocation ownership"
  - n: 3
    project: tddcli
    title: "pytest reports each failure with the phase that failed, its message and its longrepr"
    test: "tests/test_failure_details.py::test_pytest_reports_each_failure_with_the_phase_that_failed"
    stub_expected: ["src/tddcli/adapters/base.py"]
    files: ["src/tddcli/adapters/base.py", "src/tddcli/adapters/pytest_adapter.py"]
    commit_red: "test: pytest reports why each test failed"
    commit_green: "feat: pytest verdicts carry each failure's phase, message and longrepr"
    commit_refactor: "refactor: tidy pytest failure details"
  - n: 4
    project: tddcli
    title: "a GREEN run records why its other failures failed, and not its baseline's"
    test: "tests/test_failure_details.py::test_a_green_run_records_why_its_other_failures_failed"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: a GREEN run records its other failures' details"
    commit_green: "feat: phase runs persist the details of their other failures"
    commit_refactor: "refactor: tidy phase-run failure recording"
  - n: 5
    project: tddcli
    title: "a pytest failure detail is clipped and keeps the error at its tail"
    test: "tests/test_failure_clipping.py::test_pytest_failure_detail_keeps_the_error_at_the_tail"
    files: ["src/tddcli/adapters/pytest_adapter.py"]
    commit_red: "test: a pytest failure detail keeps its tail"
    commit_green: "feat: clip pytest failure details like target failures"
    commit_refactor: "refactor: tidy pytest failure clipping"
  - n: 6
    project: tddcli
    title: "a close sweep records why its failures failed"
    test: "tests/test_failure_details.py::test_a_close_sweep_records_why_its_failures_failed"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: a close sweep records its failures' details"
    commit_green: "feat: close sweeps persist the details of their failures"
    commit_refactor: "refactor: tidy close-sweep failure recording"
  - n: 7
    project: tddcli
    title: "vitest reports each failure with its first message line"
    test: "tests/test_failure_details.py::test_vitest_reports_each_failure_with_its_first_message_line"
    files: ["src/tddcli/adapters/vitest_adapter.py"]
    commit_red: "test: vitest reports why each test failed"
    commit_green: "feat: vitest verdicts carry each failure's details"
    commit_refactor: "refactor: tidy vitest failure details"
  - n: 8
    project: tddcli
    title: "cargo reports each failure with its panic line"
    test: "tests/test_failure_details.py::test_cargo_reports_each_failure_with_its_panic_line"
    files: ["src/tddcli/adapters/cargo_adapter.py"]
    commit_red: "test: cargo reports why each test failed"
    commit_green: "feat: cargo verdicts carry each failure's details"
    commit_refactor: "refactor: tidy cargo failure details"
  - n: 9
    project: tddcli
    title: "gradle reports each failure with its failure message"
    test: "tests/test_failure_details.py::test_gradle_reports_each_failure_with_its_failure_message"
    files: ["src/tddcli/adapters/gradle_adapter.py"]
    commit_red: "test: gradle reports why each test failed"
    commit_green: "feat: gradle verdicts carry each failure's details"
    commit_refactor: "refactor: tidy gradle failure details"
  - n: 10
    project: tddcli
    title: "xctest reports each failure with its error line"
    test: "tests/test_failure_details.py::test_xctest_reports_each_failure_with_its_error_line"
    files: ["src/tddcli/adapters/xctest_adapter.py"]
    commit_red: "test: xctest reports why each test failed"
    commit_green: "feat: xctest verdicts carry each failure's details"
    commit_refactor: "refactor: tidy xctest failure details"
  - n: 11
    project: tddcli
    title: "exec reports each failing script with its last output line"
    test: "tests/test_failure_details.py::test_exec_reports_each_failing_script_with_its_last_output_line"
    files: ["src/tddcli/adapters/exec_adapter.py"]
    commit_red: "test: exec reports why each script failed"
    commit_green: "feat: exec verdicts carry each failure's details"
    commit_refactor: "refactor: tidy exec failure details"
  - n: 12
    project: tddcli
    title: "the friction log lists each invocation's failures with phase and message"
    test: "tests/test_failure_details.py::test_the_friction_log_lists_each_invocations_failures"
    files: ["src/tddcli/render.py", "README.md"]
    commit_red: "test: the friction log says why each failure failed"
    commit_green: "feat: the friction log lists each invocation's failure details"
    commit_refactor: "refactor: tidy the friction log's failure block"
  - n: 13
    project: tddcli
    title: "tdd invocation show refuses an id the ledger does not hold"
    test: "tests/test_failure_details.py::test_showing_an_unknown_invocation_is_refused"
    stub_expected: ["src/tddcli/cli.py"]
    files: ["src/tddcli/cli.py"]
    commit_red: "test: tdd invocation show refuses an unknown id"
    commit_green: "feat: tdd invocation show refuses an unknown invocation"
    commit_refactor: "refactor: tidy the invocation verb"
  - n: 14
    project: tddcli
    title: "tdd invocation show prints an invocation's stored failure details"
    test: "tests/test_failure_details.py::test_invocation_show_prints_the_stored_failure_details"
    files: ["src/tddcli/cli.py", "README.md", "docs/PRD.md", "docs/split-runner.md", "CHANGELOG.md"]
    commit_red: "test: tdd invocation show prints the stored failure details"
    commit_green: "feat: tdd invocation show prints an invocation's failure details"
    commit_refactor: "docs: tdd invocation show and persisted failure details"
  - n: 15
    project: tddcli
    pin_cycle: true
    title: "a split-mode guest shows its own invocation's failures through the ledger service"
    test: "tests/test_ledger_service.py::test_a_guest_shows_its_own_invocations_failures"
    files: []
    commit_pin: "test: pin that a guest shows its invocation's failures over the socket"
---

# Issue 105: keep and show why suite failures failed

## Context

[#105](https://github.com/geuben/tdd-cli/issues/105). For a failing suite invocation the ledger
keeps the ids of the failing tests (`invocation.other_failures`) and drops the reason. The pytest
adapter reads `--json-report-file` from a temp directory and removes the directory once the report
is parsed. Of each failure, only the *target's* `longrepr` survives, in `invocation.target_failure`.
Every other failure's phase, crash message and `longrepr` is lost. The adapters for vitest, cargo,
gradle, xctest and exec do the same thing with their own runner output: they work out failure text
for every failing test and keep only the target's.

The motivating case in the issue: a close sweep under xdist reported five failures that passed
when re-run alone. One of them was a static AST guard with no fixtures. Planning probe (2026-10-29,
pytest-json-report on this repo's lockfile): a `session`-scoped fixture whose teardown raises is
reported as `outcome: "error"` on the **last test that ran**, with `setup` and `call` passed, and
`teardown.crash.message == "RuntimeError: session teardown boom"`. The phase and message are what
the issue asks for. With them, the guard's failure would have read as a teardown error.

The issue asks for three things:

1. persist failure details per invocation, keyed by `invocation.id`;
2. show them in `tdd log render`: the failing phase and the first line of the message for each
   failure;
3. print the stored `longrepr` on demand with a new verb.

## Design decisions (locked)

1. **Persist the non-passing subset, not the whole JSON report.** The issue offers both and names
   this as the minimum. A full report is about 10 MB for a 1600-test suite. The non-passing subset
   is a few KB, and every adapter can produce it, not only pytest. *Decided by: the issue's own
   size figures, and the cross-adapter evidence below.*

2. **A new table, `failure_detail`, with one row per id in the invocation's `other_failures`.**
   Columns: `id INTEGER PRIMARY KEY`,
   `invocation_id INTEGER NOT NULL REFERENCES invocation(id)`, `test_id TEXT NOT NULL`,
   `phase TEXT` (NULL when the runner reports no phases), `message TEXT NOT NULL`,
   `detail TEXT NOT NULL`. A phase run's `other_failures` is already baseline-subtracted and
   excludes the target, so a baseline failure is not re-recorded on every attempt. The target's
   text already lives in `target_failure`. A close sweep's row lists every failure
   (`other_failures=verdict.failed`, as it does today), so its details cover every failure too.
   **No `SCHEMA_VERSION` bump.** `SCHEMA` is `CREATE TABLE IF NOT EXISTS`, and an older tool never
   reads the table (repo note, #150). The referee therefore stays the released `tdd` on `PATH`.
   *Decided by: the code (`Engine.run_projects` and `Engine.sweep` in `machine.py`) and the repo
   note.*

3. **The shape adapters produce: `Verdict.failure_details: dict[str, FailureDetail]`.** It is
   keyed by the qualified test id, with one entry for every id in `verdict.failed`.
   `FailureDetail` is a dataclass in `src/tddcli/adapters/base.py`, next to `Verdict`, with fields
   in this order: `phase: str | None`, `message: str`, `detail: str`. The field defaults to an
   empty dict (`field(default_factory=dict)`), so every existing `Verdict(...)` call and fake
   adapter in `tests/` keeps working. The machine passes
   `{tid: dataclasses.asdict(d) for tid, d in verdict.failure_details.items() if tid in other}`
   to `record_invocation`. Plain dicts cross the ledger socket as JSON and dataclasses do not.
   *Decided by: `wire.py` serialises JSON values and `Row`s only.*

4. **What each adapter records.** The goal is the same answer for a failing non-target test as
   for a failing target.
   - **pytest.** `phase` is the first of `setup`, `call` and `teardown` that is present with an
     `outcome` other than `"passed"`. When `call` and `teardown` both fail, `call` is recorded,
     because it is the cause. `message` is the first line of that phase's `crash.message`. When
     there is no `crash`, which the probe found for `XPASS(strict)`, `message` is the **last**
     non-empty line of the phase's `longrepr`. Not the first: under xdist the first line is the
     `[gw0] linux -- Python …` header (probed). `detail` is
     `clip_failure(str(longrepr))`, the same clipping `target_failure` gets.
   - **vitest, cargo, gradle, xctest, exec.** `phase` is `None`. `message` is the line the
     adapter already reports as `target_evidence` for a failing target. `detail` is the text it
     already reports as `target_failure`. Both were probed against each adapter's existing
     fixtures (expected values are in the cycles).

   *Decided by: the probes.*

5. **Retention: keep every row and do not prune.** Size is bounded per row by clipping (1500
   characters, plus the clip marker) and per invocation by `other_failures`. The issue's own
   suggestion is "only invocations with failures", and that is what one-row-per-failure gives.
   *Decided by: the issue's retention note.*

6. **The command is `tdd invocation show <id>`, not `tdd status --failures`.** `status` reports
   the open cycle. Auditing happens after the run, often for a run that is long finished, and an
   invocation id is a stable handle that the friction log prints. The id is looked up across the
   repository's whole ledger, not only the worktree's latest run. `id` is parsed by argparse as
   `type=int`; a non-integer exits 2 the way every other int flag does.

   The envelope:
   - `result.invocation`: the id;
   - `result.phase`: the invocation's `phase_at`;
   - `result.project`;
   - `result.failures`: a list of `{"test", "phase", "message", "detail"}`, ordered by test id.

   `next_action` is always `REFACTOR_OR_ADVANCE` ("Read-only. Resume the phase in progress."). A
   read-only verb an executor may run mid-run must never reply `terminal: true`. An id the ledger
   does not hold is refused with `failure(..., reason="unknown_invocation")`, so `reason` sits
   under `result.reason`. *Decided by: the planner (unattended dispatch run). The issue offers
   both forms, and `tdd note`'s envelope is the precedent for a read/annotate verb that must not
   end the loop.*

7. **Split mode: `invocation_id` is a fourth ownership parameter.** Two new guest reads,
   `Ledger.invocation(invocation_id)` and `Ledger.failure_details(invocation_id)`, take only an
   invocation id. The service's `_Session._foreign` gains an owner,
   `("invocation_id", "invocation", self._invocation_source)`. `_invocation_source` resolves the
   invocation through `self.ledger.invocation(...)` and then `self.ledger.run_source(...)`. An
   invocation that does not exist is refused the same way, exactly as for the other owners, so
   ids cannot be probed. `OWNERSHIP` in `tests/test_ledger_surface.py` gains `"invocation_id"`,
   in the same cycle that makes the service enforce it (cycle 2). Until then `failure_details` is
   classified `HOST_ONLY`, so no guest can read it while the guard is missing. Writes need no new
   owner: `record_invocation` gets a keyword argument `failures: dict[str, dict] | None = None`
   and inserts the rows itself, so the existing `run_id` ownership covers them. *Decided by: the
   code (`_foreign`, `test_every_ledger_method_is_classified_and_scoped`).*

8. **Version skew in socket mode.** A guest on this version sends `record_invocation(...,
   failures=...)`, which a host service on 0.15.0 rejects. The service binds the call's signature,
   so the host must be upgraded together with its guests. This is the same constraint as every
   other ledger-surface change since #169. The CHANGELOG entry says so. *Decided by: the code
   (`inspect.signature(fn).bind` in `service.py`).*

9. **The friction-log block.** It goes inside each cycle's section, right after the
   `- **First run outcome:**` line, or after `- **Suite runs by phase:**` when there is no
   first-run line, and before the sensitivity line. There is one block per invocation that has
   details, in invocation order:

       - **Failures — invocation <id> (<phase_at>, <project>):**
         - `<test_id>` [<phase>]: <message>
         - `<test_id>`: <message>

   The second form is for rows whose `phase` is NULL. *Decided by: the planner. The issue asks
   for phase plus the first message line per `other_failures` entry, and the id is printed so
   that `tdd invocation show` has a handle.*

## Deliberate scope cuts (do not build)

- **The full JSON report on disk** (`<data dir>/<repo>/reports/<invocation id>.json`). Premise:
  **a named non-goal**. The issue offers it as an alternative to the minimum ("or at minimum …"),
  and decision 1 picks the minimum. Not a deferral.
- **`tdd status --failures`.** Premise: **a named non-goal**. The issue offers it as an
  alternative spelling of the on-demand view ("or"), and decision 6 picks `tdd invocation show`.
- **Baseline probes.** The probes at `run start`, the late probe and accept-failures re-runs are
  not invocation rows and have no invocation id. The issue asks for details keyed by
  `invocation.id`, so nothing is recorded for them. Premise: **outside the issue's definition**,
  not a deferral.

## Cycles

All new tests in `tests/test_failure_details.py` live at module scope (no classes), like every
other test file in this repo. The file's imports, which RED stages:

- `from conftest import git, run_cli, write_plan`
- `from test_baseline_integrity import PLAN, TEST_ADD, reach_refactor`
- `from test_evidence_extraction import _exec_adapter, _gradle_adapter, _gradle_write_results, _vitest_adapter, _write_script, _xctest_adapter`
- `from test_cargo_adapter import FULL_RUN, make_adapter`
- `from tddcli import adapters, gitutil, render`
- `from tddcli import config as config_mod`
- `from tddcli.adapters.base import FailureDetail`
- `from tddcli.adapters.cargo_adapter import CargoAdapter`
- `from tddcli.ledger import Ledger`

Add each import in the cycle that first needs it. Cross-test imports are already a convention
here (`tests/test_late_baseline.py` imports from `test_baseline_integrity`).

Ledger reads in the end-to-end tests:

    ledger = Ledger(gitutil.repo_identity(repo))
    run = ledger.latest_run(str(repo))

Then filter `ledger.invocations(cycle["id"], phase)` over `ledger.cycles(run["id"])`. All of it
was probed against this flow.

### Cycle 1: an invocation keeps the failure details it was recorded with

- **Behaviour:** `Ledger.record_invocation(..., failures={...})` stores one `failure_detail` row
  per entry. `Ledger.failure_details(invocation_id)` returns them ordered by `test_id`, with
  exactly the columns `test_id, phase, message, detail`.
- **Test** (`test_an_invocation_keeps_the_failure_details_it_was_recorded_with`):
  1. Build a fixture ledger the way `tests/test_time_report.py`'s `_ledger` does:
     `Ledger(tmp_path / "somerepo")` with the `ledger_home` fixture, then `ledger.insert` a
     `plan_contract` and a `run`.
  2. `inv = ledger.record_invocation(run_id, None, phase_at="CLOSE_SWEEP", project="p",
     adapter="pytest", target_test=None, target_outcome=None, target_failure="",
     total_passed=0, total_failed=2, other_failures=["p::b", "p::a"], duration_ms=1,
     tree_hash=None, failures={"p::b": {"phase": None, "message": "FAIL: b", "detail": "b out"},
     "p::a": {"phase": "teardown", "message": "RuntimeError: a", "detail": "a out"}})`.
  3. Single assertion: `[dict(r) for r in ledger.failure_details(inv)] == [{"test_id": "p::a",
     "phase": "teardown", "message": "RuntimeError: a", "detail": "a out"}, {"test_id": "p::b",
     "phase": None, "message": "FAIL: b", "detail": "b out"}]`.
- **Production:** `src/tddcli/ledger.py`. The `failure_detail` table goes in `SCHEMA` (decision
  2), plus the `record_invocation` keyword argument and `failure_details`.
- **Stub (RED):** add `failures: dict[str, dict] | None = None` to `record_invocation`'s
  keyword-only parameters, unused, and add `def failure_details(self, invocation_id: int) ->
  list: raise NotImplementedError`.
- **GREEN must also** classify `failure_details` as **`HOST_ONLY`** (decision 7). The whole-suite
  GREEN run fails `test_every_ledger_method_is_classified_and_scoped` on an unclassified method.
  `HOST_ONLY` needs no owner parameter. Do not touch `OWNERSHIP` or `service.py` here.
- **Refactor:** in `docs/PRD.md` §5, add a `### FailureDetail` entity after `### Invocation`,
  with the columns from decision 2 and the rule "one row per id in the invocation's
  `other_failures`, written with the invocation".
- **EXPECTED FAILURE:** `NotImplementedError`, raised by the `failure_details` stub.

### Cycle 2: a guest naming another source's invocation is refused

- **Behaviour:** the ledger service refuses `failure_details` with `foreign_run` when the
  invocation belongs to another source's run.
- **Test** (`test_a_guest_naming_another_sources_invocation_is_refused`, in
  `tests/test_ledger_service.py`, next to `test_a_guest_naming_another_sources_cycle_is_refused`):

      ledger_service.service.add_source("vm-2", ledger_service.dir / "vm-2.sock", executor=None)
      start_run(repo)
      run_cli(repo, "advance")
      host = ledger_mod.open_readonly(host_file(ledger_service, repo), source=None)
      cycle = host.open_cycle(host.active_runs()[0]["id"])
      invocation_id = host.invocations(cycle["id"])[0]["id"]
      assert refusal_of(ledger_service.dir / "vm-2.sock", str(gitutil.repo_identity(repo)),
                        "failure_details", invocation_id) == "foreign_run"

  Probed: the `advance` records invocation 1 (the plan's target passes, so the reply is
  `run_sensitivity_check`). `refusal_of` today returns `method_not_allowed`.
- **Production:**
  - `src/tddcli/ledger.py`: add `Ledger.invocation(invocation_id)`, the row or None. Move
    `failure_details` from `HOST_ONLY` to `GUEST_READS`, and add `invocation` to `GUEST_READS`.
    Update the guest-registry comment ("names that run by a parameter called exactly `run_id`,
    `cycle_id`, `contract_id` or `invocation_id`").
  - `src/tddcli/service.py`: `_Session._foreign` gains the owner from decision 7, plus
    `_invocation_source`.
- **modifies_tests:**
  `tests/test_ledger_surface.py::test_every_ledger_method_is_classified_and_scoped`. Its
  `OWNERSHIP` set gains `"invocation_id"`, and nothing else in that test changes. This is not a
  weakened guard: the service enforces the new owner in this same cycle, and this cycle's test
  is what proves it.
- **Refactor:** in `docs/split-runner.md`, where the service's `foreign_run` refusal is described,
  say that it covers invocations too.
- **EXPECTED FAILURE:** `AssertionError: assert 'method_not_allowed' == 'foreign_run'`.

### Cycle 3: pytest reports each failure with the phase that failed

- **Behaviour:** `PytestAdapter.run` fills `verdict.failure_details` for every non-passing test,
  following decision 4.
- **Test** (`test_pytest_reports_each_failure_with_the_phase_that_failed`): a real pytest run, no
  fake report.
  1. Write `tmp_path / "tdd.toml"`: `[project.backend]`, `root = "backend"`,
     `adapter = "pytest"`, `test_paths = ["tests/"]`.
  2. Write `backend/tests/test_phases.py`, holding:
     - a fixture `broken_setup` that raises `RuntimeError("setup boom")`;
     - a fixture `broken_teardown` that yields and then raises `RuntimeError("teardown boom")`;
     - `test_passes`, which passes;
     - `test_fails_in_call`: `assert 1 == 2, "values differ"`;
     - `test_fails_in_setup(broken_setup)`: `pass`;
     - `test_fails_in_teardown(broken_teardown)`: `pass`;
     - `test_fails_in_call_and_teardown(broken_teardown)`: `raise ValueError("call boom")`;
     - `@pytest.mark.xfail(strict=True) def test_passes_unexpectedly(): pass`.
  3. Run `adapters.build(config_mod.load(tmp_path).project("backend"), tmp_path).run(None)`.
  4. Single assertion:
     `{tid: (d.phase, d.message, d.message in d.detail) for tid, d in v.failure_details.items()}`
     equals this mapping (keys prefixed `backend::tests/test_phases.py::`):

     | test | expected value |
     |---|---|
     | `test_fails_in_call` | `("call", "AssertionError: values differ", True)` |
     | `test_fails_in_setup` | `("setup", "RuntimeError: setup boom", True)` |
     | `test_fails_in_teardown` | `("teardown", "RuntimeError: teardown boom", True)` |
     | `test_fails_in_call_and_teardown` | `("call", "ValueError: call boom", True)` |
     | `test_passes_unexpectedly` | `("call", "[XPASS(strict)]", True)` |

     `test_passes` must be absent.

  Every expected value was probed (2026-10-29) against the real report: the phases, the
  `crash.message` first lines, the missing `crash` on XPASS(strict) whose `longrepr` is
  `[XPASS(strict)]`, and each message appearing in its phase's `longrepr`.
- **Production:**
  - `src/tddcli/adapters/pytest_adapter.py`, in `PytestAdapter.run`: build the details in the
    loop over `tests`, **before** the `if target is None` early return.
  - `src/tddcli/adapters/base.py`: `FailureDetail`.
- **Stub (RED):** in `base.py`, add the `FailureDetail` dataclass (three fields, decision 3) and
  `failure_details: dict[str, FailureDetail] = field(default_factory=dict)` on `Verdict`. Fill
  nothing.
- **Mechanism footgun:** do not reuse `hit.get("call") or hit.get("setup")`, the target's
  current lookup. It never reads `teardown`, and a passed `call` is a truthy dict, so it returns
  the passed call with no `longrepr`.
- **EXPECTED FAILURE:** `AssertionError: assert {} == {'backend::tests/test_phases.py::test_fails_in_call': ...}`.

### Cycle 4: a GREEN run records why its other failures failed, and not its baseline's

- **Behaviour:** `Engine.run_projects` passes each verdict's details for the ids in that
  invocation's `other` list to `record_invocation(failures=...)`.
- **Test** (`test_a_green_run_records_why_its_other_failures_failed`):
  1. Write `backend/tests/test_flaky.py` with `def test_flaky():\n    assert False\n`, then
     `git add -A` and commit. This is the baseline failure.
  2. `write_plan(repo, PLAN)`, `plan register`, `run start`.
  3. Write `TEST_ADD`, and `app/calc.py` raising `NotImplementedError`. `advance`, which is RED.
  4. Write the real `add`, and overwrite `backend/tests/test_smoke.py` with
     `def test_smoke():\n    assert 1 == 2, "smoke broke"\n`. `advance`, which replies
     `fix_regression`.
  5. Find the `AWAITING_IMPL` invocation with `others_observed == 1`. Probed: invocation 3, with
     `other_failures == ["backend::tests/test_smoke.py::test_smoke"]` and `test_flaky` excluded.
  6. Single assertion: `[(r["test_id"], r["phase"], r["message"]) for r in
     ledger.failure_details(inv["id"])] == [("backend::tests/test_smoke.py::test_smoke", "call",
     "AssertionError: smoke broke")]`. The absent `test_flaky` row is what pins "not the
     baseline's".
- **Production:** `src/tddcli/machine.py`, `Engine.run_projects` only.
- **EXPECTED FAILURE:** `AssertionError: assert [] == [('backend::tests/test_smoke.py::test_smoke', 'call', 'AssertionError: smoke broke')]`.

### Cycle 5: a pytest failure detail is clipped and keeps the error at its tail

- **Behaviour:** pytest's `detail` is `clip_failure(longrepr)`.
- **Test** (`test_pytest_failure_detail_keeps_the_error_at_the_tail`, in
  `tests/test_failure_clipping.py`, next to `test_pytest_target_failure_keeps_the_error_at_the_tail`,
  reusing its `_pytest_adapter` and its `run_command` fake):
  - The fake report holds one test: `nodeid: "tests/test_db.py::test_connects"`,
    `outcome: "failed"`, `setup: {"outcome": "passed"}`, and `call: {"outcome": "failed",
    "crash": {"message": "ConnectionRefusedError: [Errno 61]"}, "longrepr": ("connector
    frame\n" * 300) + "ConnectionRefusedError: [Errno 61]"}`.
  - Run with `adapter.run(None)`, so there is no target.
  - Single assertion, with `d = verdict.failure_details["backend::tests/test_db.py::test_connects"]`:
    `(d.detail.endswith("ConnectionRefusedError: [Errno 61]"), len(d.detail) <= 1520) == (True, True)`.
- **Production:** `src/tddcli/adapters/pytest_adapter.py`.
- **EXPECTED FAILURE:** `AssertionError: assert (True, False) == (True, True)`. After cycle 3 the
  detail is the whole 5 KB `longrepr`.

### Cycle 6: a close sweep records why its failures failed

- **Behaviour:** `Engine.sweep` passes each verdict's details for its `other_failures`
  (`verdict.failed`) to `record_invocation(failures=...)`.
- **Test** (`test_a_close_sweep_records_why_its_failures_failed`):
  1. `reach_refactor(repo)`.
  2. Overwrite `test_smoke.py` with the cycle 4 body, then `advance`, which replies
     `fix_regression`.
  3. Take the `CLOSE_SWEEP` invocation. Probed: invocation 4,
     `other_failures == ["backend::tests/test_smoke.py::test_smoke"]`.
  4. Single assertion: the same tuple list as cycle 4, for that invocation.
- **Production:** `src/tddcli/machine.py`, `Engine.sweep` only.
- **EXPECTED FAILURE:** `AssertionError: assert [] == [('backend::tests/test_smoke.py::test_smoke', 'call', 'AssertionError: smoke broke')]`.

### Cycles 7–11: the other adapters

These cycles use the same pattern. Each runs the adapter with `run(None)` against canned output.
Its single assertion is `verdict.failure_details == {<id>: FailureDetail(phase=None,
message=<m>, detail=<d>)}`, and each fixture includes one passing test, which must be absent.
Every value below was probed (2026-10-29) as that adapter's `target_evidence` and
`target_failure` for the same fixture with the failing id as target. The test is
**independent**: it writes the strings literally and calls no production helper.

- **Cycle 7, vitest** (`test_vitest_reports_each_failure_with_its_first_message_line`).
  - Fixture: `_vitest_adapter(tmp_path)`, patched with
    `patch.object(type(adapter), "_run_suite", return_value=(1, json.dumps(report), ""))`. The
    report has one suite, `name = str(tmp_path / "frontend" / "calc.test.ts")`, with:
    - `calc add returns the sum`, failed, with the `failureMessages` list copied verbatim from
      `test_vitest_evidence_is_the_first_failure_message_line` in
      `tests/test_evidence_extraction.py` (one message, whose first line is the `m` below);
    - `calc add is pure`, passed, `failureMessages: []`.
  - Key: `"frontend::calc.test.ts > calc add returns the sum"`.
  - `m = "AssertionError: expected 2 to be 3 // Object.is equality"`.
  - `d` is that one message string, whole and unchanged (it is under vitest's 600-character
    clip).
  - Production: `VitestAdapter.run`, before its `if target is None` return.
- **Cycle 8, cargo** (`test_cargo_reports_each_failure_with_its_panic_line`).
  - Fixture: `make_adapter(tmp_path)`, patched with
    `patch.object(CargoAdapter, "_run_suite", return_value=(101, FULL_RUN, ""))`.
  - Key: `"kernel::lib::layout::tests::fails_on_purpose"`.
  - `m = "thread 'layout::tests::fails_on_purpose' (173172849) panicked at src/lib.rs:7:41:"`.
  - `d = "thread 'layout::tests::fails_on_purpose' (173172849) panicked at src/lib.rs:7:41:\nassertion `left == right` failed: expected width mismatch\n  left: 2\n right: 3\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace"`.
  - Production: `CargoAdapter.run`. `_parse_run`'s `failures` map is keyed by the native id
    (`lib::…`), so qualify it, before the `if target is None or native is None` return.
- **Cycle 9, gradle** (`test_gradle_reports_each_failure_with_its_failure_message`).
  - Fixture: `_gradle_adapter(tmp_path)`, with a `_run_suite` side effect that calls
    `_gradle_write_results(adapter, xml)` and returns `(1, "", "")`.
  - The XML is `test_gradle_evidence_is_the_first_failure_message_line`'s failing `add` case,
    plus `<testcase name="sub" classname="com.example.CalcTest" time="0.010"/>` before
    `</testsuite>`, with `tests="2"`.
  - Key: `"android-app::com.example.CalcTest/add"`.
  - `m = "expected:<1000> but was:<500>"`.
  - `d = "expected:<1000> but was:<500>\norg.opentest4j.AssertionFailedError: expected:<1000> but was:<500>\n\tat com.example.CalcTest.add(CalcTest.kt:10)"`.
  - Production: `GradleAdapter.run`. `_parse_results`'s `failures` is already keyed by the
    qualified id. Fill it before the `if target is None` return.
- **Cycle 10, xctest** (`test_xctest_reports_each_failure_with_its_error_line`).
  - Fixture: `_xctest_adapter(tmp_path)`, patched to return `(1, canned, "")`.
  - `canned` is `test_xctest_evidence_is_the_error_line_not_console_noise`'s text with two
    lines inserted before `Test Suite 'All tests' failed …`:
    - `Test Case '-[AppTests.RecTests testStarts]' started.`
    - `Test Case '-[AppTests.RecTests testStarts]' passed (0.001 seconds).`
  - Key: `"native-ios::AppTests/RecTests/testStopsRecording"`.
  - `m = '/Users/x/RecTests.swift:42: error: -[AppTests.RecTests testStopsRecording] : XCTAssertEqual failed: ("recording") is not equal to ("stopped")'`.
  - `d = '2026-08-27 10:00:00.001 AppTests[1234:5678] Socket SO_ERROR [61: Connection refused]\n' + m`.
  - Production: `XCTestAdapter.run`. Use `_failure_for(combined, <native id>)` and
    `_evidence_line` for every failed id, before the `if target is None` return.
- **Cycle 11, exec** (`test_exec_reports_each_failing_script_with_its_last_output_line`).
  - Fixture: `_exec_adapter(tmp_path)`, plus two scripts written with `_write_script`:
    - `gates/scripts/check-deploy.sh`: `'echo "INFO: starting deployment"\necho "FAIL: expected exit 0, got 1"; exit 1'`;
    - `gates/scripts/check-ok.sh`: `'exit 0'`.
  - Key: `"gates::scripts/check-deploy.sh"`.
  - `m = "FAIL: expected exit 0, got 1"`.
  - `d = "INFO: starting deployment\nFAIL: expected exit 0, got 1"`.
  - Production: `ExecAdapter.run`, in the `code != 0` branch, for every failing script.
- **EXPECTED FAILURE (each of the five):** `AssertionError: assert {} == {'<id>': FailureDetail(...)}`.

### Cycle 12: the friction log lists each invocation's failures

- **Behaviour:** `render.friction_log` prints decision 9's block.
- **Test** (`test_the_friction_log_lists_each_invocations_failures`):
  1. Build a fixture ledger shaped like `tests/test_time_report.py`'s `_ledger`: one
     `plan_contract`, one `run`, and one `cycle` (ordinal 1, `"CLOSED"`). Use fixed `_at(...)`
     timestamps.
  2. `ledger.record_invocation(run_id, cycle_id, phase_at="CLOSE_SWEEP", project="p",
     adapter="pytest", ..., other_failures=["p::tests/test_a.py::test_a",
     "p::tests/test_b.py::test_b"], failures={"p::tests/test_a.py::test_a": {"phase":
     "teardown", "message": "RuntimeError: session teardown boom", "detail": "x"},
     "p::tests/test_b.py::test_b": {"phase": None, "message": "FAIL: expected exit 0",
     "detail": "y"}})`. It is invocation 1 of a fresh ledger.
  3. Single assertion: `"\n".join(BLOCK) in render.friction_log(ledger, ledger.run(run_id))`,
     where `BLOCK` is:

         - **Failures — invocation 1 (CLOSE_SWEEP, p):**
           - `p::tests/test_a.py::test_a` [teardown]: RuntimeError: session teardown boom
           - `p::tests/test_b.py::test_b`: FAIL: expected exit 0

     Each line is a separate list item. Sub-items are indented two spaces, the way the
     sensitivity `observed:` sub-line is.
- **Production:** `src/tddcli/render.py`, `friction_log`. Read `ledger.failure_details(inv["id"])`
  for each invocation it already iterates. No SQL in `render.py`
  (`test_no_module_but_the_ledger_speaks_sql`).
- **Refactor:** in `README.md`'s "The friction log" paragraph, after "commits, and integrity
  events", add: "the failures each suite invocation saw, with the phase that failed and the
  first line of its message".
- **EXPECTED FAILURE:** `AssertionError: assert '- **Failures — invocation 1 (CLOSE_SWEEP, p):**\n…' in '# …'`.

### Cycle 13: `tdd invocation show` refuses an id the ledger does not hold

- **Behaviour:** `tdd invocation show 999` in a repo whose ledger has no invocation 999 fails
  with `reason: "unknown_invocation"`, under `result.reason`.
- **Test** (`test_showing_an_unknown_invocation_is_refused`): the `repo` fixture, with no run
  started. Single assertion: `run_cli(repo, "invocation", "show",
  "999")["result"].get("reason") == "unknown_invocation"`.
- **Production:** `src/tddcli/cli.py`:
  - `cmd_invocation_show`;
  - in `build_parser`, `inv = sub.add_parser("invocation", help="one suite invocation's
    recorded failures").add_subparsers(dest="invocation_command", required=True)`, then
    `s = inv.add_parser("show")`, `s.add_argument("id", type=int)`,
    `s.set_defaults(fn=cmd_invocation_show)`.

  The handler gets the ledger from `_context(require_run=False)` and refuses when
  `ledger.invocation(args.id) is None`.
- **Stub (RED):** the subparser as above. The handler returns
  `failure("tdd invocation show is not implemented", reason="not_implemented")`. Without the
  subparser, argparse exits 2 with empty stdout, and RED dies in `json.JSONDecodeError` instead
  of an assertion (repo note).
- **EXPECTED FAILURE:** `AssertionError: assert 'not_implemented' == 'unknown_invocation'`.

### Cycle 14: `tdd invocation show` prints an invocation's stored failure details

- **Behaviour:** for a known id, the envelope from decision 6.
- **Test** (`test_invocation_show_prints_the_stored_failure_details`):
  1. The same setup as cycle 6, then take the `CLOSE_SWEEP` invocation's id.
  2. `out = run_cli(repo, "invocation", "show", str(sweep_id))`.
  3. Single assertion:
     `(out["result"].get("invocation"), [(f["test"], f["phase"], f["message"], "smoke broke" in
     f["detail"]) for f in out["result"].get("failures", [])], (out["next_action"] or
     {}).get("terminal")) == (sweep_id, [("backend::tests/test_smoke.py::test_smoke", "call",
     "AssertionError: smoke broke", True)], False)`.

  Use `.get` and `or {}` deliberately. Until GREEN the reply is cycle 13's `not_implemented`
  failure, with no `invocation` key and `next_action: null`, and plain indexing would die in
  `KeyError` or `TypeError` instead of an assertion.
- **Production:** `src/tddcli/cli.py`, `cmd_invocation_show`. `result.phase` and
  `result.project` come from the invocation row, as decision 6 says.
- **Refactor (docs; the commit message is `docs:`):**
  - `README.md`: in the command table, add
    `| \`tdd invocation show <id>\` | an invocation's recorded failures: phase, message, detail |`
    after the `tdd log render` row.
  - `docs/PRD.md` §8.5: add the same row.
  - `docs/split-runner.md`: add `tdd invocation show` to the guest sentence "`tdd metrics`,
    `tdd fleet` and `tdd log render` still work, and see only that guest's source".
  - `CHANGELOG.md`: under `## [Unreleased]` → `### Added`, add an entry such as "**Suite failure
    details are kept** (#105). Every failing test an invocation records now keeps why it failed:
    the phase (pytest: setup, call or teardown), the first line of the message, and the clipped
    failure text, for every adapter. The friction log lists them per invocation, and
    `tdd invocation show <id>` prints them. A socket-mode host must run this version before its
    guests do."
- **EXPECTED FAILURE:** `AssertionError: assert (None, [], None) == (<id>, [('backend::tests/test_smoke.py::test_smoke', 'call', 'AssertionError: smoke broke', True)], False)`.

### Cycle 15 (pin): a split-mode guest shows its own invocation's failures

- **Behaviour (characterised):** the whole path crosses the socket. The guest sends
  `record_invocation(failures=...)` as JSON. The guest reads `invocation` and `failure_details`
  as `wire.Row`s, and the CLI builds the envelope from them.
- **Test** (`test_a_guest_shows_its_own_invocations_failures`, in `tests/test_ledger_service.py`,
  with fixtures `repo, split_guest, ledger_service`):
  1. Import `reach_refactor` from `test_baseline_integrity`.
  2. `reach_refactor(repo)`, overwrite `test_smoke.py` as in cycle 4, `run_cli(repo, "advance")`.
  3. Read the host: `host = ledger_mod.open_readonly(host_file(ledger_service, repo),
     source=None)`, `run = host.active_runs()[0]`, and take the last `CLOSE_SWEEP` invocation
     over `host.cycles(run["id"])`. Probed: invocation 4.
  4. Single assertion: `[(f["test"], f["phase"], f["message"]) for f in run_cli(repo,
     "invocation", "show", str(sweep_id))["result"]["failures"]] ==
     [("backend::tests/test_smoke.py::test_smoke", "call", "AssertionError: smoke broke")]`.
- **Why a pin:** cycles 1–14 build every piece, and `wire` already carries dicts, `None` and
  `Row`s, so this passes on arrival by design. If it **fails** on arrival, that is a defect in
  an earlier cycle, not new work. Run `tdd blocker --kind plan_defect --detail "<the
  failure>"`, and do not change production code inside the pin.
- **Sensitivity mutation:** take `failure_details` out of `GUEST_READS`, check, then restore.
- **EXPECTED (on arrival):** passes.

## Behaviour census

| Promise | Test |
|---|---|
| failure details are persisted per invocation, ordered, with exactly four columns | cycle 1 |
| no guest reads another source's invocation | cycle 2 |
| pytest: setup/call/teardown phase, first crash line, fallback to the last `longrepr` line, `longrepr` as detail | cycle 3 |
| phase runs record their other failures' details, and not the baseline's | cycle 4 |
| pytest detail is clipped, keeping the tail | cycle 5 |
| close sweeps record their failures' details | cycle 6 |
| vitest, cargo, gradle, xctest, exec: evidence line plus failure text per failing test | cycles 7–11 |
| the friction log shows phase and message per failure, both forms | cycle 12 |
| `tdd invocation show`: unknown id refused | cycle 13 |
| `tdd invocation show`: failures, the id, non-terminal `next_action` | cycle 14 |
| the same over the ledger socket | cycle 15 |

Cross-boundary checks:

- The adapters compute the details (cycles 3 and 7–11).
- The machine stores what they computed (cycles 4 and 6).
- Each stored value is read back where it is consumed: by the friction log (cycle 12), by the
  verb (cycle 14), and across the socket (cycle 15).
- `result.phase` and `result.project` (decision 6) are carried by cycle 14's handler from the
  row it already reads. They are not asserted. They are informational, and minimal GREEN may
  omit them; the census records that gap deliberately.

**Fakes vs real.**

| Seam | Fake | Real | Untested real path | Ruling |
|---|---|---|---|---|
| vitest/cargo/gradle/xctest `_run_suite` | canned output | real runner | runner output drift | acceptable: repo convention, canned from real runs |
| pytest | none (cycle 3 is a real `pytest --json-report` run) | — | — | — |
| ledger service | real `Service` on real sockets | — | — | — |

There are no mirrors, generated artifacts or invariant registry, and no perturb ledger.

**Test-side blast radius.** Only `test_every_ledger_method_is_classified_and_scoped`, which is
declared in cycle 2. The evidence:

- `grep -n "Verdict(" tests/*.py`: four constructions, all by keyword or by the first two
  positional fields. A defaulted field breaks none of them.
- `grep -n "def record_invocation" tests/`: no fake ledger.
- The only test calling `record_invocation` (`tests/test_ledger_sources.py`) does not pass the
  new optional keyword.
- No render test has an invocation with details, and the block appears only for those.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-105-failure-details          # first, before anything else
    tdd doctor                                         # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-105-failure-details.md   # captures baselines, opens cycle 1

`tdd doctor` checks every project; `tdd run start` probes only the ones the plan declares and
those downstream of them through an `[artifact]`. A failing check on a project outside that set
does not stop the run: note it and go on. Any other failing check stops it.

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

**Referee.** Use the released `tdd` on `PATH` (`tdd --version`), never an editable install of
this working tree. `SCHEMA_VERSION` does not change in this plan (decision 2).

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is green
  at the plan's base in a fresh worktree (722 passed, 2026-10-29); expect
  `baselines: {tddcli: 0}`.
- Verbs this plan will hit:
  - `create_stub`, `write_test`, `write_implementation`, `refactor_or_advance`;
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`. Cycle 15 is a pin and will ask
    for it.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|regression|bad_red|tooling|pre_existing_failure> --detail '...'`;
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.

  This plan declares no annotation keys beyond the reserved `plan_defect` and
  `friction_note`.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- cycle 1:
  - the `failure_detail` table;
  - the `failures` inserts in `record_invocation`;
  - `failure_details` (ordered by `test_id`, four columns), classified `HOST_ONLY`.

  No `Ledger.invocation`, no service change, no `OWNERSHIP` edit.
- cycle 2:
  - `Ledger.invocation`;
  - both methods in `GUEST_READS`;
  - the `_foreign` owner and `_invocation_source`;
  - `"invocation_id"` in `OWNERSHIP`.
- cycle 3:
  - in `pytest_adapter.py`, phase, message (crash first line, else last `longrepr` line) and
    **unclipped** `str(longrepr)`.

  No machine change and no clipping.
- cycle 4: `run_projects` passes `failures=` for `other`. **Do not touch `sweep`.**
- cycle 5: wrap pytest's detail in `clip_failure`. Nothing else.
- cycle 6: `sweep` passes `failures=`. Nothing else.
- cycles 7–11: the one adapter the cycle names. Nothing in any other adapter.
- cycle 12: the friction-log block. No CLI.
- cycle 13:
  - the `unknown_invocation` refusal only. A known id still returns the `not_implemented`
    failure.
- cycle 14: the success envelope for a known id.
- cycle 15: a pin. Write the test and change no production code.

Refactor phases may extract a per-adapter helper that both the target path and
`failure_details` call (the evidence line plus failure text). The suite is the guard, so keep
the behaviour identical.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-105-failure-details-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-105-failure-details-friction.md
    git commit -m "docs: friction log for issue-105-failure-details"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #105`.

Docs are deliverables. Each of these must be non-empty (cycles 1, 2, 12, 14), or the PR body says
which cycle dropped it and why:
- `git diff --stat origin/main -- README.md`
- `git diff --stat origin/main -- docs/PRD.md`
- `git diff --stat origin/main -- docs/split-runner.md`
- `git diff --stat origin/main -- CHANGELOG.md`

This is a new ledger table and a new CLI verb with a JSON envelope. Nothing visual changes, so no
demo recording is required.
