# Plan: address `docs/multi-agent-feedback.md`

Nineteen TDD cycles closing the five issues from the 2026-08-04 five-agent parallel run.

**Execution mode: legacy.** This repo has no `tdd.toml` and is not registered with its own
tool. The executor drives `tdd-step`/`tdd-run` by hand — see *Pre-flight* and *Execution
Contract* at the end of this file. Registering tdd-cli with itself is separate work: it needs
`Project.owns` to handle a root-level project, which it cannot today.

> **Read cycle 19 first.** Issue #1's root cause is the agent's 120s Bash timeout, which no
> change to this tool can lift. The heartbeat makes a slow baseline *legible*; what makes it
> *survivable* is invoking `tdd run start` in the background (the harness re-invokes the agent
> on exit — a genuine callback) or with an explicit longer timeout. Cycle 19 carries more of
> issue #1 than the eleven code cycles before it.

## Baseline

`uv run pytest -q` on `main` at the time of hardening: **`91 passed in 26.15s`**. Green. Any
failure at pre-flight is a blocker, not the work.

## Evidence from probing (not reasoning)

Four throwaway probes were run against the real code and deleted. What they established:

**P1 — issue #4 reproduces exactly.** Two `run start` calls against one worktree via
`ThreadPoolExecutor` both returned `ok: true`. Two runs, one worktree, no error. This is the
bug, and it confirms cycle 4's test is the one that matters.

**P2 — issue #3's root cause is a wrong stream, not a missing check.** `tdd doctor` against a
project whose test file raises `ModuleNotFoundError` reports
`verify: pytest-json-report installed → ok: false` with this detail:

```
warning: `VIRTUAL_ENV=...` does not match the project environment path `.venv` and will be
ignored; use `--active` to target the active environment instead\nUsing
```

The real error is nowhere in it. The check reads the subprocess's **stderr**, and `uv` writes
environment warnings there while pytest writes the actual `ModuleNotFoundError` to **stdout**.
Cycle 15 must read stdout. This is the single most important line in this plan.

**P3 — the whole-suite collection probe works and is cheap.** `uv run pytest --collect-only -q`
in the broken project exits 2 in **0.04s** with `ModuleNotFoundError: No module named
'yaml_does_not_exist'` and `ERROR tests/test_v.py` on stdout. Cycle 15's approach is validated,
and it is nowhere near the per-file loop's cost.

**P4 — a broken project cannot start a run.** `run start` with a second project whose files all
fail to collect returns the R9.5a refusal. **Therefore two fixtures are needed, not one:** a
*healthy* multi-project fixture for the run-based cycles, and a *broken* one for doctor, which
needs no run. This is the correction that would otherwise have burned cycles 9 and 15.

**P5 — a second project with no test files is startable.** `run start` with an empty vitest
`frontend` succeeded, reporting `baselines: {backend: 0, frontend: 0}`. That is the shape of the
healthy fixture.

**P6 — the seams work.** `sqlite3` raises `IntegrityError: UNIQUE constraint failed` as cycle 3
requires. `capsys` sees stderr through `run_cli` as cycles 7–10 require.
`monkeypatch.setattr(adapters, "build", spy)` observes the probe loop in order
`['backend', 'frontend']`, which is the seam cycle 9 needs.

**Caveat, from P1:** `run_cli` uses `contextlib.redirect_stdout` and `os.chdir`, both
process-global. Under threads the redirections interleave, so **the concurrency test must assert
on returned envelopes, never on captured output.** No crash, no cwd corruption — but printed
output from a threaded test is unreliable.

## Findings from reading the code

**1. The heartbeat cannot go to stdout.** PRD §8 states *"Every command emits JSON on stdout
with a common envelope"*, and `run_cli` in `tests/conftest.py` does `json.loads(stdout)`.
Prepending NDJSON breaks the envelope contract and every existing test. The heartbeat goes to
**stderr**; nothing in `src/` writes there today.

**2. Issue #4's guard already exists and is ineffective.** `cmd_run_start` rejects a second run
(grep `a run is already active`) — but the run row is not inserted until after the probe loop
(grep `run_id = ledger.insert`). During the baseline window there is no run row, so both
processes pass. Confirmed by P1.

**3. R9.5a forbids the obvious fix for issue #2.** R9.5a states *"The check runs before the run
row is written, so a refusal leaves nothing behind to block the next attempt."* Inserting the
run row early would contradict it. A separate self-releasing `baseline_claim` row serves both
issues.

**4. Naive claiming reintroduces the race.** `Ledger.__init__` commits per statement with no
spanning transaction, so check-then-insert is two commits. `baseline_claim.worktree_path`
carries `UNIQUE` and **the insert is the lock** — `IntegrityError` is the rejection path.

## Decisions

| # | Decision | Rationale |
|---|---|---|
| Heartbeat transport | stderr, not stdout | Finding 1 — stdout is a contract |
| Claim liveness | `hostname` + `pid`, age fallback across hosts | PIDs are reused and meaningless from another host; a false "alive" bricks the worktree, a false "dead" reopens the bug |
| Doctor collection probe | whole-suite `--collect-only`, **not** `collect()` | `collect()` is the per-file loop that *causes* issue #1. P3 shows the whole-suite probe costs 0.04s |
| Doctor probe stream | **stdout** | P2 — reading stderr is the root cause of issue #3 |
| Polling verb | new `await_baseline`, `VERB_SET_VERSION` → 2 | R8.3a makes the verb set closed; no existing verb means *wait and poll again* |
| Collecting response `ok` | `true` | A polling agent must not see repeated exit-1 — that is the signal that caused the re-runs |
| Doctor exit code | non-zero when unhealthy | Nothing shells out to doctor (no `.claude/`, no hooks); `run_cli` ignores exit codes |
| `active_claim` | reads only, returns a `stale` flag | Pollers must not mutate an append-only store. Only `cmd_run_start` acts on staleness |
| Claim progress detail | overall `elapsed_s` only | A poller needs "is it moving"; `projects_done` answers that |
| Agent guidance | background > longer timeout > poll | The harness re-invokes an agent when a backgrounded command exits — a real callback |
| PRD | updated inside the cycles that change behaviour | R-numbers are cited throughout the code |

## Behaviour census

Every behaviour this plan's prose promises, and the test that pins it:

| Behaviour | Status | Cycle |
|---|---|---|
| Active-run rejection names the run | PINNED | 1 |
| Claim taken before probing, released on success | PINNED | 2 |
| Concurrent start rejected | PINNED | 3 |
| Two racing starts → exactly one winner | PINNED | 4 |
| Refused baseline releases the claim | PINNED | 5 |
| Stale claim reclaimed | PINNED | 6 |
| Per-project baseline heartbeat | PINNED | 7 |
| Heartbeat carries elapsed time | PINNED | 8 |
| Claim records per-project progress | PINNED | 9 |
| Sweep heartbeat | PINNED | 10 |
| `await_baseline` verb exists | PINNED | 11 |
| `progress --json` reports collecting | PINNED | 12 |
| Bare `progress` reports collecting | PINNED | 13 |
| `status` reports collecting | PINNED | 14 |
| Doctor attributes a collection failure | PINNED | 15 |
| Doctor reports per-project map | PINNED | 16 |
| Doctor exits non-zero when unhealthy | PINNED | 17 |
| Doctor names a missing `node_modules` | PINNED | 18 |
| Rejection prose tells the agent to poll | PINNED | 19 |

**Deliberate scope cuts — do not build:**
- Parallelising per-file collection to make the baseline fast. R10.3/R10.4 require per-file
  collection; speeding it up is separate work with its own risk.
- Scoping `doctor` to a plan's projects (a `--project` flag). The feedback calls current
  behaviour "arguably correct".
- Fixing `INSERT OR IGNORE INTO meta` so `SCHEMA_VERSION` updates on an existing ledger. Real
  gap, out of scope, **do not fix it in passing**.
- Registering tdd-cli with itself (`Project.owns` for a root-level project).

## Preconditions (before cycle 1)

**Schema.** Add to `SCHEMA` in `src/tddcli/ledger.py`:

```sql
CREATE TABLE IF NOT EXISTS baseline_claim (
    id INTEGER PRIMARY KEY,
    worktree_path TEXT NOT NULL UNIQUE,
    hostname TEXT NOT NULL,
    pid INTEGER NOT NULL,
    projects_total INTEGER NOT NULL DEFAULT 0,
    projects_done INTEGER NOT NULL DEFAULT 0,
    current_project TEXT,
    started_at TEXT NOT NULL
);
```

`SCHEMA` runs `CREATE TABLE IF NOT EXISTS` on every open, so no migration machinery is needed.
Bump `SCHEMA_VERSION` to 2 for the R13.2 record.

**Two fixtures in `tests/conftest.py`** — P4 proved one will not do:

- `repo_multi` — `repo` plus an **empty** vitest `frontend` (a `package.json`, no test files).
  P5 proved this starts a run cleanly. Used by cycles 9, 18.
- `repo_broken` — `repo` plus a **second pytest project** `verify` whose `tests/test_v.py`
  begins `import yaml_does_not_exist`, mirroring the real `pyyaml` incident. **Cannot start a
  run** (P4) and must only be used by doctor cycles 15–17, which need no run.

*Fixture friction, expect it:* `uv run` inside a second project creates `verify/.venv`, so
`worktree clean` reports false in doctor output for `repo_broken`. Assert on the specific check
you care about, never on `healthy`.

**Test files.** New: `tests/test_run_claim.py` (1–6), `tests/test_heartbeat.py` (7–10),
`tests/test_doctor_attribution.py` (15–18). Cycles 12–13 extend `tests/test_progress.py`.

**Stderr capture.** `run_cli`/`run_cli_text` redirect stdout only, so heartbeat cycles capture
stderr with `capsys` (P6 confirmed this works).

---

## Part A — worktree claim (issue #4, foundation for #2)

### Cycle 1: the existing already-active rejection carries machine-readable detail

**Production target:** `cmd_run_start` in `src/tddcli/cli.py` (grep `a run is already active`).
**Test file:** `tests/test_run_claim.py`.

STUB     1.0 — None needed; no new symbol.
RED      1.1 — Write test `test_second_start_reports_the_active_run_id`: after one successful
`run start`, a second returns `result["reason"] == "run_already_active"` and
`result["run_id"] == 1`.
EXPECTED FAILURE — `KeyError: 'reason'`; the current rejection's `result` is `{}`.
COMMIT   1.2 — Commit failing test: "test: second run start names the active run"
GREEN    1.3 — Pass `reason="run_already_active"`, `run_id=active["id"]`,
`started_at=active["started_at"]` through `failure(**result)`. Prose stays in `error`, the
machine key in `result`, per R8.3a.
COMMIT   1.4 — Commit implementation: "feat: an already-active run is identified in the rejection"

### Cycle 2: `run start` claims the worktree before probing and releases it on success

**Production target:** `Ledger.claim` / `release_claim` / `active_claim` in
`src/tddcli/ledger.py`; `cmd_run_start` in `src/tddcli/cli.py`.
**Test file:** `tests/test_run_claim.py`.

STUB     2.0 — Add `baseline_claim` to `SCHEMA` and `Ledger.claim`, `release_claim`,
`active_claim` raising `NotImplementedError`. No logic. Must satisfy ruff.
RED      2.1 — Write test `test_successful_start_leaves_no_claim`: after a normal `run start`,
`Ledger(...).all("SELECT * FROM baseline_claim")` is empty.
EXPECTED FAILURE — before the stub, `sqlite3.OperationalError: no such table: baseline_claim`;
after the stub the table exists and the test passes vacuously, so **write the test to assert the
claim was taken and released** by spying with `monkeypatch.setattr(adapters, "build", spy)`
(P6) and recording `active_claim` inside the spy. Then the failure is
`AssertionError: claim was never taken`.
COMMIT   2.2 — Commit failing test: "test: a completed start releases its claim"
GREEN    2.3 — Implement the three methods. In `cmd_run_start`, claim immediately before the
probe loop and release in a `try/finally` around probe-and-insert.
COMMIT   2.4 — Commit implementation: "feat: run start claims the worktree while probing"

### Cycle 3: a concurrent `run start` during baseline collection is rejected

**Production target:** `cmd_run_start` in `src/tddcli/cli.py`.
**Test file:** `tests/test_run_claim.py`.

RED      3.1 — Write test `test_start_is_rejected_while_a_baseline_is_collecting`: insert a
`baseline_claim` row for the worktree naming `socket.gethostname()` and `os.getpid()`, then call
`run start`; it returns `ok: false` with `result["reason"] == "baseline_in_progress"`.
EXPECTED FAILURE — `assert out["ok"] is False` fails; the run starts normally and returns
`ok: true`.
COMMIT   3.2 — Commit failing test: "test: a start during baseline collection is refused"
GREEN    3.3 — Let `Ledger.claim` propagate the `UNIQUE` violation; catch `sqlite3.IntegrityError`
in `cmd_run_start` and return the rejection. **The insert is the lock** — do not add a
read-then-write check, which is the race this cycle exists to close (Finding 4, P6).
COMMIT   3.4 — Commit implementation: "fix: two starts could both pass the guard during baseline"

### Cycle 4: exactly one of two concurrent starts wins the claim

**Production target:** none — this cycle pins cycle 3's implementation against regression.
**Test file:** `tests/test_run_claim.py`.

RED      4.1 — Write test `test_only_one_of_two_concurrent_starts_wins`: two `run start` calls
against one worktree via `ThreadPoolExecutor(max_workers=2)`; assert exactly one returned
envelope has `ok: true`. **Assert on returned envelopes only** — `run_cli` redirects stdout
process-globally and threaded output interleaves (P1 caveat).
EXPECTED FAILURE — on current code both succeed: `assert [True, True].count(True) == 1` fails.
This is P1, reproduced as a test.
COMMIT   4.2 — Commit failing test: "test: concurrent starts resolve to a single winner"
GREEN    4.3 — Expected to pass on the strength of cycle 3. If it does not, the implementation
drifted back to read-then-write — fix it here, **do not weaken the test**. Cycle 3 proves the
rejection *branch*; this proves the *race*.
COMMIT   4.4 — Commit implementation: "test: pin the concurrent-start race"

### Cycle 5: a refused baseline releases its claim

**Production target:** `cmd_run_start` in `src/tddcli/cli.py` (grep `no test could be collected`).
**Test file:** `tests/test_run_claim.py`.

RED      5.1 — Write test `test_a_refused_baseline_leaves_no_claim`: using a project whose files
all fail to collect, `run start` returns `ok: false` **and** `baseline_claim` is empty, so a
retry is possible.
EXPECTED FAILURE — `AssertionError` on the claim table being non-empty; the R9.5a refusal
returns before the release.
COMMIT   5.2 — Commit failing test: "test: an R9.5a refusal releases the claim"
GREEN    5.3 — Ensure the `finally` from cycle 2 encloses the R9.5a refusal returns, not only
the success path.
COMMIT   5.4 — Commit implementation: "fix: a refused baseline no longer strands its claim"

### Cycle 6: a claim whose owner is gone is reclaimed

**Production target:** `Ledger.active_claim` in `src/tddcli/ledger.py`; `cmd_run_start`.
**Test file:** `tests/test_run_claim.py`.

RED      6.1 — Write test `test_a_claim_from_a_dead_process_is_reclaimed`: insert a claim naming
`socket.gethostname()` and a pid that is not running (allocate one, then assert it is gone), and
confirm `run start` proceeds and returns `ok: true`.
EXPECTED FAILURE — after cycle 3, the start is refused: `assert out["ok"]` fails with
`reason == "baseline_in_progress"`.
COMMIT   6.2 — Commit failing test: "test: a dead process's claim does not brick the worktree"
GREEN    6.3 — Have `active_claim` return the row with a computed `stale` flag — true when
`hostname == socket.gethostname()` and `os.kill(pid, 0)` raises `ProcessLookupError`, or when the
hostname differs and the row is older than 60 minutes. Only `cmd_run_start` acts on it, calling
`release_claim` before claiming. **`active_claim` must not delete**: `cmd_progress` and
`cmd_status` call it as pure observers, and `ledger.py`'s docstring holds this store append-only.
Without reclaim, one `SIGKILL`ed `run start` blocks the worktree forever.
COMMIT   6.4 — Commit implementation: "feat: a stale claim is reclaimed rather than obeyed"

---

## Part B — heartbeat (issue #1)

### Cycle 7: each completed project baseline emits a line to stderr

**Production target:** `heartbeat` in `src/tddcli/envelope.py`; `cmd_run_start` in `cli.py`.
**Test file:** `tests/test_heartbeat.py`.

STUB     7.0 — Add `def heartbeat(**fields) -> None:` to `src/tddcli/envelope.py` raising
`NotImplementedError`. New symbol imported by the test — declare it before RED.
RED      7.1 — Write test `test_baseline_captured_line_is_written_per_project`: capture with
`capsys` (P6); one stderr line parses as JSON with `event == "baseline_captured"`,
`project == "backend"`, and an integer `test_count`.
EXPECTED FAILURE — `AssertionError: no baseline_captured line in stderr`; stderr is empty.
COMMIT   7.2 — Commit failing test: "test: baseline collection emits a per-project heartbeat"
GREEN    7.3 — Implement `heartbeat` writing `json.dumps(fields)` and a newline to `sys.stderr`
with `flush=True` — unflushed output defeats the entire purpose. It lives in `envelope.py`, not
`cli.py`, because cycle 10 calls it from `machine.py`. Call it in the probe loop.
COMMIT   7.4 — Commit implementation: "feat: run start emits a per-project baseline heartbeat"

### Cycle 8: the heartbeat reports elapsed seconds per project

**Production target:** `cmd_run_start` in `src/tddcli/cli.py`.
**Test file:** `tests/test_heartbeat.py`.

RED      8.1 — Write test `test_baseline_heartbeat_reports_elapsed_seconds`: the
`baseline_captured` line carries a numeric `elapsed_s`.
EXPECTED FAILURE — `KeyError: 'elapsed_s'`.
COMMIT   8.2 — Commit failing test: "test: the baseline heartbeat times each project"
GREEN    8.3 — Wrap each project's probe in a `time.monotonic()` span; include the rounded delta.
COMMIT   8.4 — Commit implementation: "feat: the baseline heartbeat carries per-project elapsed time"

### Cycle 9: the claim records per-project progress as it goes

**Production target:** `Ledger.update_claim` in `src/tddcli/ledger.py`; `cmd_run_start`.
**Test file:** `tests/test_heartbeat.py`. **Fixture: `repo_multi`** (healthy, P5).

STUB     9.0 — Add `Ledger.update_claim` raising `NotImplementedError`.
RED      9.1 — Write test `test_claim_records_projects_done_as_each_completes`. **Seam, proven by
P6:** `monkeypatch.setattr(adapters, "build", spy)`; the spy records `active_claim(...)` on each
call. `build` is called once per project in `tdd.toml` order (`['backend', 'frontend']`), so the
row seen on the **second** call reports `projects_done == 1` and `projects_total == 2`.
EXPECTED FAILURE — `AssertionError: 0 != 1`; nothing updates the claim.
COMMIT   9.2 — Commit failing test: "test: the claim tracks per-project baseline progress"
GREEN    9.3 — Implement `update_claim(worktree, projects_done, current_project)` and call it in
the probe loop beside the heartbeat. Counters and `started_at` only — no per-project timing
history; that lives in the stderr lines.
COMMIT   9.4 — Commit implementation: "feat: the claim records baseline progress per project"
REFACTOR 9.5 — Extract the probe loop from `cmd_run_start` into
`_probe_projects(cfg, worktree, ledger, on_progress)`. It now carries claiming, timing,
heartbeating and progress updates; `cmd_run_start` is past 100 lines and this is the seam.

### Cycle 10: each project in a sweep emits a completion heartbeat

**Production target:** `Engine.run_projects` in `src/tddcli/machine.py`.
**Test file:** `tests/test_heartbeat.py`.

RED      10.1 — Write test `test_sweep_emits_a_project_completed_line`: stderr during
`tdd advance` contains a line with `event == "project_completed"`, `project`, and `elapsed_s`.
EXPECTED FAILURE — `AssertionError: no project_completed line in stderr`.
COMMIT   10.2 — Commit failing test: "test: a sweep emits a per-project heartbeat"
GREEN    10.3 — Call `heartbeat` in `Engine.run_projects` after each verdict. One insertion point
covers every phase, close sweeps included. Emit unconditionally rather than past a duration
threshold — a conditional heartbeat goes silent exactly when a run is slow for an unexpected
reason. Distinct event name from `baseline_captured`: same channel, different meaning.
COMMIT   10.4 — Commit implementation: "feat: sweeps emit a per-project completion heartbeat"

---

## Part C — polling surfaces (issue #2)

### Cycle 11: the verb set gains `await_baseline`

**Production target:** `Verb` and `VERB_SET_VERSION` in `src/tddcli/envelope.py`; `docs/PRD.md` §8.
**Test file:** `tests/test_contract.py`.

RED      11.1 — Write test `test_await_baseline_is_a_non_terminal_verb`: `Verb.AWAIT_BASELINE`
exists, is not in `TERMINAL_VERBS`, and `NextAction(...).to_dict()["verb_set_version"] == 2`.
EXPECTED FAILURE — `AttributeError: AWAIT_BASELINE`.
COMMIT   11.2 — Commit failing test: "test: await_baseline joins the verb set"
GREEN    11.3 — Add `AWAIT_BASELINE = "await_baseline"`, bump `VERB_SET_VERSION` to 2, and add
the verb to the R8.3a table in `docs/PRD.md` §8. R8.3a states that adding a verb is a
specification change; this cycle is that change. Nothing external pins the version — the
`tdd-step`/`tdd-run` skills do not dispatch on these verbs.
COMMIT   11.4 — Commit implementation: "feat: await_baseline tells a polling agent to wait"

### Cycle 12: `progress --json` reports collecting_baseline instead of "no runs recorded"

**Production target:** `cmd_progress` in `src/tddcli/cli.py` (grep `no runs recorded`).
**Test file:** `tests/test_progress.py`.

RED      12.1 — Write test `test_progress_reports_collecting_baseline_when_a_claim_is_open`: with
an open claim and no run row, `progress --json` returns `ok: true`,
`result["status"] == "collecting_baseline"`, and verb `await_baseline`.
EXPECTED FAILURE — `assert out["ok"]` fails; returns
`{"ok": false, "error": "no runs recorded for this worktree"}`.
COMMIT   12.2 — Commit failing test: "test: progress distinguishes collecting from never-started"
GREEN    12.3 — In `cmd_progress`, consult `active_claim` before the `no runs recorded` return
and return the collecting envelope with `projects_done`, `projects_total`, `current_project` and
overall `elapsed_s`. `ok: true` — a polling agent must not see exit-1.
COMMIT   12.4 — Commit implementation: "feat: progress reports an in-flight baseline"

### Cycle 13: the bare `tdd progress` reports it too

**Production target:** `cmd_progress` in `src/tddcli/cli.py`; `progress` in `src/tddcli/render.py`.
**Test file:** `tests/test_progress.py`.

RED      13.1 — Write test `test_bare_progress_reports_collecting_baseline`:
`run_cli_text(repo, "progress")` with an open claim contains `collecting baseline` and the
project counters.
EXPECTED FAILURE — `AssertionError`; output is the JSON failure envelope, since the
`no runs recorded` return precedes the `--json` branch.
COMMIT   13.2 — Commit failing test: "test: the human progress view reports collecting baseline"
GREEN    13.3 — Render a text line for the non-`--json` path. Leaving the human form saying "no
runs recorded" while JSON says "collecting" is the same ambiguity in a new place.
COMMIT   13.4 — Commit implementation: "feat: the human progress view reports an in-flight baseline"

### Cycle 14: `tdd status` reports it as well

**Production target:** `cmd_status` in `src/tddcli/cli.py`.
**Test file:** `tests/test_progress.py`.

RED      14.1 — Write test `test_status_reports_collecting_baseline`: with an open claim and no
run, `status` returns `result["status"] == "collecting_baseline"` and verb `await_baseline`.
EXPECTED FAILURE — `KeyError: 'status'`; `cmd_status` returns `{"active": False}`.
COMMIT   14.2 — Commit failing test: "test: status reports an in-flight baseline"
GREEN    14.3 — Add the same branch to `cmd_status` (already `require_run=False`). `status` is
documented as the agent's machine view; agents polled `progress` because `status` gave them
nothing, and routing agents to the human command to learn machine state is the actual defect.
COMMIT   14.4 — Commit implementation: "feat: status reports an in-flight baseline"
REFACTOR 14.5 — Extract the branch shared by `cmd_progress` and `cmd_status` into
`_collecting_envelope(claim)`. Three call sites now build the same response.

---

## Part D — `tdd doctor` (issues #3 and #5)

### Cycle 15: doctor probes collection per project and attributes the failure

**Production target:** `Adapter.collectable` in `src/tddcli/adapters/base.py`, implemented in
`pytest_adapter.py` and `vitest_adapter.py`; `cmd_doctor` in `src/tddcli/cli.py`.
**Test file:** `tests/test_doctor_attribution.py`. **Fixture: `repo_broken`** (P4 — it cannot
start a run, and doctor needs none).

STUB     15.0 — Add `def collectable(self) -> GateResult: raise NotImplementedError` to
`Adapter` in `base.py`. New symbol; declare before RED.
RED      15.1 — Write test `test_doctor_attributes_a_collection_failure_to_its_project`: `doctor`
on `repo_broken` returns a check naming `verify` whose `detail` contains
`yaml_does_not_exist`.
EXPECTED FAILURE — no check mentions the module. P2 showed the closest existing check,
`verify: pytest-json-report installed`, carries only a `uv` VIRTUAL_ENV warning.
COMMIT   15.2 — Commit failing test: "test: doctor names the project that failed to collect"
GREEN    15.3 — Implement `collectable()` as a **single whole-suite** `--collect-only` at the
project root (P3: exit 2 in 0.04s). **Read the subprocess's stdout, not its stderr** — P2 proved
pytest writes `ModuleNotFoundError` to stdout while `uv` writes environment noise to stderr, and
reading the wrong stream is the root cause of issue #3. Call it per project in `cmd_doctor` and
document the method in PRD §10. Do **not** call `collect()`: that is the per-file loop behind
issue #1. `collect()` is unchanged, so R10.3 is untouched.
COMMIT   15.4 — Commit implementation: "fix: doctor read the wrong stream and lost the real error"

### Cycle 16: doctor groups its results per project

**Production target:** `cmd_doctor` in `src/tddcli/cli.py`.
**Test file:** `tests/test_doctor_attribution.py`. **Fixture: `repo_broken`.**

RED      16.1 — Write test `test_doctor_reports_a_per_project_result_map`: `result["projects"]`
maps project name to `{"ok": bool}` with `projects["verify"]["ok"] is False`.
EXPECTED FAILURE — `KeyError: 'projects'`.
COMMIT   16.2 — Commit failing test: "test: doctor reports a per-project result map"
GREEN    16.3 — Build `projects` alongside `checks`. **Keep `checks`** —
`test_doctor_ignores_nested_checkouts` in `tests/test_end_to_end.py` asserts on it by name.
COMMIT   16.4 — Commit implementation: "feat: doctor summarises health per project"
REFACTOR 16.5 — Replace the `f"{name}: ..."` string-prefix convention with an explicit `project=`
field on the check dict. The prefix becomes load-bearing at 16.3 and string parsing is the wrong
seam for that. **`modifies_tests`:** `test_doctor_ignores_nested_checkouts` looks up checks by
the `check` key — confirm it still passes; the `no legacy state artifacts` check it uses has no
project prefix, so it should be untouched.

### Cycle 17: doctor exits non-zero when the environment is unhealthy

**Production target:** `cmd_doctor` in `src/tddcli/cli.py` (grep `healthy`); `docs/PRD.md` §8.
**Test file:** `tests/test_doctor_attribution.py`. **Fixture: `repo_broken`.**

RED      17.1 — Write test `test_doctor_fails_when_a_check_fails`: with a failing check,
`cmd_doctor`'s envelope has `ok is False`.
EXPECTED FAILURE — `assert out["ok"] is False` fails; P2 showed doctor returns `ok: true` with
`healthy: false`.
COMMIT   17.2 — Commit failing test: "test: an unhealthy environment fails doctor"
GREEN    17.3 — Return `ok=healthy` rather than the hardcoded `ok=True`, and state the exit
contract in PRD §8's doctor row. Verb-dispatching consumers are unaffected — `RESOLVE_BLOCKER`
already distinguishes the unhealthy case per R8.1.
COMMIT   17.4 — Commit implementation: "fix: doctor reported success on an unhealthy environment"

### Cycle 18: a vitest project with no node_modules gets a named error

**Production target:** `cmd_doctor` in `src/tddcli/cli.py`.
**Test file:** `tests/test_doctor_attribution.py`. **Fixture: `repo_multi`** (its `frontend` is
vitest with no `node_modules`).

RED      18.1 — Write test `test_doctor_names_a_missing_node_modules`: a check's detail contains
`node_modules`, and does not contain a vitest stack trace.
EXPECTED FAILURE — `AssertionError: no check mentions node_modules`.
COMMIT   18.2 — Commit failing test: "test: doctor names a missing node_modules directly"
GREEN    18.3 — When `project.adapter == "vitest"` and `root/"node_modules"` is not a directory,
add a failing `node_modules present` check whose detail states that git worktrees do not inherit
`node_modules` and names the symlink fix. Run it **before** the `collectable()` probe so the
actionable message wins over the stack trace.
COMMIT   18.4 — Commit implementation: "feat: doctor names a missing node_modules for vitest projects"

---

## Part E — the guidance that actually closes issue #1

### Cycle 19: the tool tells a re-running agent to wait instead

**Production target:** `cmd_run_start` in `src/tddcli/cli.py`; `README.md`.
**Test file:** `tests/test_run_claim.py`.

RED      19.1 — Write test `test_baseline_in_progress_tells_the_agent_to_poll`: the
`baseline_in_progress` rejection's `error` string contains both `tdd progress` and
`do not re-run`.
EXPECTED FAILURE — `AssertionError`; cycle 3's prose does not mention either.
COMMIT   19.2 — Commit failing test: "test: the rejection tells an agent what to do instead"
GREEN    19.3 — Write the rejection prose, and add a `README.md` section on running a long
baseline, in this order of preference:
1. **Background it.** The harness re-invokes the agent when the command exits — a real callback,
   no timeout ceiling, and the heartbeat lands in the task log.
2. **Raise the timeout.** Claude Code's Bash tool takes an explicit `timeout`, default 120000ms,
   max 600000ms. A 3–8 minute baseline fits in ten minutes.
3. **Poll.** `tdd progress` returns `await_baseline` while collecting — the fallback for an
   agent that inherited a run it did not start.

Issue #1's root cause is the 120s Bash default, which no change to this tool can lift. Cycles
7–14 make a slow baseline *legible*; this cycle makes it *survivable*. The rejection message is
the one thing a re-running agent is guaranteed to read.
COMMIT   19.4 — Commit implementation: "docs: name the three ways to survive a long baseline"

---

## Summary of files

**Modified:** `src/tddcli/ledger.py`, `src/tddcli/envelope.py`, `src/tddcli/cli.py`,
`src/tddcli/machine.py`, `src/tddcli/adapters/base.py`, `src/tddcli/adapters/pytest_adapter.py`,
`src/tddcli/adapters/vitest_adapter.py`, `docs/PRD.md`, `README.md`, `tests/conftest.py`,
`tests/test_progress.py`, `tests/test_contract.py`

**Created:** `tests/test_run_claim.py`, `tests/test_heartbeat.py`,
`tests/test_doctor_attribution.py`

---

## Pre-flight: Test Suite Gate & Branch Creation

**1. Confirm the test suite is green.** Run `uv run pytest -q` from the repository root — not a
subdirectory — and **quote the summary line**. The plan's baseline is `91 passed in 26.15s`.

- Suite green → proceed.
- Any failure → **stop immediately.** A red baseline means failures you introduce are
  undetectable.

**2. Create a dedicated git branch.** `git checkout -b multi-agent-feedback`. If it already
exists, stop and ask — do not force-checkout.

## Execution Contract: Autonomous Implementation

Execute the plan **without handing back to the user** between steps.

- Use `tdd-run` for every TDD cycle. Do not hand-step phases.
- For non-TDD steps (the schema and fixture preconditions, the PRD and README edits), execute
  directly and continue.
- **Do not pause for confirmation** between cycles.
- **The only valid reasons to stop:** (1) a regression in code you did not touch; (2) an
  unresolvable plan/codebase conflict needing user input; (3) a tool or environment failure
  blocking progress.
- **"This requires updating existing tests" is not one of them.** Neither is "this is larger than
  expected". Scope is the user's call: finish what you can, then say so.
- **Finish on the branch you created**, and end by committing the friction log and invoking the
  `raise-pr` skill. Raising the PR is part of the work, not a follow-up question.

**Integrity rules — violating any invalidates the run:**

- **Commit after every RED and every GREEN.** Collapsing cycles means no RED was observed
  failing. No scripted or regex-driven bulk edits.
- **Never delete, skip, `xfail`, or weaken a test to reach green.** A test that resists passing is
  evidence; deleting it destroys that evidence.
- **Run the full suite, never a subdirectory**, and quote the summary line.
- **Never report a step complete without having run the thing that proves it.**
- If a RED test passes on arrival, do not proceed. Run a **sensitivity check**: temporarily break
  the production path the test claims to cover, confirm the test fails, then restore. Record it
  in the friction log. If the test still passes with the path broken, stop and surface it.
- If a test fails with `ImportError`/`ModuleNotFoundError`/`NameError` on the target symbol, the
  RED phase has not started — stop, create the stub, re-run. RED means "test runs and fails on an
  assertion", never "test crashes on import".

## Friction Log: Incremental Recording Protocol

Written **incrementally**, not at the end — context compaction erases in-memory observations.

**Step 0 — before any cycle:** create `tasks/friction-logs/multi-agent-feedback-friction.md` at
the **repository root** with the header below. Never create a second one under a project
directory.
**After every COMMIT:** append one cycle entry.
**Whenever you notice work this task will not do:** append a row to *New Work Raised* immediately.
**Final:** fill in the Summary. Reconstruct missing entries from `git log` first.

```markdown
# Implementation Friction Log: multi-agent-feedback
Date: <YYYY-MM-DD>
Executor: <Agent Model Name>
Plan File: tasks/multi-agent-feedback.md
```

```markdown
### Cycle <N>: <cycle name>
- **Test:** `<test name>` (or "pre-existing: <name>" / "non-TDD: <step>")
- **Stub needed?** Yes — `<what was stubbed>` / No
- **RED as expected?** Yes — `<paste the actual failure>` / Passed-on-arrival — sensitivity
  check: `<what was broken>` → `<the exact failure>`
- **Files outside plan:** none / `<file>` — <why>
- **Tests deleted, skipped, or weakened?** none / `<name>` — <STOP: blocker>
- **Plan defect?** none / <description>
- **Friction note:** <one line, or "smooth">
```

**The RED and sensitivity fields require pasted output, not a verdict.** "Yes", "confirmed" and
"validated" are not evidence and will be treated as the step not having been run.

```markdown
## Summary

### Test Setup & Design Smells
* **Hardest test overall:** <test and why>
* **Mock burden:** >2 mocks or >15 lines of setup anywhere? <yes — file:test / no>
* **Architectural smell:** <specific, or "none">

### Unplanned Changes
* **Files modified outside plan:** <list with reasons, or "none">

### New Work Raised
| Item | Evidence (file:symbol) | Why it matters | Severity |
|---|---|---|---|

### Plan Quality
* **Plan Quality (1–5):** <score> — <justification>
* **Design Quality (1–5):** <score> — <justification>
* **Top refactoring recommendation:** <single most valuable change>
```

## Done-criteria

1. Full suite green from the repository root, summary line quoted. Expect **110+ passed**
   (91 baseline plus this plan's ~19 new tests).
2. Every cycle's named test exists — verify by grep, not memory.
3. No test deleted, skipped, or weakened. Confirm with
   `git diff main --stat -- tests/` showing no net deletions.
4. One commit per RED and per GREEN, confirmed with `git log --oneline main..HEAD`.
5. Friction log finalised at `tasks/friction-logs/multi-agent-feedback-friction.md`, with all
   deviations recorded.
6. Commit the friction log:
   `git add tasks/friction-logs/multi-agent-feedback-friction.md && git commit -m "docs: friction log for multi-agent-feedback"`
7. Invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the branch
   and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate fails,
   fix it and re-run the skill — a failed gate is work, not a reason to hand back.
