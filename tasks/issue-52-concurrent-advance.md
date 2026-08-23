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
`WHERE closed_at IS NULL ORDER BY ordinal LIMIT 1` — thereafter ping-pongs between the
two chains: closing chain A's cycle N opens chain A's N+1, but chain B's N is still open
at a lower ordinal, so the next `advance` snaps back to it. Every remaining ordinal is
written, swept and closed twice, and the envelope only ever names one cycle number, so
the doubling is invisible to the agent driving the run.

Observed in a real 11-cycle run: cycles 3–11 each ran twice, roughly doubling wall
clock. The run "completed" when one chain reached the final ordinal, stranding the other
chain's last row open forever — `run.outcome = 'complete'` while `open_cycle()` still
returns a row, a state that should be impossible.

Ordering: cycles 1–2 make the ledger uncorruptible by a double close (the correctness
fix, no new state); cycles 3–6 add the claim that stops the second process from doing
the redundant work at all (the ergonomic fix). The order matters — the claim is
advisory and there is always a window between "check claim" and "commit", so
idempotency must land first and must stand on its own.

## Verified repo facts

*Every fact below was probed against this working tree during planning. Locators are
function names; grep for them at execution time.*

- **`Engine.close_cycle` (`machine.py:342`) has exactly one caller**,
  `advance._handle_refactor` (`advance.py:336`) — verified by grep over `src/` and
  `tests/`. Its blast radius is one call site.
- **The stale-snapshot trap — this is the crux of cycle 1.** `close_cycle` receives a
  `cycle_row` *snapshot* fetched at the top of `cmd_advance` (`cli.py:734`). The second
  process read that row **before** the first committed, so its snapshot says
  `AWAITING_REFACTOR` even after the row is `CLOSED` in the ledger. A guard written as
  `if cycle_row["phase"] == CLOSED` therefore does **not** fire. The guard must re-read
  `closed_at` for that row id from the ledger.
- `Engine.transition` (`machine.py:332`) performs no legality check: it inserts a
  transition row and updates the phase unconditionally. There is no existing barrier to
  a second `AWAITING_REFACTOR → CLOSED`. Ledger evidence from the observed run: cycle
  row 475 carries two such transitions, 32s apart.
- `Engine.open_cycle(ordinal)` (`machine.py:299`) always `INSERT`s. Besides
  `close_cycle` it is called by `cmd_run_start` (`cli.py:682`) and `cmd_cycle_skip`
  (`cli.py:764`) — so the duplicate-insert hole is reachable independently of the double
  close, which is why cycle 2 is its own cycle and not folded into cycle 1's GREEN.
- `Ledger.open_cycle(run_id)` (`ledger.py:319`) is
  `WHERE closed_at IS NULL ORDER BY ordinal LIMIT 1` — the selection that makes two
  chains ping-pong rather than merely coexist.
- **The claim pattern already exists and is the model for cycles 3–6.**
  `baseline_claim` (`ledger.py:37`) has `worktree_path TEXT NOT NULL UNIQUE`; the
  `INSERT` *is* the lock (`Ledger.claim`, `ledger.py:386`), and `cmd_run_start` catches
  `sqlite3.IntegrityError` and returns `failure(..., reason="baseline_in_progress")`
  (`cli.py:592`) — an `ok: false` envelope with a `reason` key and **no verb**. Follow
  this exactly: adding a verb is a specification change (`envelope.py` docstring) that
  would bump `VERB_SET_VERSION` from 2 and break every skill pinned to 2, including
  `examples/skills/tdd-drive/SKILL.md`. A refusal needs no verb.
- `Ledger.active_claim` (`ledger.py:415`) computes staleness: same host → `os.kill(pid,
  0)`, `ProcessLookupError` → stale, `PermissionError` → alive; cross-host → a 60-minute
  age fallback (`ledger.py:440`). It is documented read-only — it never deletes. Cycle 5
  reuses this rule; the `commit_refactor` extracts it so one rule serves both claim
  kinds.
- **Schema migration:** `SCHEMA_VERSION = 2` (`ledger.py:16`) and `MIGRATIONS` (`ledger.
  py:29`) is keyed by the version upgraded *from*, with `""` where the idempotent
  `SCHEMA` script suffices. A new `CREATE TABLE IF NOT EXISTS advance_claim` needs
  exactly: the table in `SCHEMA`, `SCHEMA_VERSION = 3`, and `MIGRATIONS[2] = ""` with a
  comment matching the existing v1→v2 line's style.
- **Test template, probed:** `tests/test_run_claim.py` already tests this shape for the
  baseline claim — `test_start_is_rejected_while_a_baseline_is_collecting` inserts a
  claim row by hand and asserts `out["ok"] is False` and the `reason`;
  `test_baseline_in_progress_tells_the_agent_to_poll` asserts on the *error prose*
  (`"tdd progress" in out["error"]`, `"do not re-run" in out["error"]`), which is the
  precedent authorising cycle 4's prose assertions; and there is a dead-pid reclaim test
  and a threaded `test_only_one_of_two_concurrent_starts_wins`. Copy this file's style
  throughout — do not invent a new one.
- **Engine can be constructed directly in a test**, and cycles 1–2 need this rather than
  a full run: `tests/test_baseline_integrity.py:311` does
  `Engine(ledger, cfg, repo, run_row)` after `config_mod.load(repo)` and reads rows via
  `ledger.one(...)`. Cycles 1–2 need no suite execution at all.
- `run_cli` (parsed envelope dicts) and the `repo` fixture (single project `tddcli`,
  matching this repo's own `tdd.toml`) are in `tests/conftest.py`.
- `cmd_advance` (`cli.py:731`) is four lines: `_context()`, `_engine()`,
  `ledger.open_cycle(run["id"])`, then `do_advance(...)`. The claim wraps that last
  call. The `cycle is None` early return (run complete) must **not** take a claim —
  claiming to report "all cycles complete" would leave a row behind on a finished run.
- `cmd_status` (`cli.py:698`) only reads (`active_claim` is a pure observer per its
  docstring) and takes no claim, so it stays callable while an advance is in flight.
  No cycle needed; asserted nowhere; stated here so nobody "fixes" it.
- **Precondition — the referee is currently wrong in this checkout.** `which tdd`
  resolves to `/Users/headless-coding/repos/tdd-cli/.venv/bin/tdd` — an editable install
  in a *different* checkout, not the released tool. It reports 0.6.0, which matches the
  last release, but the path violates the referee rule. Fix before `run start` (see
  Execution).

## Cycle detail

*Expected failure per cycle; minimum GREEN; resist later cycles' behaviour.*

### Cycle 1 — idempotent close

**Expected RED:** the run ends with **two** open cycle rows where the test asserts one
(and a second `AWAITING_REFACTOR → CLOSED` transition exists for the first cycle's id).

Test (no suites, no `run_cli`): start a run on `repo` so cycle 1 is open, build
`Engine(ledger, cfg, repo, run_row)`, and read `cycle_row` once — **keep that snapshot**.
Call `engine.close_cycle(cycle_row)` (opens ordinal 2), then call
`engine.close_cycle(cycle_row)` again with the same stale snapshot. Assert: exactly one
row with `closed_at IS NULL` for the run, exactly one `CLOSED` transition for the first
cycle's id, and exactly one row at ordinal 2.

GREEN: at the top of `close_cycle`, re-read `closed_at` for `cycle_row["id"]`; if it is
non-null, return `self.ledger.open_cycle(self.run["id"])` without transitioning, without
stamping `closed_at`, and without opening anything. Returning the currently-open cycle
(rather than `None`) is what lets the loser of the race reply with the run's real
position instead of a phantom "cycle N+1 opened" — the `commit: null` closes seen in the
observed run. Do not touch `_handle_refactor` yet; its reply already renders whatever
`close_cycle` returns.

### Cycle 2 — no duplicate row per ordinal

**Expected RED:** the two calls return different `id`s and two rows exist at that
ordinal.

Test: same fixture, no closing involved. Call `engine.open_cycle(2)` twice; assert the
same `id` back both times and one row at ordinal 2.

GREEN: in `open_cycle`, before inserting, `SELECT` an existing row for
`(run_id, ordinal)` with `closed_at IS NULL` and return it if present. Keep the
`declared is None → return None` guard first — it is what `cmd_cycle_skip` relies on at
the end of a plan.

### Cycle 3 — the advance claim

**Expected RED:** `out["ok"] is True` — a second advance runs today.

Test: start a run on `repo`; insert an advance claim by hand
(`led.claim_advance(str(repo), hostname=socket.gethostname(), pid=os.getpid())`);
`run_cli(repo, "advance")` → `out["ok"] is False` and
`out["result"]["reason"] == "advance_in_flight"`. Direct copy of
`test_start_is_rejected_while_a_baseline_is_collecting`.

GREEN, minimum: `advance_claim` table (`id`, `worktree_path` UNIQUE, `hostname`, `pid`,
`started_at`) in `SCHEMA`; `SCHEMA_VERSION = 3`; `MIGRATIONS[2] = ""` with a comment;
`Ledger.claim_advance` / `release_advance_claim`; in `cmd_advance`, attempt the claim
around `do_advance`, return the `failure(..., reason="advance_in_flight")` on
`sqlite3.IntegrityError`, and release on the success path. **Release on the success path
only** — the `finally` is cycle 6's GREEN and writing it here leaves cycle 6 with no RED.

### Cycle 4 — a refusal the agent can act on

**Expected RED:** assertion on the error prose / missing `result` keys — cycle 3's
refusal carries only `reason`.

Test: as cycle 3, but assert `"do not re-run" in out["error"]`, `"tdd status" in
out["error"]`, and that `result` carries `pid`, `started_at` and an integer
`elapsed_s`. Precedent: `test_baseline_in_progress_tells_the_agent_to_poll`.

GREEN: read the held claim row and populate those keys; write the prose to say an
advance is already running, how long it has been running, to wait for its envelope, and
to run `tdd status` meanwhile — and explicitly **not** to kill it and not to re-run.
State the pid as evidence of liveness only. An agent that kills a close sweep between
`git commit` and `close_cycle` causes worse corruption than the bug this issue fixes.

### Cycle 5 — reclaim a dead holder

**Expected RED:** `out["ok"] is False` — the dead claim still blocks.

Test: insert an advance claim with a pid that is not running (copy the dead-pid recipe
from `tests/test_run_claim.py`), then `run_cli(repo, "advance")` → `ok is True`.

GREEN: before returning the refusal, compute staleness for the held claim; if stale,
delete it and proceed. REFACTOR (declared `commit_refactor`): the staleness rule now
exists twice — extract the hostname/pid/60-minute computation out of
`Ledger.active_claim` into one helper used by both claim kinds. The existing
`test_run_claim.py` staleness tests (fresh cross-host, old cross-host, dead pid) are the
guard; do not weaken them.

### Cycle 6 — release on the raising path

**Expected RED:** an `advance_claim` row remains after the raise, wedging the worktree
until it goes stale.

Test: start a run; monkeypatch the advance entry point `cmd_advance` calls
(`do_advance`, i.e. `advance.advance`) to raise; call `cmd_advance` directly and let the
exception propagate (`pytest.raises`); assert no `advance_claim` row remains for the
worktree. `run_cli` is the wrong vehicle here — the exception must escape.

GREEN: move the release into a `finally`. The parallel is `cmd_run_start`'s documented
obligation at `cli.py:605` — a failed attempt that keeps its claim turns a recoverable
error into a wedged worktree.

## Deliberate scope cuts (do not build)

- **No new verb.** A refusal is `ok: false` with a `reason`, exactly like
  `baseline_in_progress`. Adding `wait_for_advance` bumps `VERB_SET_VERSION` and breaks
  every skill pinned to 2 — not worth it for a caller error. If a verb is ever wanted,
  it is its own issue with a coordinated skill release.
- **Do not make the claim block or wait.** Blocking recreates the original failure: the
  second `advance` waits, hits the harness's command timeout, is backgrounded too, and
  two queued processes sweep back to back. `named_lease` (`leases.py:109`) blocks and is
  therefore the wrong primitive here despite fitting in every other respect.
- **No repair of already-forked ledgers.** Detection is a one-line query
  (`SELECT run_id, ordinal, COUNT(*) FROM cycle GROUP BY run_id, ordinal HAVING
  COUNT(*) > 1`); automatic repair means guessing which chain's commits are real. Out of
  scope.
- **No change to `cmd_status`.** It is read-only and must stay callable while an advance
  holds the claim.
- **No change to heartbeat emission.** `heartbeat()` already writes to stderr with
  `flush=True` (`envelope.py:91`) and `machine.py:132` emits unconditionally by design.
  The observed run's silence was `tdd advance 2>&1 | tail -25` buffering — a caller
  problem, fixed in the harness docs, not in the tool.
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
**At planning time it was neither** — it resolved into another checkout's `.venv`. Fix
it (`uv tool install tdd-cli==0.6.0`) and re-verify before `run start`; do not start a
run under an editable referee.

The branch `fix/52-concurrent-advance` already exists and carries both this plan and the
harness-guidance changes for this issue (`docs/harness-integration.md` and both
`examples/skills/*/SKILL.md`, commit `edbc805`). Check it out; if it has grown unrelated
work, stop and ask.

    git checkout fix/52-concurrent-advance
    tdd doctor                                      # must report healthy: true
    tdd run start --plan tasks/issue-52-concurrent-advance.md

Then repeat until done: read `next_action.verb`, do exactly what it says, run
`tdd advance`. Stop when `next_action.terminal` is `true`.

- `tdd advance` is the only command that changes phase. Do not `git add` or
  `git commit` — the tool stages and commits, deriving the file set from the phase.
- Expected baseline for this repo: `{"tddcli": 0}` — anything else means a moved
  branch; stop.
- **Do not re-run `tdd advance` because it seems slow.** That is the bug being fixed,
  and until cycle 3 lands the tool cannot stop you. Do not pipe it through
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
- README / `docs/harness-integration.md`: the `advance_in_flight` refusal beside the
  existing `baseline_in_progress` one.
- CHANGELOG: `Fixed` entry for the double-close, `Added` for the claim.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-52-concurrent-advance-friction.md
    git commit -m "docs: friction log for issue-52-concurrent-advance"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates and
creates the PR with the repo's Keychain-scoped token.
