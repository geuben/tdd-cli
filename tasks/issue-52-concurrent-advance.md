---
closes: 52
cycles:
  - n: 1
    project: tddcli
    title: "close_cycle is a no-op when the ledger says the row is already closed"
    test: "tests/test_concurrent_advance.py::test_close_cycle_is_idempotent_when_the_row_is_already_closed"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: close_cycle called twice on one cycle row"
    commit_green: "fix: close_cycle re-reads closed_at and no-ops on an already-closed row"

  - n: 2
    project: tddcli
    title: "open_cycle returns the existing open row for an ordinal instead of inserting a duplicate"
    test: "tests/test_concurrent_advance.py::test_open_cycle_returns_the_existing_open_row_for_an_ordinal"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: open_cycle called twice for one ordinal"
    commit_green: "fix: open_cycle returns the existing open row for an ordinal"

  - n: 3
    project: tddcli
    title: "a second advance is refused while one is in flight"
    test: "tests/test_concurrent_advance.py::test_advance_is_rejected_while_another_advance_is_in_flight"
    files: ["src/tddcli/ledger.py", "src/tddcli/cli.py"]
    commit_red: "test: a second advance while one is in flight"
    commit_green: "feat: advance_claim table and an advance_in_flight refusal"

  - n: 4
    project: tddcli
    title: "the refusal tells the agent to wait rather than kill or re-run"
    test: "tests/test_concurrent_advance.py::test_advance_in_flight_directs_the_agent_to_wait"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: advance_in_flight refusal names elapsed, status, and do-not-re-run"
    commit_green: "feat: advance_in_flight reports pid, elapsed and the wait instruction"

  - n: 5
    project: tddcli
    title: "a dead holder's advance claim is reclaimed"
    test: "tests/test_concurrent_advance.py::test_a_dead_advance_claim_is_reclaimed"
    files: ["src/tddcli/ledger.py", "src/tddcli/cli.py"]
    commit_red: "test: an advance claim held by a dead pid"
    commit_green: "fix: reclaim a stale advance claim"
    commit_refactor: "refactor: one staleness rule shared by both claim kinds"

  - n: 6
    project: tddcli
    title: "the advance claim is released when the handler raises"
    test: "tests/test_concurrent_advance.py::test_advance_releases_its_claim_when_the_handler_raises"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: a raising advance must not leave its claim behind"
    commit_green: "fix: release the advance claim in a finally"
---

# Issue #52 — concurrent `tdd advance` double-closes a cycle and forks the run

https://github.com/geuben/tdd-cli/issues/52
Task file: `tasks/issue-52-concurrent-advance.md`

## Context

Two `tdd advance` processes in one worktree can both close the same cycle. Nothing
serialises `advance`: `leases.py` budgets test workers, it is not mutual exclusion, and
`cmd_advance` takes no claim.

`Engine.close_cycle` then turns one double-close into permanent corruption. It
unconditionally transitions the row to `CLOSED` and unconditionally calls
`open_cycle(nxt.ordinal)`, which unconditionally `INSERT`s. Two closes of cycle N
therefore create **two** rows for ordinal N+1, and `Ledger.open_cycle` — which selects
the open row with the lowest ordinal — thereafter ping-pongs between the two chains:
closing chain A's cycle N opens chain A's N+1, but chain B's N is still open at a lower
ordinal, so the next `advance` snaps back to it. Every remaining ordinal is written,
swept and closed twice, and the envelope only ever names one cycle number, so the
doubling is invisible to the agent driving the run.

Observed in a real 11-cycle run: cycles 3–11 each ran twice, roughly doubling wall
clock. The run "completed" when one chain reached the final ordinal, stranding the other
chain's last row open forever — `run.outcome = 'complete'` while `open_cycle()` still
returns a row, a state that should be impossible.

`tests/test_run_claim.py`'s own module docstring already describes this exact scenario
for the *other* long command: *"An agent whose `run start` times out at the harness
assumes failure and re-runs it; two probes then compete on one worktree's ledger."*
`advance` is the same hazard with no claim.

Ordering: cycles 1–2 make the ledger uncorruptible by a double close (the correctness
fix, no new state); cycles 3–6 add the claim that stops the second process doing the
redundant work at all (the ergonomic fix). The order matters — the claim is advisory and
there is always a window between "check claim" and "commit", so idempotency must land
first and must stand on its own.

## Verified repo facts

*Probed against this working tree during hardening — the RED path of cycles 1, 2 and 3
was executed, not reasoned about. Locators are symbol names; grep for them.*

### Probe results (executed, then deleted)

- **Cycle 1 RED, executed.** A run on the `repo` fixture with a two-cycle plan; snapshot
  the cycle-1 row; `engine.close_cycle(row)` twice with the *same* snapshot. Result
  today: **2 open cycle rows** and **2 rows at ordinal 2** (ids 2 and 3), two identical
  `AWAITING_TEST → CLOSED` transitions for cycle id 1, and the second call **returns a
  phantom new cycle row** (id 3). It also **overwrites `closed_at`** with a later
  timestamp. That phantom return is the observed run's `commit: null` "Cycle N closed"
  reply.
- **Cycle 2 RED, executed.** `engine.open_cycle(2)` twice returns ids `2` and `3` —
  different rows, both at ordinal 2.
- **Cycle 3 RED, executed.** `sqlite_master` on a fresh ledger lists no `advance_claim`
  table; `hasattr(Ledger, "claim_advance")` is `False`; and `run_cli(repo, "advance")`
  on a claimed worktree returns `ok: True` with verb `write_test`. Note this first
  `advance` runs **no suite** (the target test does not exist yet), so cycles 3–6 are
  fast tests.
- **`stub_expected` is empty for every cycle — probe-verified, not assumed.** Walking
  the imports of each specified RED test: `Ledger`, `Engine`, `gitutil`, `config`,
  `run_cli`, `write_plan` all exist today at the stated paths. No cycle introduces a new
  module. Cycle 3's test reaches a *missing method* on an existing class, and a probe
  confirmed the tool treats that correctly: a test raising `AttributeError: type object
  'Ledger' has no attribute 'claim_advance'` in its body **collects fine and reads as a
  legitimate RED** — the run moved to `AWAITING_IMPL` with verb `write_implementation`
  and committed the test. No `create_stub` round trip is expected anywhere in this plan.

### Code facts

- **`Engine.close_cycle` (`machine.py`) has exactly one caller**,
  `_handle_refactor` in `advance.py` — verified by grep over `src/` and `tests/`. Its
  blast radius is one call site.
- **The stale-snapshot trap — the crux of cycle 1.** `close_cycle` receives a
  `cycle_row` *snapshot* fetched by `cmd_advance` via `ledger.open_cycle(run["id"])`.
  The second process read that row **before** the first committed, so its snapshot still
  names the pre-close phase. A guard written as `if cycle_row["phase"] == CLOSED` does
  **not** fire — the probe above closed from an `AWAITING_TEST` snapshot and the row was
  already `CLOSED` in the ledger. The guard must re-read `closed_at` by row id.
- `Engine.transition` (`machine.py`) performs no legality check: it inserts a transition
  row and updates the phase unconditionally. Nothing today bars a second
  `→ CLOSED`.
- `Engine.open_cycle(ordinal)` (`machine.py`) always `INSERT`s. Besides `close_cycle` it
  is called by `cmd_run_start` and `cmd_cycle_skip` (`cli.py`) — so the duplicate-insert
  hole is reachable independently of the double close, which is why cycle 2 is its own
  cycle and not folded into cycle 1's GREEN.
- `Ledger.open_cycle(run_id)` (`ledger.py`) selects
  `WHERE closed_at IS NULL ORDER BY ordinal LIMIT 1` — the selection that makes two
  chains ping-pong rather than merely coexist.
- **The claim pattern already exists and is the model for cycles 3–6.** The
  `baseline_claim` table in `SCHEMA` (`ledger.py`) declares
  `worktree_path TEXT NOT NULL UNIQUE`; the `INSERT` *is* the lock (`Ledger.claim`, whose
  docstring says so), and `cmd_run_start` catches `sqlite3.IntegrityError` and returns
  `failure(..., reason="baseline_in_progress")` — an `ok: false` envelope with a `reason`
  key and **no verb**. Follow this exactly: adding a verb is a specification change (see
  the `envelope.py` module docstring) that would bump `VERB_SET_VERSION` off 2 and break
  every skill pinned to it, including `examples/skills/tdd-drive/SKILL.md`. A refusal
  needs no verb.
- `Ledger.active_claim` (`ledger.py`) computes staleness: same host → `os.kill(pid, 0)`,
  `ProcessLookupError` → stale, `PermissionError` → alive; cross-host → a 60-minute age
  fallback. Its docstring pins it as read-only — it never deletes. Cycle 5 reuses this
  rule; the `commit_refactor` extracts it so one rule serves both claim kinds.
- **Schema migration.** `SCHEMA_VERSION` is `2` and `MIGRATIONS` is keyed by the version
  upgraded *from*, with `""` where the idempotent `SCHEMA` script suffices. The upgrade
  loop indexes `MIGRATIONS[stored]` directly, so a missing key is a `KeyError`, not a
  silent skip. Adding `advance_claim` needs exactly: the table in `SCHEMA`,
  `SCHEMA_VERSION = 3`, and `MIGRATIONS[2] = ""` with a comment in the style of the
  existing v1→v2 line.
- **No test-side blast radius — checked, not assumed.** `tests/test_release_surface.py`
  is the only test touching schema versioning and it compares against the imported
  `SCHEMA_VERSION` symbol, never a literal `2`; `test_older_ledger_is_migrated_forward`
  walks a v1 ledger forward and is the existing guard that catches a missing
  `MIGRATIONS` key. No cycle in this plan declares `modifies_tests`, and none should
  need to. If one appears to, stop — it means the fix is wrong, not the test.
- **Test template.** `tests/test_run_claim.py` already tests this shape for the baseline
  claim: `test_start_is_rejected_while_a_baseline_is_collecting` inserts a claim row by
  hand and asserts `out["ok"] is False` plus the `reason`;
  `test_baseline_in_progress_tells_the_agent_to_poll` asserts on the *error prose*,
  which is the precedent authorising cycle 4's prose assertions;
  `test_a_claim_from_a_dead_process_is_reclaimed` gets a genuinely dead pid via
  `subprocess.Popen(["true"])` then `proc.wait()`, asserting `os.kill` raises
  `ProcessLookupError` before use — copy that recipe verbatim in cycle 5. Follow this
  file's style throughout; do not invent a new one.
- **Engine can be constructed directly**, and cycles 1–2 need this rather than a full
  run: `Engine(ledger, cfg, repo, run_row)` after `config_mod.load(repo)`, as
  `tests/test_baseline_integrity.py` does in its un-baselined sweep test. Cycles 1–2
  execute no suites.
- **The `repo` fixture's project is named `backend`**, not `tddcli` — `tddcli` is the
  project in *this* repo's own `tdd.toml`, which is what the front-matter's `project:`
  field names. Plans written against the fixture use `project: backend`. Do not confuse
  the two.
- `run_cli` (returns the parsed envelope), `run_cli_text`, `write_plan` and the `repo`
  fixture are in `tests/conftest.py`.
- `cmd_advance` (`cli.py`) is four lines: `_context()`, `_engine()`,
  `ledger.open_cycle(run["id"])`, then `do_advance(...)`. The claim wraps that last call.
  The `cycle is None` early return (run complete) must **not** take a claim — claiming to
  report "all cycles complete" would leave a row behind on a finished run.
- **`do_advance` is bound at import time**: `cli.py` does
  `from .advance import advance as do_advance`. Cycle 6 must therefore monkeypatch
  **`tddcli.cli.do_advance`** — patching `tddcli.advance.advance` leaves the already-bound
  name in `cli` untouched and the test will not do what it says.
- `cmd_status` (`cli.py`) only reads (`active_claim` is a pure observer per its
  docstring) and takes no claim, so it stays callable while an advance is in flight. No
  cycle needed; stated here so nobody "fixes" it.
- **No invariant registry in this repo** — `docs/` holds `PRD.md` and
  `harness-integration.md` only, no `INVARIANTS.md`. Nothing to reconcile.

## Cycle kinds

All six are **standard**. Each RED was probed and fails today: cycles 1, 2 and 3 by
execution (above); cycles 4, 5 and 6 build directly on cycle 3's new surface, so their
targets cannot pass before it exists. No cycle characterises existing behaviour, so
there is no pin cycle; no cycle is behaviour-preserving, so there is no refactor-only
cycle. Cycle 5 carries a refactor *phase* (`commit_refactor`), which is not the same as
a `refactor_cycle`.

## Cycle detail

*Expected failure per cycle; minimum GREEN; resist later cycles' behaviour.*

### Cycle 1 — idempotent close

**EXPECTED FAILURE (probed):** `assert 2 == 1` on the open-row count — the run ends with
two open cycle rows and two rows at ordinal 2.

Test (no suites, no `run_cli` beyond start): register a two-cycle plan and start a run on
`repo`, build `Engine(ledger, cfg, repo, run_row)`, read the cycle-1 row once and **keep
that snapshot**. Call `engine.close_cycle(cycle_row)` (opens ordinal 2), then call it
again with the same stale snapshot. Assert: exactly one row with `closed_at IS NULL` for
the run, exactly one `CLOSED` transition for cycle 1's id, exactly one row at ordinal 2,
and that cycle 1's `closed_at` is unchanged by the second call.

GREEN: at the top of `close_cycle`, re-read `closed_at` for `cycle_row["id"]`; if it is
non-null, return `self.ledger.open_cycle(self.run["id"])` without transitioning, without
re-stamping `closed_at`, and without opening anything. Returning the currently-open cycle
(rather than `None`) is what lets the loser of the race reply with the run's real
position instead of the phantom row the probe observed. Do not touch `_handle_refactor`;
its reply already renders whatever `close_cycle` returns.

### Cycle 2 — no duplicate row per ordinal

**EXPECTED FAILURE (probed):** the two calls return ids `2` and `3`; `assert a["id"] ==
b["id"]` fails and two rows exist at ordinal 2.

Test: same fixture, no closing involved. Call `engine.open_cycle(2)` twice; assert the
same `id` back both times and one row at ordinal 2.

GREEN: in `open_cycle`, before inserting, `SELECT` an existing row for
`(run_id, ordinal)` with `closed_at IS NULL` and return it if present. Keep the
`declared is None → return None` guard first — `cmd_cycle_skip` relies on it at the end
of a plan.

### Cycle 3 — the advance claim

**EXPECTED FAILURE (probed):** `assert True is False` — today the second advance runs,
returning `ok: True` with verb `write_test`.

Test: register and start a run on `repo`; insert an advance claim by hand
(`led.claim_advance(str(repo), hostname=socket.gethostname(), pid=os.getpid())`);
`run_cli(repo, "advance")` → `out["ok"] is False` and
`out["result"]["reason"] == "advance_in_flight"`. Direct copy of
`test_start_is_rejected_while_a_baseline_is_collecting`.

GREEN, minimum: `advance_claim` table (`id`, `worktree_path` UNIQUE, `hostname`, `pid`,
`started_at`) in `SCHEMA`; `SCHEMA_VERSION = 3`; `MIGRATIONS[2] = ""` with a comment;
`Ledger.claim_advance` and `Ledger.release_advance_claim`; in `cmd_advance`, attempt the
claim around `do_advance`, return `failure(..., reason="advance_in_flight")` on
`sqlite3.IntegrityError`, and release on the success path. **Release on the success path
only** — the `finally` is cycle 6's GREEN, and writing it here leaves cycle 6 with no
RED. This is this plan's most likely fidelity break.

### Cycle 4 — a refusal the agent can act on

**EXPECTED FAILURE:** `KeyError`/assertion on the missing `result` keys — cycle 3's
refusal carries only `reason`.

Test: as cycle 3, but assert `"do not re-run" in out["error"]`, `"tdd status" in
out["error"]`, and that `result` carries `pid`, `started_at` and an integer `elapsed_s`.
Precedent for asserting on prose: `test_baseline_in_progress_tells_the_agent_to_poll`.

GREEN: read the held claim row and populate those keys; write the prose to say an
advance is already running, how long it has been running, to wait for its envelope, and
to run `tdd status` meanwhile — and explicitly **not** to kill it and not to re-run. The
pid is evidence of liveness only. An agent that kills a close sweep between `git commit`
and `close_cycle` causes worse corruption than the bug this issue fixes.

### Cycle 5 — reclaim a dead holder

**EXPECTED FAILURE:** `assert False is True` — the dead claim still blocks after cycle 3.

Test: get a genuinely dead pid with the `subprocess.Popen(["true"])` recipe from
`test_a_claim_from_a_dead_process_is_reclaimed`, insert an advance claim naming it, then
`run_cli(repo, "advance")` → `ok is True`.

GREEN: before returning the refusal, compute staleness for the held claim; if stale,
delete it and proceed. REFACTOR (declared `commit_refactor`): the staleness rule now
exists twice — extract the hostname/pid/60-minute computation out of
`Ledger.active_claim` into one helper used by both claim kinds. The existing
`test_run_claim.py` staleness tests (fresh cross-host, old cross-host, dead pid) are the
guard; do not weaken them.

### Cycle 6 — release on the raising path

**EXPECTED FAILURE:** an `advance_claim` row remains after the raise, wedging the
worktree until it goes stale.

Test: start a run; `monkeypatch.setattr("tddcli.cli.do_advance", <raiser>)` — **not**
`tddcli.advance.advance`, which is bound at import and would leave `cmd_advance`
unaffected. Call `cmd_advance` directly under `pytest.raises` so the exception escapes
(`run_cli` is the wrong vehicle here), then assert no `advance_claim` row remains for the
worktree.

GREEN: move the release into a `finally`. The parallel is `cmd_run_start`'s documented
obligation to release its claim on the failure path — a failed attempt that keeps its
claim turns a recoverable error into a wedged worktree.

## Deliberate scope cuts (do not build)

- **No new verb.** A refusal is `ok: false` with a `reason`, exactly like
  `baseline_in_progress`. Adding `wait_for_advance` bumps `VERB_SET_VERSION` and breaks
  every skill pinned to 2 — not worth it for a caller error. If a verb is ever wanted, it
  is its own issue with a coordinated skill release.
- **Do not make the claim block or wait.** Blocking recreates the original failure: the
  second `advance` waits, hits the harness's command timeout, is backgrounded too, and
  two queued processes sweep back to back. `named_lease` (`leases.py`) blocks and is
  therefore the wrong primitive here despite fitting in every other respect.
- **No repair of already-forked ledgers.** Detection is one query
  (`SELECT run_id, ordinal, COUNT(*) FROM cycle GROUP BY run_id, ordinal HAVING
  COUNT(*) > 1`); automatic repair means guessing which chain's commits are real. Out of
  scope.
- **No change to `cmd_status`.** It is read-only and must stay callable while an advance
  holds the claim.
- **No change to heartbeat emission.** `heartbeat()` already writes to stderr with
  `flush=True` and `Engine.run_projects` emits `project_completed` unconditionally by
  design (its comment says why). The observed run's silence was
  `tdd advance 2>&1 | tail -25` buffering — a caller problem, already fixed in the
  harness docs, not in the tool.
- **No cross-process concurrency test.** `test_only_one_of_two_concurrent_starts_wins`
  exists for the baseline claim and documents in its own docstring why threading plus
  process-global stdout redirection is fragile. Cycles 3–6 test the claim's *mechanism*
  by inserting the row by hand, which is what that test's stable half does.
- **PRD/README documentation** of the claim and the idempotency invariant: same PR,
  after the run completes, not a cycle (see Done-criteria).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do
not ask the user to start the run. `tdd run start` records which model is executing,
resolved from your own session; a run started by anyone else attributes this work to the
wrong agent.

**Referee rule:** run the *released* `tdd`, never this working tree's editable install.
Do not work in a shell with this repo's `.venv` activated. Verify before starting:
`which tdd` must be `~/.local/bin/tdd` and `tdd --version` the pinned release (0.6.0).
**At hardening time it was neither** — it resolved into another checkout's `.venv`
(`~/repos/tdd-cli/.venv/bin/tdd`). Fix it (`uv tool install tdd-cli==0.6.0`) and
re-verify before `run start`; do not start a run under an editable referee.

The branch `fix/52-concurrent-advance` already exists and carries both this plan and the
harness-guidance changes for this issue (`docs/harness-integration.md` and both
`examples/skills/*/SKILL.md`). Check it out; if it has grown unrelated work, stop and
ask.

    git checkout fix/52-concurrent-advance
    tdd doctor                                      # must report healthy: true
    tdd run start --plan tasks/issue-52-concurrent-advance.md

Then repeat until done: read `next_action.verb`, do exactly what it says, run
`tdd advance`. Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit
it, and raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or
  `git commit` — the tool stages and commits, deriving the file set from the phase.
- Expected baseline for this repo: `{"tddcli": 0}` — anything else means a moved branch;
  stop.
- **Do not re-run `tdd advance` because it seems slow.** That is the bug being fixed, and
  until cycle 3 lands the tool cannot stop you. Do not pipe it through
  `tail`/`head`/`grep`; they buffer and hide the stderr heartbeats.
- Verbs this plan can hit: `run_sensitivity_check` → `tdd sensitivity begin|check|end`
  (only if a RED passes on arrival — none is expected to); `resolve_blocker` →
  `tdd blocker --kind --detail` (kinds: `plan_defect`, `tooling`, `regression`,
  `pre_existing_failure`); `confirm_cycle_applicable` on a cycle the codebase has
  outgrown → `tdd cycle skip --reason`. This plan declares no `annotation_keys`.

## Done-criteria

**Before finishing:** run
`tdd log render --out tasks/friction-logs/issue-52-concurrent-advance-friction.md` and
`tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and
every integrity event. Do not narrate what the ledger already records.

Then the documentation follow-up, committed as ordinary commits on the branch after the
run is terminal:

- PRD: a rule that a run has at most one open cycle row, and that `advance` is
  single-flight per worktree; note the schema bump to 3.
- README and `docs/harness-integration.md`: the `advance_in_flight` refusal beside the
  existing `baseline_in_progress` one.
- CHANGELOG: `Fixed` for the double-close, `Added` for the claim.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-52-concurrent-advance-friction.md
    git commit -m "docs: friction log for issue-52-concurrent-advance"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes
the branch and opens the PR against `main`. Do not push or call the GitHub API by hand.
If a gate fails, fix it and re-run the skill — a failed gate is work, not a reason to
hand back.
