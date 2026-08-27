---
closes: 46
cycles:
  - n: 1
    project: tddcli
    title: "run start accepts --baseline-jobs N, default 1"
    test: "tests/test_baseline_integrity.py::test_run_start_accepts_baseline_jobs_flag"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: run start accepts --baseline-jobs"
    commit_green: "feat: --baseline-jobs flag on run start (parsed, default 1)"

  - n: 2
    project: tddcli
    title: "--baseline-jobs below 1 is refused"
    test: "tests/test_baseline_integrity.py::test_run_start_refuses_baseline_jobs_below_one"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: --baseline-jobs must be >= 1"
    commit_green: "feat: reject --baseline-jobs < 1 before probing"

  - n: 3
    project: tddcli
    title: "with jobs>1 the reachable projects are probed concurrently"
    test: "tests/test_baseline_integrity.py::test_run_start_probes_concurrently_under_a_bounded_pool"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: run start probes concurrently under a bounded pool"
    commit_green: "feat: bounded ThreadPoolExecutor for baseline probing when jobs>1"

  - n: 4
    project: tddcli
    title: "baseline_captured heartbeat is emitted per project under concurrency"
    test: "tests/test_heartbeat.py::test_baseline_captured_lines_emitted_under_concurrency"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: baseline_captured heartbeat survives the worker pool"
    commit_green: "feat: emit baseline_captured from the main thread as probes complete"

  - n: 5
    project: tddcli
    title: "a probe failure under concurrency aborts before a run row and releases the claim"
    test: "tests/test_baseline_integrity.py::test_concurrent_probe_failure_aborts_and_releases_claim"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: a concurrent probe failure aborts cleanly and frees the worktree"
    commit_green: "fix: a worker probe exception becomes an attributed failure, claim released"
---

# Issue #46 — parallelize baseline probing with a bounded worker pool

https://github.com/geuben/tdd-cli/issues/46
Task file: `tasks/issue-46-parallel-baseline-probing.md`

## Context

`run start` captures every reachable project's baseline serially: `_probe_projects`
(`cli.py`) iterates the project mapping, and for each one runs the suite, collects, and
emits a `baseline_captured` heartbeat before moving to the next. On a repo with many
independent projects the wall-clock cost is the **sum** of the per-project suite
runtimes when it could approach the **max** — each probe is already self-contained: one
adapter instance, one `Verdict`, one `Collection`, one heartbeat, one pair of monotonic
timings. Nothing about probe *k* depends on probe *k-1*.

This issue schedules those probes on a bounded worker pool. It is deliberately
**behaviour-neutral**: the same projects are probed, the same refusal conditions (R9.5a)
apply, the same `baseline`/`collection_snapshot` rows are written, and any single probe
failure still aborts `run start` before a run row exists — only the *schedule* changes.
Concurrency is a knob (`--baseline-jobs N`) whose **default is 1 (serial)**; the serial
path is left byte-for-byte as it is today, so every existing serial guarantee (and the
existing heartbeat ordering test) holds untouched, and a caller opts into parallelism
only when their suites tolerate it.

The one hard constraint the design is built around is the ledger's threading model (see
Verified facts): the ledger is a **single shared sqlite connection created on the main
thread**, so *no worker may touch it*. Workers therefore run only the adapter (which
shells out — I/O-bound, GIL released) and **return** their results; the main thread does
every ledger write (`update_claim`, `baseline`/`collection_snapshot` inserts) and every
heartbeat. Under concurrency `projects_done` becomes a completed-count and
`current_project` the most-recently-finished project — both already tolerated by their
only readers (progress/fleet display).

Ordering: cycle 1 lands the flag surface (parsed, still serial); cycle 2 guards its
domain; cycle 3 introduces the pool and proves real concurrency; cycle 4 restores the
per-project heartbeat on the pool path; cycle 5 pins the abort-and-release safety net.
This composes with the already-merged #44 scoping — the pool schedules exactly the
`reachable_projects` subset `cmd_run_start` already computes.

## Verified repo facts

*Every fact below was read from the code or executed during hardening — none are
asserted from memory. Locators are function/line names; grep for them at execution
time.*

- **KEY ledger thread-safety finding.** `Ledger.__init__` (`ledger.py`) opens one
  connection — `self.db = sqlite3.connect(self.path, timeout=30.0)` — with **no
  `check_same_thread=False`**, so Python's default `check_same_thread=True` applies: that
  connection may be used **only from the thread that created it** (the main thread). Every
  write (`insert`, `update`, `update_claim`, `release_claim`, `event`) funnels through
  `self.db` via `_write`/direct `self.db.execute`. A worker thread calling any ledger
  method would raise `sqlite3.ProgrammingError: SQLite objects created in a thread can
  only be used in that same thread`. **Design consequence, load-bearing:** workers must
  perform *no* ledger access; they return probe data and the main thread does all writes.
  A worker that violated this would blow up under the real threads in cycle 3's test, so
  the test doubles as the guard for this rule.
- `_probe_projects(projects, worktree, ledger, on_progress)` (`cli.py`) today loops
  `enumerate(projects.items(), start=1)`; per project it calls `adapters.build`,
  `adapter.run(None)`, `adapter.collect()`, times each with `time.monotonic()`, emits
  `heartbeat(event="baseline_captured", ...)` with `test_count`/`elapsed_s`/`run_s`/
  `collect_s`, then calls `on_progress(done, name)`. It returns `{name: (verdict,
  collection)}`. The heartbeat and `on_progress` are the only two side-effects; the rest
  is pure per-project work that returns a value — exactly the shape a worker can return.
- `cmd_run_start` (`cli.py`) already scopes probing to `reachable_projects` (#44,
  merged): it builds `probe_projects` (a `{name: project}` subset), calls
  `ledger.claim(..., projects_total=len(probe_projects))`, then inside a
  `try/.../finally: ledger.release_claim(...)` calls `_probe_projects(probe_projects, ...,
  on_progress=lambda done, name: ledger.update_claim(...))`, runs the refusal checks over
  `probes.items()`, inserts the run row, then the `baseline` + `collection_snapshot` rows
  from the same `probes`. The pool must live **inside** the existing `try`, so its
  `finally` keeps releasing the claim; the refusal checks and row inserts stay on the main
  thread over the returned `probes` dict and need no change.
- The `on_progress` callback writes the claim via `ledger.update_claim` — **a ledger
  write**, so it must be invoked on the main thread, never inside a worker. Under the pool,
  call it as each future completes (a completed-count), not from the worker.
- **Adapter isolation audit (the issue's required audit) — per-instance, no shared
  mutable state across the built-in adapters, with two operator-owned caveats:**
  - `adapters.build(project, worktree)` (`adapters/__init__.py`) constructs a **fresh**
    adapter instance per call; `Adapter.__init__` (`base.py`) only stores
    `project`/`worktree`/`root`. No module-level or class-level mutable state is shared.
  - **pytest** (`pytest_adapter.py:_suite_report`): writes its JSON report into a fresh
    `tempfile.TemporaryDirectory(prefix="tdd-pytest-")` **per invocation** — a unique path
    each probe, no cross-thread collision. This was an explicit prior-bug fix ("a stale
    report can never be read as if current").
  - **vitest** (`vitest_adapter.py`): reads results from **stdout**
    (`--reporter=json` → `_extract_json(out)`) — no report file at all, nothing to collide.
  - **gradle** (`gradle_adapter.py`): reads `self.root/**/build/test-results/**/*.xml`
    — a path under the **project's own root**. Distinct projects have distinct roots, and
    we probe each project exactly once, so no two concurrent probes share it.
  - **Caveat 1 — xctest** (`xctest_adapter.py` docstring): the operator's `test_command`
    typically carries `-derivedDataPath /tmp/app-unit-dd` and a fixed simulator
    `-destination`. Those are **operator-declared, shared, global resources**: two xctest
    projects pointing at the same derived-data dir or simulator would corrupt each other
    under concurrency. This is precisely the "suites contending for global resources
    (ports/simulators) may need `--baseline-jobs 1`" caveat.
  - **Caveat 2 — the existing `lease` mechanism already neutralises Caveat 1 without a new
    default.** `Adapter._run_suite` (`base.py`) wraps a suite that declares
    `lease = "<name>"` in `leases.named_lease` — an **exclusive, machine-wide** lock
    (`leases.py`). Two probes whose suites share a lease name serialize automatically
    even inside the pool. `leases.worker_lease` (`base.py`) additionally splits the
    core budget across every live suite invocation, so N concurrent probes each take
    `cores // N` workers — the pool does not oversubscribe the box. **No lease change is in
    scope here**; this is recorded so the plan does not reinvent serialization.
- **Existing serial-ordering guard stays green untouched.**
  `tests/test_heartbeat.py::test_claim_records_projects_done_as_each_completes`
  (`test_heartbeat.py`) monkeypatches `adapters.build` with a spy that reads
  `active_claim` at each build and asserts `build` is called in `tdd.toml` order with
  `projects_done == 1` / `projects_total == 2` on the second call. This is a **serial**
  guarantee and is preserved because the default (`jobs=1`) path is left exactly as today
  — the spy still sees the in-thread `on_progress` fire between builds. Do not modify this
  test; if it breaks, the serial path was not left intact.
- **Claim counters have three readers, all display-only, none order-sensitive.**
  `_collecting_envelope` (`cli.py`) and `fleet.py` render
  `projects_done`/`current_project`; `update_claim` (`ledger.py`) writes them. Under
  concurrency `projects_done` reads as "how many finished" and `current_project` as "the
  one most recently finished" — both sensible for a progress display and asserted nowhere
  as an ordering. `test_fleet.py` and `test_progress.py` build claims **by hand**
  via `update_claim` and never go through `run start`, so the pool cannot perturb them.
- **Refusal checks are order-independent** (`cli.py`): they iterate `probes.items()`
  checking `not collection.tests and collection.failed_files` and `collection.tests and
  not verdict.passed and not verdict.failed`, each returning a `failure(...)` envelope
  **before** any run row is inserted, inside the `try` whose `finally` releases the claim.
  They keep working verbatim over the dict the pool returns.
- **Probe-verified RED for the flag (cycle 1):** the `run start` subparser
  (`cli.py`) has `--plan/--executor/--allow-dirty/--allow-undeclared/--baseline-all`
  but **no `--baseline-jobs`**. Passing it today makes `argparse` raise `SystemExit(2)`
  ("unrecognized arguments: --baseline-jobs"), caught by `main` (`cli.py`) which
  returns the exit code with empty stdout — so `run_cli`'s `json.loads(stdout)` raises
  `JSONDecodeError`. Write the cycle-1 test around the *post-GREEN* behaviour (call it,
  assert an ok envelope); today the call cannot even produce an envelope.
- **Fixtures.** `repo_three` (`conftest.py`) is `backend` + `svc` + `other`, all pytest,
  with artifact `schema` `produced_by = "backend"`, `consumed_by = ["svc"]`; a plan
  declaring only `backend` makes `{backend, svc}` reachable and skips `other` (proven by
  `test_run_start_probes_only_reachable_projects`). This is the multi-project fixture for
  cycles 3–5: default scoping gives **two** concurrent probes (compose with #44), and
  `--baseline-all` gives three. `repo` (`conftest.py`) is single-project `backend` for
  cycle 1. Harness helpers `run_cli`, `run_cli_text`, `write_plan` are in `conftest.py`;
  stderr is captured with `capsys` (see the `_heartbeat_lines` helper in
  `test_heartbeat.py`).
- **Fake-adapter shape for the deterministic concurrency tests (probe-verified).** A test
  double returned from a monkeypatched `adapters.build` needs `run(target=None) -> Verdict`
  and `collect() -> Collection`. To clear the refusal checks it must return
  `Collection(tests={...non-empty...})` and `Verdict(passed=[...non-empty...], failed=[])`
  (`Verdict`/`Collection` in `adapters/base.py`). **Verified during hardening:** a fake of
  exactly this shape (`Verdict(project=…, adapter="pytest", passed=["t::a"])`,
  `Collection(tests={"t::a","t::b"})`), monkeypatched over `adapters.build` and driven
  through a plain serial `run start` on `repo_three`, clears both refusal checks and returns
  `result["baselines"] == {"backend": 0, "svc": 0}` (`svc` reachable, `other` skipped —
  composes with #44). So a probe can be fully synthetic (no real test runner), making the
  concurrency and failure cycles fast and hermetic.
- The `run start` envelope's `result["baselines"]` is `{n: len(v) for n, v in
  ledger.baselines(run_id).items()}` (`cli.py`) — a project-keyed dict, so assertions
  compare by content and are immune to probe-completion order.

## Cycle detail

*Expected failure per cycle, probe-verified where marked; minimum GREEN; resist future
cycles' behaviour.*

### Cycle 1 — the `--baseline-jobs` flag exists (still serial)

**Expected RED (probed):** `argparse` rejects `--baseline-jobs`: `SystemExit(2)`, no
envelope on stdout, so `run_cli` raises `json.JSONDecodeError`. Write the test around the
GREEN behaviour and let the un-implemented flag fail it via that raise (mirror the
exemplar's cycle-7 `--baseline-all` note).

Test (`repo`, single project): `run start --plan <p> --baseline-jobs 2` returns an ok
envelope with `result["baselines"] == {"backend": 0}`. GREEN: add
`s.add_argument("--baseline-jobs", type=int, default=1, help=...)` to the `run start`
subparser. **This cycle does not parallelise** — the value is parsed and available on
`args`; `_probe_projects` is untouched and still serial. Resist wiring the pool here.

### Cycle 2 — `--baseline-jobs` below 1 is refused

**Expected RED:** `run start --plan <p> --baseline-jobs 0` returns an **ok** envelope
today (the value is parsed but unused, so probing runs serially) where the test expects a
failure envelope.

Test (`repo`): `--baseline-jobs 0` → `out["ok"] is False` and the error names the
constraint (e.g. "--baseline-jobs must be >= 1"); assert no run row exists for the
worktree. GREEN: in `cmd_run_start`, before `ledger.claim`, `if args.baseline_jobs < 1:
return failure("--baseline-jobs must be >= 1")`. This guards the pool's `max_workers`
(which raises `ValueError` at 0) and stops a silent misconfiguration from reading as
serial. One line, one behaviour.

### Cycle 3 — bounded concurrent probing

**Expected RED (deterministic, barrier-based):** with a monkeypatched `adapters.build`
whose `run` blocks on `threading.Barrier(2, timeout=T)`, a serial probe never lets two
probes reach the barrier together → the first `barrier.wait` times out →
`BrokenBarrierError` propagates out of the probe. The test asserts an ok envelope **and**
a recorded peak concurrency of 2, both of which fail while probing is serial.

Test (`repo_three`, plan declares `backend` only → reachable `{backend, svc}` = 2 probes,
composing with #44): monkeypatch `adapters.build` to return a fake adapter sharing a
`threading.Barrier(2)` and a lock-guarded peak-concurrency counter (increment on `run`
entry, decrement on exit, record the max). Run `run start --plan <p> --baseline-jobs 2`.
Assert `out["ok"]`, `result["baselines"] == {"backend": 0, "svc": 0}`, and the observed
peak == 2. The barrier is a hard synchronisation point, so the test is not timing-flaky:
under a real pool both probes must be in-flight for it to release; under serial it can
never release.

GREEN: give `_probe_projects` a `jobs: int = 1` parameter and thread `jobs=args.baseline_jobs`
through from `cmd_run_start`. When `jobs <= 1`, run the **existing serial loop unchanged**
(preserves cycle-1 default and the heartbeat-ordering test). When `jobs > 1`, submit one
task per project to `concurrent.futures.ThreadPoolExecutor(max_workers=jobs)`; each worker
does `adapters.build` → `adapter.run(None)` → `adapter.collect()` and captures its
monotonic `run_s`/`collect_s`/`elapsed_s` and `test_count`, then **returns** a small
result (name + verdict + collection + timings). The worker touches **no ledger and emits
no heartbeat** (Verified facts: the sqlite connection is main-thread-only). The main
thread drains `as_completed`, and per completed future calls `on_progress(done_count,
name)` (a completed-count) and stores into `probes[name] = (verdict, collection)`. Return
`probes` exactly as before so the refusal checks and row inserts downstream are untouched.
**Do not emit the `baseline_captured` heartbeat yet** — that is cycle 4, kept separate so
this cycle's GREEN is only "the probes run concurrently and the baselines are correct".

### Cycle 4 — the `baseline_captured` heartbeat survives the pool

**Expected RED:** under `--baseline-jobs 2` on `repo_three`, cycle 3's pool path emits no
`baseline_captured` line, so a `capsys`-captured stderr scan finds none for `backend`/`svc`
(the serial path still emits them, which is why the existing
`test_baseline_captured_line_is_written_per_project` stayed green — it runs at the default
`jobs=1`).

Test (`repo_three`, `--baseline-jobs 2`, `capsys`): assert a `baseline_captured`
heartbeat line exists for **each** probed project, each carrying an int `test_count` and a
numeric `elapsed_s` (reuse `_heartbeat_lines`). GREEN: on the pool path, as each future
completes on the **main thread**, emit `heartbeat(event="baseline_captured", project=name,
test_count=len(collection.tests), elapsed_s=..., run_s=..., collect_s=...)` from the
timings the worker returned. Emitting on the main thread (not the worker) keeps the
heartbeat stream and all ledger writes on one thread and makes ordering the completion
order. The serial path's existing heartbeat is unchanged.

### Cycle 5 — a concurrent probe failure aborts before a run row and releases the claim

**Expected RED:** with a monkeypatched `adapters.build` whose `svc` probe's `run` raises
`RuntimeError`, the pool's `future.result()` re-raises inside `cmd_run_start`; the
`RuntimeError` is not in `main`'s caught tuple (`cli.py`), so `run_cli` sees an
uncaught exception (its `main(...)` call raises) instead of a clean failure envelope —
the test, which expects `out["ok"] is False`, errors out.

Test (`repo_three`, `--baseline-jobs 2`): a fake where `backend` probes fine and `svc`'s
`run` raises. Assert `out["ok"] is False` and the error is attributed to `svc`; assert
**no** run row exists for the worktree (`SELECT * FROM run WHERE worktree_path = ?`); and
assert the worktree is **retryable** — a second `run start` is *not* rejected with
`reason == "baseline_in_progress"`, proving the claim was released. GREEN: on the pool
path, gather results so a worker exception becomes an **attributed `failure(...)`
envelope** returned from within the existing `try` (e.g. catch the exception off
`future.result()` and return `failure(f"{name}: baseline probe failed: {exc}",
project=name)`), leaving no run row and letting the existing `finally: ledger.release_claim`
free the worktree. This is the issue's safety contract made observable: same refusal
semantics, same claim release, only the schedule changed.

**Resist:** do not add retry, partial-baseline, or per-probe timeout logic — a single
failure aborts the whole start, exactly as the serial path does today.

## Deliberate scope cuts (do not build)

- **Processes / a process pool.** Probes are I/O-bound (each shells out to a real test
  runner via `subprocess.run`, releasing the GIL), so threads suffice and keep adapters,
  `project` objects, and the ledger un-pickled and in one address space. No `ProcessPoolExecutor`.
- **Any change to the `lease` machinery.** `named_lease`/`worker_lease` (`leases.py`)
  already serialize lease-declaring suites and split the core budget across concurrent
  probes. Composing with them is free; extending them is a separate issue.
- **Claim-counter semantics under concurrency have no dedicated test.**
  `projects_done`/`current_project` become a completed-count / most-recently-finished and
  are released before the envelope returns — cosmetic (progress/fleet display), asserted
  by no ordering test. Mirrors #44's `projects_total` scope cut. The serial
  `test_claim_records_projects_done_as_each_completes` remains the honest guard for the
  default path.
- **Changing the default.** The default stays `--baseline-jobs 1` (serial). Adapters that
  contend for global resources (xctest simulators, port-bound suites) are the caller's to
  raise deliberately, or to serialize with a `lease`. Do not raise the default here.
- **Auto-tuning the job count** (e.g. from `os.cpu_count()` or `leases.snapshot()`). The
  worker-lease budget already prevents oversubscription; a smart default is out of scope.
- **PRD/README documentation** of `--baseline-jobs` and the concurrency model: same PR,
  after the run completes, as ordinary commits — not a cycle (see Done-criteria).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do
not ask the user to start the run. `tdd run start` records which model is executing,
resolved from your own session; a run started by anyone else attributes this work to the
wrong agent.

The branch `feat/46-parallel-baseline-probing` already exists — it was created at
hardening and carries this plan's commit. Check it out; if it has grown unrelated work,
stop and ask.

    git checkout feat/46-parallel-baseline-probing   # exists: created at hardening, carries this plan

**Referee rule:** run the *released* `tdd` **0.7.0**, never this working tree's editable
install. Do not work in a shell with this repo's `.venv` activated. Verify before
starting: `tdd --version` → **0.7.0**.

> **Environment blocker found at hardening (2026-08-23):** `~/.local/bin/tdd` is stale at
> **0.6.0**, which understands ledger schema only up to v2 and *cannot open this repo's
> v3 ledger* — `tdd doctor` fails with "written by a newer tdd-cli". Meanwhile `which tdd`
> may resolve to a `.venv` on `PATH`. Before starting you MUST have 0.7.0 as the `tdd` you
> invoke: `uv tool upgrade tdd-cli` (or reinstall) so `~/.local/bin/tdd --version` → 0.7.0,
> and confirm `which tdd` points at a 0.7.0 binary that is **not**
> `/Volumes/SSD/repos/tdd-cli/.venv` (this working tree's own editable install). A separate
> 0.7.0 clone is fine.

The suites under test are still this working tree's code; only the controller is pinned.

    tdd doctor                                       # must report healthy: true
    tdd run start --plan tasks/issue-46-parallel-baseline-probing.md

The plan file is already committed on this branch. `tdd doctor` must be green first: if it
reports "worktree clean" failing on *other* uncommitted `tasks/issue-*.md` files (sibling
plans not part of this work), commit, stash, or gitignore them before `run start`.

Then repeat until done: read `next_action.verb`, do exactly what it says, run
`tdd advance`. Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit
it, and raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit`
  — the tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. Expected
  baseline for this repo: `{"tddcli": 0}` — anything else means a moved branch; stop.
- Verbs this plan can hit: `run_sensitivity_check` → `tdd sensitivity begin|check|end`
  (only if a RED passes on arrival — none is expected to); `resolve_blocker` → `tdd
  blocker --kind --detail` (kinds: `plan_defect`, `tooling`, `regression`,
  `pre_existing_failure`); `confirm_cycle_applicable` on a cycle the codebase has outgrown
  → `tdd cycle skip --reason`. This plan declares no `annotation_keys`.
- Cycles 3 and 5 use `threading.Barrier`/a fake `adapters.build`; keep barrier `timeout`
  small but non-zero so a genuinely serial regression fails fast rather than hanging the
  suite.

## Done-criteria

**Before finishing:** run `tdd log render --out
tasks/friction-logs/issue-46-parallel-baseline-probing-friction.md` and `tdd metrics`.
Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity
event. Do not narrate what the ledger already records.

Then the documentation follow-up, committed as ordinary commits on the branch after the
run is terminal: the PRD R9.5 family (document `--baseline-jobs`, the default-serial
stance, the main-thread-only-ledger constraint, and the xctest/global-resource caveat)
and the README's `run start` section.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-46-parallel-baseline-probing-friction.md
    git commit -m "docs: friction log for issue-46-parallel-baseline-probing"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes
the branch and opens the PR against `main`. Do not push or call the GitHub API by hand.
If a gate fails, fix it and re-run the skill — a failed gate is work, not a reason to hand
back.
