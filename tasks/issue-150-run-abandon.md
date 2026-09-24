---
closes: 150
cycles:
  - n: 1
    project: tddcli
    title: "tdd run abandon ends the worktree's live run as abandoned"
    test: "tests/test_run_abandon.py::test_abandon_ends_the_live_run_as_abandoned"
    stub_expected: ["src/tddcli/cli.py"]
    files: ["src/tddcli/cli.py"]
    commit_red: "test: tdd run abandon ends the live run"
    commit_green: "feat: tdd run abandon ends the worktree's live run as abandoned"
    commit_refactor: "refactor: tidy tdd run abandon"
  - n: 2
    project: tddcli
    title: "metrics reports an abandoned run's reason and who abandoned it"
    test: "tests/test_run_abandon.py::test_metrics_reports_the_reason_and_who_abandoned_the_run"
    files: ["src/tddcli/ledger.py", "src/tddcli/cli.py", "src/tddcli/render.py"]
    commit_red: "test: metrics reports why and by whom a run was abandoned"
    commit_green: "feat: record the abandonment and report it in tdd metrics"
    commit_refactor: "refactor: tidy the abandonment record"
  - n: 3
    project: tddcli
    title: "abandoning records a human intervention"
    test: "tests/test_run_abandon.py::test_abandoning_records_a_human_intervention"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: abandoning a run is a human intervention"
    commit_green: "feat: abandoning a run records a human intervention"
    commit_refactor: "refactor: tidy the abandon intervention"
  - n: 4
    project: tddcli
    pin_cycle: true
    title: "fleet stops listing an abandoned run"
    test: "tests/test_run_abandon.py::test_fleet_stops_listing_an_abandoned_run"
    files: []
    commit_pin: "test: pin that fleet stops listing an abandoned run"
  - n: 5
    project: tddcli
    title: "--run abandons a run whose worktree is gone"
    test: "tests/test_run_abandon.py::test_abandon_by_id_ends_a_run_whose_worktree_is_gone"
    stub_expected: ["src/tddcli/cli.py"]
    files: ["src/tddcli/cli.py"]
    commit_red: "test: tdd run abandon --run ends a run whose worktree is gone"
    commit_green: "feat: tdd run abandon --run <id>"
    commit_refactor: "refactor: tidy abandon-by-id"
  - n: 6
    project: tddcli
    pin_cycle: true
    title: "a new run for the same plan starts in a fresh worktree at the same path"
    test: "tests/test_run_abandon.py::test_a_new_run_starts_in_a_fresh_worktree_after_abandon"
    files: []
    commit_pin: "test: pin that a new run can start after an abandon"
  - n: 7
    project: tddcli
    title: "live and blocked runs are abandonable from their worktree, by id when it is gone, and by id from their own worktree"
    test: "tests/test_run_abandon.py::test_abandon_accepts_live_and_blocked_runs_in_every_accepted_form"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: abandon accepts blocked runs and every accepted form"
    commit_green: "feat: tdd run abandon accepts blocked runs"
    commit_refactor: "refactor: tidy abandon run lookup"
  - n: 8
    project: tddcli
    title: "a blank reason is refused"
    test: "tests/test_run_abandon.py::test_abandon_refuses_a_blank_reason"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: abandon refuses a blank reason"
    commit_green: "feat: abandon refuses a blank reason"
    commit_refactor: "refactor: tidy the reason check"
  - n: 9
    project: tddcli
    title: "no live or blocked run in the worktree is refused as no_run"
    test: "tests/test_run_abandon.py::test_abandon_without_a_live_or_blocked_run_is_refused"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: abandon with nothing to abandon is refused"
    commit_green: "feat: abandon reports no_run"
    commit_refactor: "refactor: tidy no_run"
  - n: 10
    project: tddcli
    title: "an unknown --run id is refused as run_not_found"
    test: "tests/test_run_abandon.py::test_abandon_refuses_an_unknown_run_id"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: abandon refuses an unknown run id"
    commit_green: "feat: abandon reports run_not_found"
    commit_refactor: "refactor: tidy run_not_found"
  - n: 11
    project: tddcli
    title: "--run on a complete or abandoned run is refused as run_ended"
    test: "tests/test_run_abandon.py::test_abandon_refuses_a_run_that_already_ended"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: abandon refuses a run that already ended"
    commit_green: "feat: abandon reports run_ended"
    commit_refactor: "refactor: tidy run_ended"
  - n: 12
    project: tddcli
    title: "--run on another worktree that still exists is refused as worktree_exists"
    test: "tests/test_run_abandon.py::test_abandon_by_id_refuses_a_run_whose_worktree_still_exists"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: abandon by id refuses a run whose worktree still exists"
    commit_green: "feat: abandon reports worktree_exists"
    commit_refactor: "refactor: tidy worktree_exists"
  - n: 13
    project: tddcli
    title: "abandoning releases the run worktree's stale claims"
    test: "tests/test_run_abandon.py::test_abandoning_releases_the_worktrees_claims"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: abandoning releases the worktree's claims"
    commit_green: "feat: abandoning releases the worktree's claims"
    commit_refactor: "refactor: tidy claim release"
  - n: 14
    project: tddcli
    title: "an advance in flight is refused as advance_in_flight"
    test: "tests/test_run_abandon.py::test_abandon_refuses_while_an_advance_is_in_flight"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: abandon refuses while an advance is in flight"
    commit_green: "feat: abandon reports advance_in_flight"
    commit_refactor: "refactor: tidy advance_in_flight"
  - n: 15
    project: tddcli
    title: "on a split runner the account is the calling agent (SUDO_USER)"
    test: "tests/test_run_abandon.py::test_a_split_runner_records_the_calling_agent_as_the_account"
    files: ["src/tddcli/cli.py", "README.md", "docs/PRD.md", "CHANGELOG.md"]
    commit_red: "test: a split runner records the calling agent as the abandoning account"
    commit_green: "feat: a split runner records SUDO_USER as the abandoning account"
    commit_refactor: "docs: tdd run abandon in the README, PRD and changelog"
---

# Issue 150 — `tdd run abandon`: end a run that will not be finished

## Context

Issue #150. The ledger's `run.outcome` column documents `complete | blocked | abandoned`, but
nothing writes `abandoned`. geuben/dispatch#24's run (44 cycles, stopped on purpose at cycle 1 so
#145's suite speedups could land first) had its worktree and branch removed, and the ledger
still holds it as unfinished. `tdd fleet` keeps listing it, nothing records that it was stopped
on purpose, and a new run cannot start at the same worktree path, because `run start` refuses
with `run_already_active` (verified by probe, see cycle 6).

The ask: `tdd run abandon --reason "<text>"` for the current worktree's run, and a way to
abandon a run by id when its worktree is gone. It sets `outcome = abandoned`, records the
reason and who did it, and releases any claim. `fleet` stops listing it. `metrics` reports it
as abandoned, separately from blocked. Like `resume --unblock`, it is a human intervention.

**Done when** (from the issue): an abandoned run is out of `fleet`, `metrics` reports it as
abandoned, and a new run can start in a fresh worktree for the same plan. All three are tested
(cycles 4, 2 and 6).

## Design decisions (locked)

1. **Command shape.** `tdd run abandon --reason <text> [--run <id>]`, a new subparser under
   `run` beside `start` (`build_parser`, the `run_p` subparsers), with handler
   `cmd_run_abandon` in `src/tddcli/cli.py`. `--reason` is `required=True`. `--run` is
   `type=int`, so argparse refuses a non-integer id itself. The help text says
   `human only`, as the PRD does for `resume --unblock`. *Decided by: the issue plus repo
   convention.*

2. **Which runs can be abandoned: live or blocked.** A blocked run that will never be
   unblocked was also stopped on purpose, and metrics should say so. Complete, refused and
   already-abandoned runs are refused with `run_ended`. *Decided by: user.*

3. **Finding the run.**
   - Without `--run`: the worktree's live run (`Ledger.active_run(str(worktree))`), else its
     most recent blocked run (the same query `cmd_resume` uses for `--unblock`:
     `worktree_path = ? AND outcome = 'blocked' ORDER BY id DESC LIMIT 1`). Neither is
     refused with `no_run`.
   - With `--run <id>`: `SELECT * FROM run WHERE id = ?`. None → `run_not_found`. `ended_at`
     set and `outcome != 'blocked'` → `run_ended`.
   - `--run` is allowed only when the run's worktree is gone (`not Path(run["worktree_path"]).exists()`)
     or is the caller's own (`run["worktree_path"] == str(worktree)`). Otherwise it is refused
     with `worktree_exists`, so one agent cannot end another agent's live run by id. That
     matters in split mode, where every agent reaches the same runner. *Decided by: user.*
   - The handler does **not** use `_context()`. That raises `SystemExit` with a reason-less
     failure when there is no live run, and it loads `tdd.toml`, which abandon does not need.
     Use `_worktree()` and `Ledger(gitutil.repo_identity(worktree))` directly, as `cmd_resume`
     does.

4. **Guard order**, first match wins. Each guard is `failure(<message>, reason=<code>)`, and the
   code lands under `result.reason`, never at the envelope's top level:
   1. `reason_required`: `args.reason.strip()` is empty (checked before any ledger lookup);
   2. `run_not_found` / `run_ended` / `worktree_exists` for `--run`, in that order, or
      `no_run` without it;
   3. `advance_in_flight`: `ledger.active_advance_claim(run["worktree_path"])` exists and is
      not `stale`. Kill the holder first. A stale claim is released, not obeyed.

5. **What abandoning writes.** Refused calls write nothing. A successful call does four things:
   - `ledger.update("run", id, ended_at=now(), outcome="abandoned")`. For a blocked run this
     overwrites the block time with the abandon time.
   - one row in a **new `abandonment` table**: `id INTEGER PRIMARY KEY, run_id INTEGER NOT
     NULL UNIQUE REFERENCES run(id), reason TEXT NOT NULL, account TEXT NOT NULL,
     executor_model TEXT NOT NULL, executor_source TEXT NOT NULL, at TEXT NOT NULL`, added
     to `SCHEMA` in `src/tddcli/ledger.py`.
   - one `human_intervention` row, `note = f"abandoned: {reason}"`, so the friction log's
     intervention list and `metrics.human_interventions` count it and say what it was.
   - `ledger.release_claim(wt)` and `ledger.release_advance_claim(wt)` for the run's
     `worktree_path`.

   The envelope is `ok: true` with `next_action` verb `complete` and a detail naming the run
   id. `complete` is already terminal. A new verb would bump `VERB_SET_VERSION`, which every
   driving skill checks, and the caller here is a human. *Decided by: planner, from
   `envelope.Verb`.*

6. **No `SCHEMA_VERSION` bump.** `SCHEMA` is an idempotent `CREATE TABLE IF NOT EXISTS`
   script that `Ledger.__init__` runs on every open (`self.db.executescript(SCHEMA)`), so
   every existing ledger gets the table the first time a new tool opens it. The version gate
   exists to stop an older tool from misreading a shape it does not know. An older tool never
   reads `abandonment`, and it sees `outcome = 'abandoned'`, a value the PRD already documents.
   So the referee is the **released `tdd` on `PATH`**, as in #147, and no frozen snapshot is
   needed. `MIGRATIONS` is untouched. *Decided by: planner, from the migration code. This
   supersedes the v13 bump floated to the user during planning. The user's referee choice
   ("released tool on PATH") holds either way.*

7. **Who: account plus session identity.** Both are recorded:
   - `account`: `os.environ["SUDO_USER"]` when this process is the split-mode runner
     (`runner.load()` returns a config with `role == "runner"`), because sudo sets it and
     the caller cannot forge it. Otherwise `pwd.getpwuid(os.geteuid()).pw_name`.
     **Footgun:** do not use `getpass.getuser()`. It trusts `LOGNAME`/`USER` from the
     environment, and the tests compare against `conftest.current_user()`, which is the
     effective uid.
   - `executor_model` / `executor_source`: `identity.resolve(worktree)`, the same resolution
     `run start` uses (operator or claimed on a split runner). It shows whether a Claude
     session or a bare shell abandoned the run.

   *Decided by: user.*

8. **Metrics.** Each `render.metrics` run entry for an abandoned run gains `"abandoned":
   {"reason": ..., "by": {"account": ..., "executor": ..., "executor_source": ...}}`, read
   from the `abandonment` row. `outcome` already carries `"abandoned"`, separately from
   `"blocked"`. Metrics stays scoped to the caller's worktree path (`worktree_path = ?`), so
   a run whose worktree is gone shows up in `tdd metrics` only when it is run from a worktree
   at that same path. That is today's behaviour for every run, and the issue does not ask to
   change it.

9. **Fleet needs no change.** `fleet._runs` already filters `r.ended_at IS NULL`, and its
   claim lists read `baseline_claim` / `advance_claim`, which decision 5 clears. Cycle 4 pins
   the first. Cycle 13's test asserts the second through `fleet --json`.

10. **The open cycle stays open**, as it does for a blocked run. `render._time_summary`
    already handles an ended run whose last cycle is open.

## Deliberate scope cuts (do not build)

- **Cross-worktree metrics** (reporting a run from a worktree at a different path). *Premise:
  a named non-goal.* The issue asks that metrics report the run as abandoned, which cycle 2
  covers under metrics' existing per-worktree scope. Widening that scope changes every run's
  report and was not asked for.

No other cuts. Everything the issue asks for is built.

## Cycles

All tests go in the new file `tests/test_run_abandon.py`, at module scope, driven in-process
through `conftest.run_cli`. Shared helpers at the top of the file:

```python
import os, socket, subprocess
from conftest import current_user, git, run_cli, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger

PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding"
    test: "tests/test_add.py::test_add_two_numbers"
---
# Plan
"""

def ledger(repo):
    return Ledger(gitutil.repo_identity(repo))

def start(path, plan):
    out = run_cli(path, "run", "start", "--plan", plan)
    assert out["ok"], out
    return out

def outcome(repo, run_id):
    return ledger(repo).one("SELECT outcome FROM run WHERE id = ?", (run_id,))["outcome"]
```

Register the plan once per test in `repo` (`plan = write_plan(repo, PLAN)` then
`run_cli(repo, "plan", "register", plan)`). `write_plan` commits, so a worktree added afterwards
carries the plan. Add a worktree with `git(repo, "worktree", "add", "-q", "--detach",
str(tmp_path / "wt-a"))` and remove it with `git(repo, "worktree", "remove", "--force", str(wt))`.
Probe-verified: `run start` inside such a worktree succeeds, and the stored `worktree_path`
equals `str(wt)` under pytest's resolved `tmp_path`. The run id is
`ledger(repo).one("SELECT id FROM run ORDER BY id DESC LIMIT 1")["id"]`.

Today `run_cli(repo, "run", "abandon", "--reason", "x")` returns empty stdout (argparse exit 2),
so without cycle 1's stub every test dies in `json.JSONDecodeError`. **That is why cycle 1
declares `src/tddcli/cli.py` in `stub_expected`.**

### Cycle 1: abandon ends the live run

- **Behaviour:** in a worktree with a live run, `tdd run abandon --reason <text>` sets that
  run's `outcome = 'abandoned'` and `ended_at`.
- **Test:** `test_abandon_ends_the_live_run_as_abandoned`. `start(repo, plan)`, then
  `run_cli(repo, "run", "abandon", "--reason", "superseded by #145")`. Assert
  `(row["outcome"], row["ended_at"] is not None) == ("abandoned", True)` for the single run
  row.
- **Stub (RED):** add the `abandon` subparser (`--reason` required, `--run` **not yet**) and a
  `cmd_run_abandon` that returns `failure("not implemented", reason="not_implemented")`.
- **Production target:** `cli.cmd_run_abandon`: find the live run via `ledger.active_run` and
  update it.
- **EXPECTED FAILURE:** `AssertionError: assert (None, False) == ('abandoned', True)`.

### Cycle 2: metrics reports the reason and who

- **Behaviour:** after an abandon, the run's `tdd metrics` entry carries `abandoned: {reason,
  by: {account, executor, executor_source}}`, read from a new `abandonment` row.
- **Test:** `test_metrics_reports_the_reason_and_who_abandoned_the_run`. Start, abandon with
  `--reason "superseded by #145"`, then `entry = run_cli(repo, "metrics")["result"]["runs"][0]`.
  Assert `entry.get("abandoned") == {"reason": "superseded by #145", "by": {"account":
  current_user(), "executor": "pytest-executor", "executor_source": "declared"}}`. The
  executor values come from conftest's autouse `TDD_EXECUTOR_MODEL=pytest-executor`, which
  `identity` records as `declared`. They are derived independently of the code under test.
- **Production target:** `ledger.SCHEMA` (the `abandonment` table, decision 5),
  `cli.cmd_run_abandon` (insert the row: account via `pwd`, executor via `identity.resolve`),
  `render.metrics` (the `abandoned` key).
- **EXPECTED FAILURE:** `AssertionError: assert None == {'reason': 'superseded by #145', ...}`.

### Cycle 3: abandoning is a human intervention

- **Behaviour:** abandoning inserts one `human_intervention` row with note
  `"abandoned: <reason>"`.
- **Test:** `test_abandoning_records_a_human_intervention`. Start, abandon with
  `--reason "superseded by #145"`. Assert
  `[r["note"] for r in ledger(repo).all("SELECT note FROM human_intervention")] ==
  ["abandoned: superseded by #145"]`.
- **Production target:** `cli.cmd_run_abandon`.
- **EXPECTED FAILURE:** `AssertionError: assert [] == ['abandoned: superseded by #145']`.

### Cycle 4 (pin): fleet stops listing an abandoned run

- **Behaviour:** `fleet` lists only runs with `ended_at IS NULL`. Cycle 1 sets it, so an
  abandoned run drops out.
- **Test:** `test_fleet_stops_listing_an_abandoned_run`. Start, abandon, and assert
  `run_cli(repo, "fleet", "--json")["result"]["runs"] == []`.
- **Kind: pin.** Probe: with the run's `ended_at` set, `fleet` returned no runs, and before
  that it listed the run even after its worktree was removed. It passes on arrival once cycle 1
  is in. No production change.
- **Sensitivity:** remove the `r.ended_at IS NULL` filter in `fleet._runs` and the test fails
  with the run listed.

### Cycle 5: `--run` abandons a run whose worktree is gone

- **Behaviour:** `tdd run abandon --run <id> --reason <text>`, run from the main checkout,
  ends a run whose worktree has been removed.
- **Test:** `test_abandon_by_id_ends_a_run_whose_worktree_is_gone`. Register in `repo`, add
  worktree `wt-a`, `start(wt, plan)`, read the run id, remove `wt-a`, then `run_cli(repo, "run",
  "abandon", "--run", str(run_id), "--reason", "worktree removed; superseded by #145")`. Assert
  `outcome(repo, run_id) == "abandoned"`.
- **Stub (RED):** add `--run` (`type=int`, default `None`) to the `abandon` subparser. It is not
  read yet.
- **Production target:** `cli.cmd_run_abandon`: when `args.run` is set, look the run up by id.
- **EXPECTED FAILURE:** `AssertionError: assert None == 'abandoned'`. Without `--run` handling,
  the handler looks in `repo`, finds no live run and writes nothing.

### Cycle 6 (pin): a new run starts at the same path after abandon

- **Behaviour:** after `--run` abandons a gone worktree's run, re-creating a worktree at the
  same path and running `run start` for the same plan succeeds.
- **Test:** `test_a_new_run_starts_in_a_fresh_worktree_after_abandon`. Take cycle 5's setup
  through the abandon, then `git worktree add` at the **same** path `wt-a`, and assert
  `run_cli(wt, "run", "start", "--plan", plan)["ok"] is True`.
- **Kind: pin.** Probe: before the abandon, the restart is refused with
  `result.reason == "run_already_active"`. With the old run's `ended_at`/`outcome` set, it
  succeeds. After cycle 5 it passes on arrival. No production change.
- **Sensitivity:** make `cmd_run_abandon` skip the `ended_at` write and the restart is refused
  with `run_already_active`.

### Cycle 7: every accepted form

- **Behaviour:** the accepted set from decisions 2 and 3: (a) a blocked run in the caller's
  worktree, without `--run`; (b) a blocked run by `--run` when its worktree is gone; (c) a live
  run by `--run` from its own worktree.
- **Test:** `test_abandon_accepts_live_and_blocked_runs_in_every_accepted_form`. One test with
  three scenarios in sequence, and no `parametrize`, so the declared id stays a bare function
  name. Collect the three outcomes and assert
  `[a, b, c] == ["abandoned", "abandoned", "abandoned"]`.
  - (a) `start(repo, plan)`; `run_cli(repo, "blocker", "--kind", "tooling", "--detail", "d")`;
    `run_cli(repo, "run", "abandon", "--reason", "blocked for good")`.
  - (b) worktree `wt-b`: start; `blocker` there; remove `wt-b`; from `repo`:
    `--run <id> --reason "blocked and removed"`.
  - (c) worktree `wt-c`: start; from **`wt-c`**: `--run <id> --reason "own worktree"`.
- **Production target:** `cli.cmd_run_abandon`: without `--run`, fall back to the most recent
  blocked run.
- **EXPECTED FAILURE:** `AssertionError: assert ['blocked', <b>, 'abandoned'] == [...]`. (a)
  fails because cycle 1 finds only live runs. (b) depends on whether cycle 5's by-id lookup
  checked anything (minimal GREEN did not, so it may already be `abandoned`). (c) already
  passes. At least (a) fails.

### Cycle 8: a blank reason is refused

- **Test:** `test_abandon_refuses_a_blank_reason`. `start(repo, plan)`, then abandon with
  `--reason "   "`. Assert `(out["result"].get("reason"), outcome(repo, run_id)) ==
  ("reason_required", None)`.
- **Production target:** `cli.cmd_run_abandon`, the first guard (decision 4).
- **EXPECTED FAILURE:** `AssertionError: assert (None, 'abandoned') == ('reason_required', None)`.

### Cycle 9: no live or blocked run → `no_run`

- **Test:** `test_abandon_without_a_live_or_blocked_run_is_refused`. `start(repo, plan)`, then
  `run_cli(repo, "cycle", "skip", "--reason", "r")` (probe-verified: the single-cycle plan's
  run becomes `complete`). Then abandon without `--run`. Assert
  `out["result"].get("reason") == "no_run"`.
- **Production target:** `cli.cmd_run_abandon`.
- **EXPECTED FAILURE:** `AssertionError: assert None == 'no_run'`. The earlier cycles fail
  without a reason code.

### Cycle 10: unknown id → `run_not_found`

- **Test:** `test_abandon_refuses_an_unknown_run_id`. Register only (no run), then
  `run_cli(repo, "run", "abandon", "--run", "999", "--reason", "x")`. Assert
  `out["result"].get("reason") == "run_not_found"`.
- **Production target:** `cli.cmd_run_abandon`.
- **EXPECTED FAILURE:** `AssertionError: assert None == 'run_not_found'`. If the executor let a
  `None` row reach a subscript, the failure is instead `TypeError: 'NoneType' object is not
  subscriptable`, which tdd records as a failure, and GREEN is the same.

### Cycle 11: ended run → `run_ended`

- **Test:** `test_abandon_refuses_a_run_that_already_ended`. In `repo`: run A (`start` then
  `cycle skip`, so A is `complete`), then run B (`start`, then abandon without `--run`, so B is
  `abandoned`). Then abandon `--run A` and `--run B` from `repo`. Assert
  `[a["result"].get("reason"), b["result"].get("reason")] == ["run_ended", "run_ended"]`.
- **Production target:** `cli.cmd_run_abandon`: `ended_at` set and `outcome != 'blocked'`.
  Cycle 7(b) is what keeps a blocked run accepted.
- **EXPECTED FAILURE:** `AssertionError: assert [None, None] == ['run_ended', 'run_ended']`.

### Cycle 12: another worktree still exists → `worktree_exists`

- **Test:** `test_abandon_by_id_refuses_a_run_whose_worktree_still_exists`. Worktree `wt-d`:
  `start`. Leave it in place, and from `repo` run `--run <id> --reason "x"`. Assert
  `(out["result"].get("reason"), outcome(repo, run_id)) == ("worktree_exists", None)`.
- **Production target:** `cli.cmd_run_abandon`: refuse when `Path(wt).exists()` and
  `wt != str(worktree)`. Cycle 7(c) keeps the own-worktree exemption honest.
- **EXPECTED FAILURE:** `AssertionError: assert (None, 'abandoned') == ('worktree_exists', None)`.

### Cycle 13: stale claims are released

- **Test:** `test_abandoning_releases_the_worktrees_claims`. `start(repo, plan)`. Set
  `wt = str(gitutil.worktree_root(repo))`. Get a dead pid:
  `p = subprocess.Popen(["true"]); p.wait()` (probe-verified: `claim_is_stale(host, p.pid, now)`
  is `True`). Then `L = ledger(repo)`, `L.claim(wt, socket.gethostname(), p.pid, 1)` and
  `L.claim_advance(wt, socket.gethostname(), p.pid)`. Abandon. Then
  `f = run_cli(repo, "fleet", "--json")["result"]` and assert
  `(f["collecting"], f["advancing"]) == ([], [])`.
- **Production target:** `cli.cmd_run_abandon`: `release_claim` and `release_advance_claim`
  for the run's `worktree_path`.
- **EXPECTED FAILURE:** `AssertionError`, with one stale entry left in each list.

### Cycle 14: live advance → `advance_in_flight`

- **Test:** `test_abandon_refuses_while_an_advance_is_in_flight`. `start(repo, plan)`, then
  `ledger(repo).claim_advance(wt, socket.gethostname(), os.getpid())`. Probe-verified: the
  test's own pid is not stale. Abandon. Assert
  `(out["result"].get("reason"), outcome(repo, run_id)) == ("advance_in_flight", None)`.
- **Production target:** `cli.cmd_run_abandon`: the last guard (decision 4). It must come
  **before** cycle 13's release, which would otherwise delete the live claim.
- **EXPECTED FAILURE:** `AssertionError: assert (None, 'abandoned') == ('advance_in_flight', None)`.

### Cycle 15: split runner records the calling agent

- **Test:** `test_a_split_runner_records_the_calling_agent_as_the_account`. Use the
  `split_runner` fixture plus `monkeypatch.setenv("SUDO_USER", "agent-7")`. Probe-verified:
  the sudo shim ignores `-u`, and `run start` succeeds with executor source `claimed`. Register,
  start, and abandon in `repo`. Assert
  `run_cli(repo, "metrics")["result"]["runs"][0]["abandoned"]["by"]["account"] == "agent-7"`.
- **Production target:** `cli.cmd_run_abandon`'s account resolution (decision 7).
- **EXPECTED FAILURE:** `AssertionError: assert '<current user>' == 'agent-7'`.
- **REFACTOR phase: the docs.** This phase carries the documentation, and the Done-criteria
  check for each file:
  - `README.md`: a row in the command table, `| tdd run abandon --reason <text> [--run <id>] |
    end a run that will not be finished; human only |`, beside the `tdd resume` row, plus
    a short paragraph near the `resume --unblock` recovery text. The paragraph says what
    abandon writes, the `--run` worktree rule, and the refusal codes.
  - `docs/PRD.md`: a row in the human-command table beside `tdd resume --unblock --note
    <text>`, marked **human only**.
  - `CHANGELOG.md`: an `### Added` entry under `## [Unreleased]`.

## Behaviour census

| Promise | Test |
|---|---|
| sets outcome abandoned (cwd) | cycle 1 |
| records reason and who; metrics reports it | cycle 2 |
| it is a human intervention | cycle 3 |
| fleet stops listing it | cycle 4 |
| by id when the worktree is gone | cycle 5 |
| new run can start in a fresh worktree | cycle 6 |
| blocked runs, own-worktree `--run` | cycle 7 |
| releases any claim | cycle 13 |
| guards: blank reason, no run, unknown id, ended, other live worktree, advance in flight | cycles 8–12, 14 |
| who = SUDO_USER on a runner | cycle 15 |

No fakes: the ledger is real SQLite and the worktrees are real `git worktree`s. There are no
mirrors, no generated artifacts and no invariant registry. Test blast radius: none. No existing
test reads a table list or asserts on an unknown `run` subcommand, and the full suite in a
fresh worktree is 641 passed at the plan's base.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-150-run-abandon            # first, before anything else
    tdd doctor                                       # must report healthy: true
    tdd run start --plan tasks/issue-150-run-abandon.md

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

**Referee.** Use the released `tdd` on `PATH` (`tdd --version`), never an editable install of
this working tree. `SCHEMA_VERSION` does not change in this plan (decision 6).

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is
  green at the plan's base in a fresh worktree (641 passed, 2026-09-24); expect
  `baselines: {tddcli: 0}`.
- Verbs this plan will hit:
  - `create_stub`, `write_test`, `write_implementation`, `refactor_or_advance`;
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`. Cycles 4 and 6 are pins and
    will ask for it.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|regression|bad_red|tooling>
    --detail '...'`;
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.

  This plan declares no annotation keys beyond the reserved `plan_defect` and
  `friction_note`.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- cycle 1: the handler finds `active_run` and sets `ended_at`/`outcome`. No guards, no
  `abandonment` row, no intervention, no `--run`.
- cycle 2: the `abandonment` table in `SCHEMA`, its insert (account via `pwd`, **not**
  `SUDO_USER`), and the metrics key.
- cycle 3: the `human_intervention` insert.
- cycle 4: a pin. Write the test and change no production code.
- cycle 5: read `args.run` and look the run up by id. No checks on what the id names.
- cycle 6: a pin. Write the test and change no production code.
- cycle 7: the blocked-run fallback without `--run`. Still no refusal codes.
- cycle 8: `reason_required` only.
- cycle 9: `no_run` only.
- cycle 10: `run_not_found` only.
- cycle 11: `run_ended` only.
- cycle 12: `worktree_exists` only.
- cycle 13: the two claim releases.
- cycle 14: `advance_in_flight`, placed before the releases.
- cycle 15: `SUDO_USER` on a split runner. Its refactor phase carries the docs.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-150-run-abandon-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-150-run-abandon-friction.md
    git commit -m "docs: friction log for issue-150-run-abandon"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #150`.

Docs are deliverables. Each of these must be non-empty (cycle 15), or the PR body says which
cycle dropped it and why:
- `git diff --stat origin/main -- README.md`
- `git diff --stat origin/main -- docs/PRD.md`
- `git diff --stat origin/main -- CHANGELOG.md`

This is a new CLI verb with a JSON envelope. Nothing visual changes, so no demo recording is
required.
