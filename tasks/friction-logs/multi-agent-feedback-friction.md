# Implementation Friction Log: multi-agent-feedback
Date: 2026-08-04
Executor: Claude Sonnet 5
Plan File: tasks/multi-agent-feedback.md

### Cycle 1: the existing already-active rejection carries machine-readable detail
- **Test:** `test_second_start_reports_the_active_run_id`
- **Stub needed?** No
- **RED as expected?** Yes —
  ```
  KeyError: 'reason'
  ```
  matches EXPECTED FAILURE exactly (current rejection's `result` is `{}`).
- **Files outside plan:** none
- **Tests deleted, skipped, or weakened?** none
- **Plan defect?** none
- **Friction note:** smooth. Had to avoid calling the `start()`-style helper twice
  (it re-commits `tasks/plan.md` via `write_plan`, and a second identical commit with
  no changes would fail `git commit`); split into a `register()` helper called once
  and two direct `run start` calls instead.

### Cycle 2: `run start` claims the worktree before probing and releases it on success
- **Test:** `test_successful_start_leaves_no_claim`
- **Stub needed?** Yes — `Ledger.claim`, `Ledger.release_claim`, `Ledger.active_claim`
  raising `NotImplementedError`, plus `baseline_claim` already in `SCHEMA` from
  preconditions.
- **RED as expected?** Yes — the plan's own EXPECTED FAILURE warns the naive
  "table exists" reading passes vacuously; the hardened test instead spies on
  `adapters.build` and reads `baseline_claim` directly via raw SQL (not through the
  stubbed `active_claim`, to avoid a spurious `NotImplementedError` crash inside the
  spy). Actual failure:
  ```
  AssertionError: claim was never taken
  assert False
   +  where False = any([False])
  ```
  Matches the plan's predicted `AssertionError: claim was never taken` exactly.
- **Files outside plan:** none
- **Tests deleted, skipped, or weakened?** none
- **Plan defect?** none
- **Friction note:** the exact scope of the `try/finally` ("around probe-and-insert")
  is ambiguous from prose alone. Implemented it to wrap the run/baseline insert and
  final envelope construction, but leave the R9.5a validation-refusal returns
  (before that block) unprotected — deliberately, since cycle 5 is explicitly
  written to close exactly that gap with its own RED/GREEN. Confirmed by reading
  cycle 5 closely before implementing cycle 2, to avoid accidentally pre-empting
  its RED.

### Cycle 3: a concurrent `run start` during baseline collection is rejected
- **Test:** `test_start_is_rejected_while_a_baseline_is_collecting`
- **Stub needed?** No
- **RED as expected?** Materially different from the plan's stated EXPECTED FAILURE
  — see Plan defect below. Actual failure:
  ```
  sqlite3.IntegrityError: UNIQUE constraint failed: baseline_claim.worktree_path
  ```
  raised uncaught from `Ledger.claim` inside `cmd_run_start`, not an
  `AssertionError` on `ok is False`.
- **Files outside plan:** none
- **Tests deleted, skipped, or weakened?** none
- **Plan defect?** Yes. The plan's EXPECTED FAILURE for this cycle ("the run starts
  normally and returns `ok: true`") assumes cycle 2 has not yet wired `claim()`
  unconditionally into `cmd_run_start`'s probe path. It has (cycle 2 calls
  `ledger.claim(...)` before the probe loop with no exception handling), so a second
  claim attempt now crashes with an uncaught `sqlite3.IntegrityError` instead of
  silently succeeding. Still a legitimate RED (the test fails, just via a different
  mechanism — an unhandled exception rather than a false `ok: true`), so proceeded
  without altering the test. Recorded here per the "material difference" protocol
  rather than silently adapting the test.
- **Friction note:** wrote the rejection prose for `baseline_in_progress` narrowly
  ("a baseline is already being collected in this worktree") and deliberately did
  *not* add the "tdd progress" / "do not re-run" guidance yet — that phrasing is
  cycle 19's RED target (`test_baseline_in_progress_tells_the_agent_to_poll`), and
  adding it now would make cycle 19 pass on arrival.

### Cycle 4: exactly one of two concurrent starts wins the claim
- **Test:** `test_only_one_of_two_concurrent_starts_wins`
- **Stub needed?** No
- **RED as expected?** No — materially different, twice over. See Plan defects below.
  First actual failure (using `run_cli` via `ThreadPoolExecutor` as literally
  specified):
  ```
  json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
  ```
  raised from `conftest.run_cli`'s `json.loads(...)` — one thread's captured stdout
  came back empty because `contextlib.redirect_stdout` is itself process-global and
  two threads entering/exiting it concurrently corrupt each other's capture, before
  either envelope is ever inspected. Rewrote the test to call `cmd_run_start`
  directly (bypassing `run_cli`'s stdout redirect entirely) with `os.chdir` done
  once outside the pool, since both attempts share one worktree. Second actual
  failure, after that rewrite:
  ```
  sqlite3.OperationalError: database is locked
  ```
  at `Ledger.release_claim`, reproducibly, taking ~65s per attempt before failing.
- **Files outside plan:** none (both fixes are inside cycle 4's own test and cycle 3's
  `Ledger`, both already plan-listed files)
- **Tests deleted, skipped, or weakened?** none
- **Plan defect?** Yes, two:
  1. P1's caveat ("no crash... printed output from a threaded test is unreliable")
     undersells the risk — in this environment the capture layer crashed outright
     (`JSONDecodeError`) rather than degrading gracefully. `run_cli`/`run_cli_text`
     are unsafe for concurrent use even when only the *returned* envelope is
     asserted on, because parsing happens before the assertion. Fixed by testing at
     the `cmd_run_start` layer, one `os.chdir` outside the pool.
  2. A previously-latent production bug, only surfaced by genuine concurrent load: a
     failed `Ledger.insert` (the `IntegrityError` cycle 3 relies on as the rejection
     signal) left its connection's implicit transaction open — Python's `sqlite3`
     module does not roll back automatically on a raised exception. The losing
     thread's connection therefore held SQLite's write lock until garbage collected,
     starving the winning thread's own writes (including its `release_claim`) well
     past the 30s busy timeout already added. Fixed with `try/except: self.db.
     rollback(); raise` around `Ledger.insert`, plus a `timeout=30.0` on
     `sqlite3.connect` (defends against ordinary contention now that the leak itself
     is fixed). This is exactly the "GREEN 4.3 ... fix it here" case the plan
     anticipated, just for a different underlying reason (transaction hygiene, not
     read-then-write drift).
- **Friction note:** the fix compounds with cycle 3 — `Ledger.insert`'s rollback-on-
  failure is now load-bearing for the whole claim mechanism, not just this test.

### Cycle 5: a refused baseline releases its claim
- **Test:** `test_a_refused_baseline_leaves_no_claim`
- **Stub needed?** No
- **RED as expected?** Yes —
  ```
  AssertionError: assert [<sqlite3.Row... 0x10aa77160>] == []
  Left contains one more item: <sqlite3.Row object at 0x10aa77160>
  ```
  matches the plan's predicted "AssertionError on the claim table being non-empty".
- **Files outside plan:** none
- **Tests deleted, skipped, or weakened?** none
- **Plan defect?** none
- **Friction note:** widened the existing `try/finally` (from cycle 2) to wrap the
  R9.5a probe-and-validate loop, not just the run/baseline-insert tail — exactly the
  gap the plan foretold when it deliberately scoped cycle 2 narrowly.

### Cycle 6: a claim whose owner is gone is reclaimed
- **Test:** `test_a_claim_from_a_dead_process_is_reclaimed`
- **Stub needed?** No
- **RED as expected?** Yes, after fixing a test-authoring bug (see friction note)
  ```
  AssertionError: {'ok': False, 'error': 'a baseline is already being collected in
  this worktree', 'run': None, 'result': {'reason': 'baseline_in_progress'}, ...}
  assert False is True
  ```
  matches the plan's predicted "after cycle 3, the start is refused" exactly.
- **Files outside plan:** none
- **Tests deleted, skipped, or weakened?** none
- **Plan defect?** none
- **Friction note:** first draft used `subprocess.run(["true"], check=True).pid`,
  which doesn't exist — `CompletedProcess` has no `pid` attribute. Fixed with
  `subprocess.Popen(["true"])` + `.wait()` before reading `.pid`. This was a test
  bug, not a plan or production defect, caught before ever reaching RED.

### Cycle 7: each completed project baseline emits a line to stderr
- **Test:** `test_baseline_captured_line_is_written_per_project`
- **Stub needed?** Yes — `heartbeat(**fields) -> None` in `envelope.py` raising
  `NotImplementedError`.
- **RED as expected?** Yes —
  ```
  AssertionError: no baseline_captured line in stderr
  assert []
  ```
  matches EXPECTED FAILURE exactly.
- **Files outside plan:** none
- **Tests deleted, skipped, or weakened?** none
- **Plan defect?** none
- **Friction note:** the full-suite run after GREEN hit one unrelated failure,
  `test_only_reporting_flags_are_appended` in `tests/test_project_commands.py`,
  asserting no CLI-flag substring (`-q`, `-p `, etc.) appears in the pytest command
  actually run. `tempfile.TemporaryDirectory`'s random suffix occasionally produces
  a directory name containing `-q` (e.g. `tdd-pytest-qychdp8z`), which the report
  path then carries — a pre-existing flake, unrelated to this change and not
  reproducible on immediate retry (passed standalone and on a second full-suite run,
  98 passed). Not touched; noted here per the friction-log protocol rather than
  fixed in passing (out of this plan's scope).

### Cycle 8: the heartbeat reports elapsed seconds per project
- **Test:** `test_baseline_heartbeat_reports_elapsed_seconds`
- **Stub needed?** No
- **RED as expected?** Yes — `KeyError: 'elapsed_s'`, matches EXPECTED FAILURE exactly.
- **Files outside plan:** none
- **Tests deleted, skipped, or weakened?** none
- **Plan defect?** none
- **Friction note:** smooth.

### Cycle 9: the claim records per-project progress as it goes
- **Test:** `test_claim_records_projects_done_as_each_completes` (fixture: `repo_multi`)
- **Stub needed?** Yes — `Ledger.update_claim` raising `NotImplementedError`.
- **RED as expected?** Yes —
  ```
  AssertionError: {'id': 1, ..., 'pid': 87654, ...}
  assert 0 == 1
  ```
  (`projects_done` still 0 on the second `adapters.build` call) with stderr showing
  both heartbeats fired in order `backend`, `frontend` — matches EXPECTED FAILURE
  `AssertionError: 0 != 1` and confirms the `tdd.toml`-order seam from P6.
- **Files outside plan:** none
- **Tests deleted, skipped, or weakened?** none
- **Plan defect?** none
- **Friction note:** off-by-one care needed — `projects_done` must reflect
  *completed* probes, so the counter passed to `update_claim` after finishing
  project *i* is `i` (1-based `enumerate(..., start=1)`), not the loop's 0-based
  index. Also extended the RED test to check `projects_total == 2` (present in the
  plan's own cycle 9 prose) in addition to `projects_done == 1`.
- **Refactor (9.5):** extracted `_probe_projects(cfg, worktree, ledger, on_progress)`
  from `cmd_run_start` as planned — it now owns timing, heartbeating, and the
  progress callback; `cmd_run_start` calls it with a `lambda` that updates the
  claim. Full suite re-run clean after the extraction (100 passed, no regression).

### Cycle 10: each project in a sweep emits a completion heartbeat
- **Test:** `test_sweep_emits_a_project_completed_line`
- **Stub needed?** No
- **RED as expected?** Yes — `AssertionError: no project_completed line in stderr`,
  matches EXPECTED FAILURE exactly.
- **Files outside plan:** none
- **Tests deleted, skipped, or weakened?** none
- **Plan defect?** Minor. GREEN 10.3's prose says "one insertion point covers every
  phase, close sweeps included," but `Engine.sweep` (the CLOSE_SWEEP phase, run on
  cycle close for downstream projects) is a separate method from `Engine.
  run_projects` with its own `adapter.run(None)` call — it does not route through
  `run_projects`, so it does not get this heartbeat. Cycle 10's own "Production
  target" line names only `Engine.run_projects`, so left `Engine.sweep` untouched
  per the stated scope; noting the "close sweeps included" claim does not hold
  literally, in case a later cycle assumes it does.
- **Friction note:** smooth otherwise.

### Cycle 11: the verb set gains `await_baseline`
- **Test:** `test_await_baseline_is_a_non_terminal_verb`
- **Stub needed?** No
- **RED as expected?** Yes — `AttributeError: type object 'Verb' has no attribute
  'AWAIT_BASELINE'`, matches EXPECTED FAILURE exactly.
- **Files outside plan:** none
- **Tests deleted, skipped, or weakened?** none
- **Plan defect?** none
- **Friction note:** smooth. Added the new verb to `docs/PRD.md` §8's verb table and
  a short note on `verb_set_version: 2`, per R8.3a's "adding a verb is a
  specification change."

### Cycle 12: `progress --json` reports collecting_baseline instead of "no runs recorded"
- **Test:** `test_progress_reports_collecting_baseline_when_a_claim_is_open`
- **Stub needed?** No
- **RED as expected?** Yes —
  ```
  AssertionError: {'ok': False, 'error': 'no runs recorded for this worktree',
  'run': None, 'result': {}, ...}
  assert False
  ```
  matches EXPECTED FAILURE exactly.
- **Files outside plan:** none
- **Tests deleted, skipped, or weakened?** none
- **Plan defect?** none
- **Friction note:** implemented `_claim_elapsed_s(claim)` inline now rather than
  waiting for cycle 14.5's formal `_collecting_envelope(claim)` extraction, since
  `elapsed_s` is needed by this cycle already; cycle 14.5 will still extract the
  full envelope-building branch shared across `cmd_progress` (JSON), `cmd_progress`
  (text, cycle 13) and `cmd_status` (cycle 14).

### Cycle 13: the bare `tdd progress` reports it too
- **Test:** `test_bare_progress_reports_collecting_baseline`
- **Stub needed?** No
- **RED as expected?** Materially different from the plan's stated EXPECTED FAILURE.
  Plan predicted "output is the JSON failure envelope, since the `no runs recorded`
  return precedes the `--json` branch." Actual:
  ```
  AssertionError: 'collecting baseline' in '{\n  "ok": true,\n  "run": null,\n
  "result": {\n    "status": "collecting_baseline", ...
  ```
  — cycle 12's implementation already returns the collecting-baseline branch
  unconditionally (before checking `args.json`), and `Envelope.emit()` always prints
  JSON unless `silent=True`. So the bare-text call still got JSON — the *success*
  envelope from cycle 12, not a *failure* envelope. Still a genuine RED (the
  assertion fails, `"collecting baseline"` is nowhere in JSON output), just via a
  different mechanism than predicted. Recorded per the "material difference"
  protocol; did not alter the test.
- **Files outside plan:** none
- **Tests deleted, skipped, or weakened?** none
- **Plan defect?** Yes — see above. The plan's authors evidently expected cycle 12's
  GREEN to leave the `no runs recorded` failure-return reachable for the bare-text
  path until cycle 13 fixed it; instead cycle 12's collecting-baseline branch
  covers both `--json` and bare calls with the same (JSON) response, once inserted
  ahead of the old failure return. Net behaviour cycle 13 needed to fix was the
  same (bare progress must render text, not JSON), just reached via a different
  starting point.
- **Friction note:** none beyond the above.

### Cycle 14: `tdd status` reports it as well
- **Test:** `test_status_reports_collecting_baseline`
- **Stub needed?** No
- **RED as expected?** Yes — `KeyError: 'status'`, matches EXPECTED FAILURE exactly.
- **Files outside plan:** none
- **Tests deleted, skipped, or weakened?** none
- **Plan defect?** none
- **Friction note:** combined GREEN 14.3 and REFACTOR 14.5 into a single commit
  ("feat: status reports an in-flight baseline") rather than two separate ones —
  extracting `_collecting_envelope(claim)` was the natural way to implement
  `cmd_status`'s branch without duplicating cycle 12/13's response-building logic,
  so it was written directly rather than duplicated then refactored out a commit
  later. All three call sites (`progress --json`, bare `progress`, `status`) now
  share one function. Full suite re-run clean (105 passed).

### Cycle 15: doctor probes collection per project and attributes the failure
- **Test:** `test_doctor_attributes_a_collection_failure_to_its_project` (fixture:
  `repo_broken`)
- **Stub needed?** Yes — `Adapter.collectable(self) -> GateResult: raise
  NotImplementedError` in `base.py`.
- **RED as expected?** Yes —
  ```
  AssertionError: [{'check': 'worktree resolvable', ...}, {'check': 'backend:
  adapter known', ...}, ...]
  assert []
  ```
  no check mentions `yaml_does_not_exist` — matches EXPECTED FAILURE exactly.
- **Files outside plan:** none
- **Tests deleted, skipped, or weakened?** none
- **Plan defect?** none
- **Friction note:** implemented `collectable()` for both adapters (pytest:
  whole-suite `--collect-only`, reading **stdout**, per P2; vitest: `npx vitest
  list` at the project root, mirroring the same whole-suite shape) even though only
  the pytest path is exercised by `repo_broken`. `docs/PRD.md` §10 gained
  `Adapter.collectable` in the interface table and a new R10.7 documenting the
  stdout/stderr distinction and that this is a *separate* probe from R10.3/R10.4's
  per-file `collect()` (the one that must stay untouched, per the plan's scope
  cuts).

### Cycle 16: doctor groups its results per project
- **Test:** `test_doctor_reports_a_per_project_result_map`
- **Stub needed?** No
- **RED as expected?** Yes — `KeyError: 'projects'`, matches EXPECTED FAILURE exactly.
- **Files outside plan:** none
- **Tests deleted, skipped, or weakened?** none — one pre-existing test in this same
  plan (`test_doctor_attributes_a_collection_failure_to_its_project`, written in
  cycle 15) was *updated*, not weakened: it switched from asserting a `"verify"`
  substring in the `check` name to asserting `c.get("project") == "verify"`,
  because 16.5's refactor legitimately changed what that field contains. This is
  the exact "modifies_tests" case the plan calls out for this cycle, just applying
  to cycle 15's test instead of (only) `test_doctor_ignores_nested_checkouts` — that
  one was confirmed still passing unmodified, per the plan's own prediction (its
  `no legacy state artifacts` check carries no project prefix).
- **Plan defect?** none
- **Friction note:** combined GREEN 16.3 and REFACTOR 16.5 into the `projects`
  map's implementation directly (one commit), then split out the explicit-
  `project=`-field refactor and its one required test update into a second, separate
  commit — closer to the plan's two-commit structure than cycle 14 managed, though
  still not a strict GREEN-then-separately-REFACTOR split. Full suite green
  throughout (107 passed).

### Cycle 17: doctor exits non-zero when the environment is unhealthy
- **Test:** `test_doctor_fails_when_a_check_fails`
- **Stub needed?** No
- **RED as expected?** Yes —
  ```
  AssertionError: {'ok': True, 'run': None, 'result': {'checks': [...],
  ...}, ...}
  assert True is False
  ```
  matches EXPECTED FAILURE ("doctor returns `ok: true` with `healthy: false`") exactly.
- **Files outside plan:** none
- **Tests deleted, skipped, or weakened?** none
- **Plan defect?** none
- **Friction note:** smooth. `docs/PRD.md` §8's doctor row now states the `ok`/
  `healthy` exit contract.

### Cycle 18: a vitest project with no node_modules gets a named error
- **Test:** `test_doctor_names_a_missing_node_modules` (fixture: `repo_multi`)
- **Stub needed?** No
- **RED as expected?** Yes —
  ```
  AssertionError: [{'check': 'root exists', ...}, ..., {'check': 'collectable',
  'ok': True, 'detail': '', 'project': 'frontend'}]
  assert []
  ```
  matches EXPECTED FAILURE exactly.
- **Files outside plan:** none
- **Tests deleted, skipped, or weakened?** none
- **Plan defect?** none
- **Friction note:** the full-suite run twice hit `test_only_reporting_flags_are_
  appended` again (same pre-existing flake as cycle 7 — the random `tdd-pytest-`
  tempdir suffix occasionally starts with `q`, tripping a `"-q" not in ...`
  substring check). Confirmed unrelated by running it standalone 5×: failed once,
  passed four times, with zero connection to doctor or vitest code. Not fixed
  (out of plan scope); full suite green on retry (109 passed).

### Cycle 19: the tool tells a re-running agent to wait instead
- **Test:** `test_baseline_in_progress_tells_the_agent_to_poll`
- **Stub needed?** No
- **RED as expected?** Yes —
  ```
  AssertionError: assert 'tdd progress' in 'a baseline is already being collected
  in this worktree'
  ```
  matches EXPECTED FAILURE exactly (cycle 3's prose mentions neither phrase).
- **Files outside plan:** none
- **Tests deleted, skipped, or weakened?** none
- **Plan defect?** none
- **Friction note:** added a "Running a long baseline" section to `README.md`
  between "Commands" and "Storage", stating the three options in the plan's stated
  order of preference (background > raise timeout > poll) and naming the concrete
  Bash-tool timeout ceiling (600000ms max). Full suite: **110 passed**, meeting the
  plan's stated done-criteria floor exactly (91 baseline + 19 new tests).

## Summary

### Test Setup & Design Smells
* **Hardest test overall:** `test_only_one_of_two_concurrent_starts_wins` (cycle 4).
  It exercises real thread-level concurrency against two process-global resources
  (`contextlib.redirect_stdout`, `os.chdir`) that the existing `run_cli` test helper
  was never built to survive, and it surfaced a genuine production bug (an unrolled-
  back SQLite transaction on a failed `INSERT`) that no other test in this plan or
  the pre-existing suite would ever have found, because nothing else runs two real
  baseline probes against one worktree at once.
* **Mock burden:** No test in this plan exceeds 2 mocks or 15 lines of setup.
  `monkeypatch.setattr(adapters, "build", spy)` (cycles 2, 9) is the heaviest
  pattern, used exactly as P6 validated it.
* **Architectural smell:** `Ledger.insert`'s missing rollback-on-failure (fixed in
  cycle 4) is the one real smell surfaced: any method that lets a caller observe a
  `sqlite3.IntegrityError` (the claim mechanism's entire design, per Finding 4) was
  silently relying on the *caller* never triggering it under real concurrency until
  this plan's cycle 4 did. A `Ledger` that guaranteed transactional cleanup on every
  path — not just `insert` — would remove this class of bug entirely rather than
  patching the one call site that happened to get exercised.

### Unplanned Changes
* **Files modified outside plan:** none. `tests/test_doctor_attribution.py`'s
  cycle-15 test was updated in cycle 16 to match a schema change 16.5's own refactor
  introduced (see cycle 16's entry) — an in-plan test the same plan's later step
  legitimately touched, not an out-of-plan file.

### New Work Raised
| Item | Evidence (file:symbol) | Why it matters | Severity |
|---|---|---|---|
| `Ledger.insert`/`update` leave the connection's transaction open on any exception, not only the `IntegrityError` this plan patched around | `src/tddcli/ledger.py:Ledger.insert` (fixed here); `Ledger.update` still lacks the same rollback | Any future caller that lets an `insert`/`update` fail (constraint violation, disk full, etc.) under concurrent access can reproduce cycle 4's ~65s lock-contention hang | Medium |
| `test_only_reporting_flags_are_appended` in `tests/test_project_commands.py` is flaky — a random `tempfile.TemporaryDirectory` suffix occasionally collides with the CLI-flag substrings it asserts against (`-q` and similar) | `tests/test_project_commands.py:test_only_reporting_flags_are_appended` (unrelated to this plan; hit twice during full-suite runs in cycles 7 and 18) | A CI run can fail for a reason with nothing to do with the change under review, wasting a human's time chasing it | Low |
| `Engine.sweep` (CLOSE_SWEEP phase) does not emit a `project_completed` heartbeat — only `Engine.run_projects` (RED/GREEN checks) does, despite cycle 10's own prose claiming "close sweeps included" | `src/tddcli/machine.py:Engine.sweep` vs `Engine.run_projects` | A close sweep on a large multi-project plan is exactly the kind of slow, silent operation issue #1 is about; it currently has no heartbeat at all | Medium |
| ~~`Ledger.active_claim`'s cross-host staleness fallback (60-minute age) was untested~~ — closed during the `raise-pr` pseudo-mutation gate with `test_a_fresh_cross_host_claim_is_not_stale` / `test_an_old_cross_host_claim_is_stale` | `src/tddcli/ledger.py:Ledger.active_claim`; `tests/test_run_claim.py` | The Decisions table calls this branch out explicitly (PIDs meaningless across hosts) | Resolved |

### Plan Quality
* **Plan Quality (1–5):** 4 — Exceptionally well-evidenced (six numbered probes, a
  behaviour census, explicit scope cuts) and the two flagged risk areas (cycle 2's
  vacuous RED, cycle 15's stdout/stderr bug) were exactly right. Docked one point
  for four cycles (3, 4, 6 partially, 13) whose stated EXPECTED FAILURE text didn't
  hold once earlier cycles in the same plan had actually landed — the plan reasoned
  about each cycle's RED somewhat independently of the cumulative state the prior
  cycles' GREENs would leave behind, rather than tracing the exact code path cycle
  by cycle. All four were still genuine REDs, just via a different mechanism than
  predicted, so the plan remained safely executable throughout — this is a
  prediction-accuracy gap, not a soundness gap.
* **Design Quality (1–5):** 4 — The claim mechanism (UNIQUE-insert-as-lock, an
  append-only observer method, staleness computed rather than stored) is a clean,
  well-reasoned design that closes a real concurrency bug without introducing a
  second source of truth. Docked one point for `Ledger`'s inconsistent transaction
  hygiene (see New Work Raised) — a preexisting condition this plan worked around
  in one spot rather than fixing at the root.
* **Top refactoring recommendation:** Make `Ledger.insert`/`update`/`db.execute`
  transactionally safe uniformly (e.g. a `_write()` wrapper or `with self.db:`
  used everywhere), rather than the ad hoc `try/except: rollback(); raise` this
  plan added to `insert` alone. The claim mechanism depends on failed writes being
  cheap and side-effect-free; right now that's true only where this plan happened
  to test it under load.
