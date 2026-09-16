---
closes: 122
cycles:
  - n: 1
    project: tddcli
    refactor_cycle: true
    title: "extract the claim staleness rule to a module-level function in ledger.py"
    files: ["src/tddcli/ledger.py"]
    commit_refactor: "refactor: extract claim_is_stale as a module-level function"

  - n: 2
    project: tddcli
    title: "fleet claim rows report the collector's liveness and owner pid"
    test: "tests/test_fleet.py::test_fleet_claim_rows_report_collector_liveness"
    files: ["src/tddcli/fleet.py"]
    commit_red: "test: fleet claim rows carry stale and pid"
    commit_green: "feat: fleet reports baseline collector liveness"

  - n: 3
    project: tddcli
    title: "the human fleet line marks a dead collector and leaves a live one alone"
    test: "tests/test_fleet.py::test_render_marks_a_dead_collector_and_leaves_a_live_one_alone"
    files: ["src/tddcli/fleet.py"]
    commit_red: "test: the rendered fleet line names a dead collector"
    commit_green: "feat: tdd fleet names a dead baseline collector"

  - n: 4
    project: tddcli
    pin_cycle: true
    title: "pin: fleet and progress agree on a dead collector — one staleness rule, two commands"
    test: "tests/test_fleet.py::test_fleet_and_progress_agree_on_a_dead_collector"
    files: ["src/tddcli/fleet.py"]
    commit_red: "test: pin — fleet and progress agree on a dead collector"

  - n: 5
    project: tddcli
    title: "fleet lists in-flight advance claims with their holder's liveness"
    test: "tests/test_fleet.py::test_fleet_lists_advance_claims_with_holder_liveness"
    files: ["src/tddcli/fleet.py"]
    commit_red: "test: fleet --json lists advance claims"
    commit_green: "feat: fleet reports in-flight advance claims"

  - n: 6
    project: tddcli
    title: "the human fleet output prints a line per advance claim and marks a dead holder"
    test: "tests/test_fleet.py::test_render_lists_advance_claims_and_marks_a_dead_holder"
    files: ["src/tddcli/fleet.py"]
    commit_red: "test: the rendered fleet output names a dead advance holder"
    commit_green: "feat: tdd fleet renders advance claims"

  - n: 7
    project: tddcli
    title: "an advance claim alone is not 'no active runs'"
    test: "tests/test_fleet.py::test_an_advance_claim_alone_is_not_no_active_runs"
    files: ["src/tddcli/fleet.py"]
    commit_red: "test: an advance claim alone must not render 'no active runs'"
    commit_green: "fix: 'no active runs' accounts for advance claims"

  - n: 8
    project: tddcli
    refactor_cycle: true
    title: "document fleet's claim liveness and advance-claim rows"
    files:
      - "README.md"
      - "CHANGELOG.md"
    commit_refactor: "docs: fleet reports claim liveness and advance claims"
ancillary_files:
  - "README.md"
  - "CHANGELOG.md"
---

# Issue #122 — `fleet._claims` does not report claim staleness

https://github.com/geuben/tdd-cli/issues/122
Task file: `tasks/issue-122-fleet-claim-staleness.md`

## Context

Issue #115 fixed the deadlock in the polling commands: `tdd status` and `tdd progress` now emit
`confirm_cycle_applicable` with `result.stale` / `result.pid` when a `baseline_claim`'s collector
pid is dead. `src/tddcli/fleet.py::_claims` was an explicit scope cut from that plan (cut 1 in
`tasks/issue-115-stale-baseline-claim.md`), so `tdd fleet` still renders a dead collector as a
healthy one. The two commands now contradict each other, which is worse than the original silence:
`fleet` is the cross-worktree view a human reaches for precisely when an agent looks wedged.

**Probed empirically on `main` before drafting** (throwaway tests, deleted; `git status` clean).
A `baseline_claim` inserted with the pid of an exited `subprocess.Popen(["true"])`:

    ACTIVE_CLAIM:  {... 'pid': 14237, 'projects_done': 1, 'stale': True}
    FLEET_JSON:    'collecting': [{'worktree': ..., 'hostname': ..., 'projects_done': 1,
                                   'projects_total': 3, 'current_project': 'backend',
                                   'elapsed_s': 0.1}]          # no stale, no pid
    FLEET_TEXT:    '<wt>  collecting baseline 1/3 (current: backend) — 0.1s elapsed\n
                    suites executing now: 0 — 10 worker(s) each of 10 cores\n'
    PROGRESS_JSON: result {'status': 'collecting_baseline', ..., 'stale': True, 'pid': 14237}
                   next_action {'verb': 'confirm_cycle_applicable', ...}
    PROGRESS_TEXT: 'baseline collector (pid 14237) is dead — run `tdd run start --plan <path>` to recover\n'

An `advance_claim` inserted the same way is worse — it is invisible:

    ADVANCE_CLAIM: {... 'pid': 26376, 'stale': True}
    FLEET_JSON:    {'runs': [], 'collecting': [], 'suites': {...}}      # no 'advancing' key at all
    FLEET_TEXT:    'no active runs\nsuites executing now: 0 — 10 worker(s) each of 10 cores\n'

The suite is green on `main`: **536 passed**.

A scratch patch (extract `claim_is_stale`; add `stale`/`pid` to `_claims`; append a stale suffix in
`render`) was then applied and the **full suite still passed, 536 passed** — so this change has
**no test-side blast radius**: no cycle needs `modifies_tests`. Under that patch `fleet --json` and
`progress --json` reported identical `stale` and `pid` for the same claim (`True/True`,
`14581/14581`), which is why cycle 4 is a pin and not a standard cycle.

## Design decisions (locked)

1. **The staleness rule is extracted to a module-level `ledger.claim_is_stale(hostname, pid,
   started_at)`; `Ledger._claim_is_stale = staticmethod(claim_is_stale)` keeps both existing call
   sites (`active_claim`, `active_advance_claim`) working.** *User decision, 2026-09-16.* The issue
   offered either this or importing the private staticmethod. `fleet.py` is documented as read-only
   code that deliberately does not route through `Ledger`; importing a public module-level function
   honours that, importing `Ledger._claim_is_stale` would make a read-only module depend on an
   underscore-private attribute of the writer class. Verified: `src/tddcli/ledger.py` imports only
   stdlib, so `from .ledger import claim_is_stale` in `fleet.py` creates no import cycle, and the
   full suite is green under the scratch patch. The function keeps its exact body — same-host
   `os.kill(pid, 0)`, cross-host 60-minute age fallback.

2. **`stale` and `pid` go in the fleet claim row body, matching the `collecting_baseline` result
   shape from #115.** *Codebase evidence* — `src/tddcli/cli.py::_collecting_envelope` puts exactly
   these two keys in `result`, and `docs/PRD.md` §8 (`verb_set_version: 2` paragraph) documents
   `result.stale == true` as the machine-readable liveness signal. Any other spelling would make
   the two commands disagree in a new way.

3. **The human line keeps its current shape and gains a suffix: ` — collector (pid N) is dead`.**
   *User decision, 2026-09-16.* "is dead" is the phrase already used by `tdd progress`
   (`src/tddcli/cli.py`, the `f"baseline collector (pid {result['pid']}) is dead —"` branch), so
   one grep finds both. A live claim renders byte-identically to today, which is why no existing
   test changes. **The recovery command is deliberately not printed**: `fleet` is a cross-worktree
   overview and `tdd run start` must be run *in the wedged worktree*, so printing it beside another
   worktree's path would be an instruction the reader cannot follow where they are standing.

4. **`fleet` also gains in-flight `advance_claim` rows, under a new top-level `advancing` key.**
   *User decision, 2026-09-16* (the issue asks only about `_claims`; the user chose to build this
   now). Probed: a leaked advance claim is entirely invisible to `fleet`, which prints "no active
   runs" while one is held — the same class of lie this issue is about. `cmd_advance` releases the
   claim in a `finally`, so a surviving row means the holder was killed.

5. **The advance-claim line reads `{worktree}  advance in flight — {elapsed}s elapsed`, with
   ` — holder (pid N) is dead` appended when stale.** *Codebase evidence* — `advance_in_flight` is
   the existing `reason` string `cmd_advance` returns when the claim is held
   (`src/tddcli/cli.py`, the `sqlite3.IntegrityError` branch), so the human view reuses the
   vocabulary the machine view already has. "holder" rather than "collector" because an advance
   claim has no projects to collect.

6. **`fleet` remains a pure read-only observer — it never releases a stale claim of either kind.**
   *Codebase evidence* — `fleet.open_readonly` opens the database with SQLite's `mode=ro` URI and
   `tests/test_fleet.py::test_open_readonly_cannot_write` pins that a write raises
   `sqlite3.OperationalError`. Recovery stays where #115 put it: `run start` for a baseline claim,
   `cmd_advance`'s own pre-claim release for an advance claim. Do not "helpfully" add a `--prune`.

7. **The staleness rule is not re-derived in `fleet.py`.** *Follows from Decision 1.* If a cycle's
   GREEN reaches for `os.kill` or a timedelta inside `fleet.py`, the plan has been violated — that
   is the mirror this issue exists to remove. Stop and raise a blocker.

8. **Row kinds are listed even when live.** *Codebase evidence* — `_claims` already lists live
   claims and `render` already prints them; the new `advancing` rows follow the same rule. A view
   that only shows failures cannot answer "is anything happening right now?", which is what
   `tdd fleet` is for.

## Deliberate scope cuts (do not build)

- **No `plan_path` on either claim table, so no fleet line names the plan being started.**
  *Premise: blocked on work that has not landed* — the columns do not exist (`CREATE TABLE
  baseline_claim` / `advance_claim` in `src/tddcli/ledger.py`) and adding one is a ledger schema
  bump (v10 → v11) with a migration, which is a separate change from a read-only view. This
  premise was already recorded and accepted in `tasks/issue-115-stale-baseline-claim.md`.

- **No new integrity event, metric, or `tdd doctor` check for a stale claim.** *Premise: named
  non-goal* — issue #122 asks for "a staleness column/indicator to the fleet claim display" and
  nothing else; `fleet` writes nothing (Decision 6) so it structurally cannot emit an event, and
  `doctor` already has no claim check to extend. *Re-evaluation trigger:* if a probe or cycle shows
  `tdd doctor` reporting healthy while a stale claim wedges the worktree, stop and raise a blocker —
  do not absorb a doctor check into one of these cycles.

## Cycles

### Cycle 1 — refactor: extract the staleness rule to a module-level function

**Behaviour preserved; no test.** `Ledger._claim_is_stale` is a `@staticmethod` whose body moves
verbatim to a module-level `claim_is_stale(hostname, pid, started_at) -> bool` in
`src/tddcli/ledger.py`, defined above `class Ledger`. The class keeps a delegating binding:

    class Ledger:
        ...
        _claim_is_stale = staticmethod(claim_is_stale)

so `active_claim` and `active_advance_claim` (the only two call sites — verified with
`grep -n "_claim_is_stale" src/tddcli/*.py`) are untouched.

**Guarded by** the existing suite, which covers this rule in both directions:
`tests/test_run_claim.py::test_a_claim_from_a_dead_process_is_reclaimed` (same-host dead pid),
`::test_a_fresh_cross_host_claim_is_not_stale` and `::test_an_old_cross_host_claim_is_stale`
(the 60-minute fallback), plus every `stale`-asserting test in `tests/test_progress.py`. This is
**not** an unguarded refactor. Verified empirically: the extraction was applied as a scratch patch
and the full suite passed, 536 passed.

Keep the docstring with the function (same-host `os.kill(pid, 0)`; cross-host age fallback). No
signature change, no behaviour change, no new call site in this cycle — `fleet.py` is not touched
until cycle 2.

**EXPECTED FAILURE:** none — refactor cycle, no test. The guard is the green suite.

### Cycle 2 — fleet claim rows report the collector's liveness and owner pid

**Behaviour.** Each row `fleet --json` returns under `collecting` carries `stale` and `pid`, so a
machine consumer of `tdd fleet` can tell a live collector from a dead one without a second command.

**Test** (`tests/test_fleet.py::test_fleet_claim_rows_report_collector_liveness`): insert **two**
baseline claims on one ledger — one naming the pid of an exited `subprocess.Popen(["true"])` (the
idiom in `tests/test_run_claim.py::test_a_claim_from_a_dead_process_is_reclaimed`), one naming
`os.getpid()` — on two different `worktree_path` values (the column is `UNIQUE`; use `str(repo)`
and `str(repo) + "-wt2"`). Index the returned rows by `worktree` and assert, as the single
assertion, that the pair of `(stale, pid)` tuples equals `{dead_wt: (True, dead_pid),
live_wt: (False, os.getpid())}`. Both forms in one assertion: a GREEN that hardcodes `"stale": True`
fails on the live row, which is the whole point of pinning the set rather than the happy case.

**Production target.** `src/tddcli/fleet.py::_claims` — add `"pid": r["pid"]` and
`"stale": claim_is_stale(r["hostname"], r["pid"], r["started_at"])` to the dict comprehension, with
`from .ledger import claim_is_stale` at module scope. `hostname` is already selected (`SELECT *`).
**This cycle's GREEN adds the two JSON keys on the `collecting` rows and nothing earlier and
nothing later** — `render` is not touched here, `advancing` does not exist yet.

**EXPECTED FAILURE:** fails with ``AssertionError`` comparing the built mapping against the
expected one — verified empirically; the probe's `FLEET_JSON` row above has exactly the keys
`{'worktree', 'hostname', 'projects_done', 'projects_total', 'current_project', 'elapsed_s'}`, so
read the fields with `.get("stale")` / `.get("pid")` and the row values are `None`, not a `KeyError`.

### Cycle 3 — the human line marks a dead collector and leaves a live one alone

**Behaviour.** `tdd fleet`'s rendered claim line tells a human the collector is dead, and a live
claim's line is unchanged.

**Test** (`tests/test_fleet.py::test_render_marks_a_dead_collector_and_leaves_a_live_one_alone`):
call `fleet.render(summary)` directly on a hand-built summary — no ledger, no subprocess, so the
output is fully deterministic — and assert it equals the expected block, the single assertion.
Build the summary as:

    summary = {
        "runs": [],
        "advancing": [],
        "collecting": [
            {"worktree": "/wt-1", "hostname": "h", "projects_done": 1, "projects_total": 3,
             "current_project": "backend", "elapsed_s": 12.4, "pid": 4242, "stale": True},
            {"worktree": "/wt-2", "hostname": "h", "projects_done": 0, "projects_total": 2,
             "current_project": None, "elapsed_s": 3.0, "pid": 4243, "stale": False},
        ],
        "suites": {"active": 0, "total_cores": 8, "workers_each": 8},
    }

Include the `"advancing": []` key **now**, even though `render` does not read it until cycle 6 —
otherwise cycle 6 breaks this test and the executor is tempted to edit it. Expected output:

    /wt-1  collecting baseline 1/3 (current: backend) — 12.4s elapsed — collector (pid 4242) is dead
    /wt-2  collecting baseline 0/2 (current: -) — 3.0s elapsed
    suites executing now: 0 — 8 worker(s) each of 8 cores

(one trailing newline; the lines are `"\n".join(...) + "\n"`). Asserting the whole block is
deliberate: it pins that the live line did **not** change while the dead one did.

**Production target.** `src/tddcli/fleet.py::render` — the `for c in summary["collecting"]` loop.
Append ` — collector (pid {c['pid']}) is dead` when `c["stale"]`, and nothing when it is not
(Decision 3). Do not print a recovery command (Decision 3). **This cycle's GREEN adds the suffix on
the collecting line and nothing else** — no advance rows, no change to the "no active runs" line.

**EXPECTED FAILURE:** fails with ``AssertionError`` on the equality — verified empirically by
calling `fleet.render` on exactly this summary against `main`, which returned

    '/wt-1  collecting baseline 1/3 (current: backend) — 12.4s elapsed\n/wt-2  collecting baseline 0/2 (current: -) — 3.0s elapsed\nsuites executing now: 0 — 8 worker(s) each of 8 cores\n'

i.e. the expected block minus the ` — collector (pid 4242) is dead` suffix.

### Cycle 4 — pin: fleet and progress agree on a dead collector

**Behaviour.** One staleness rule (Decision 1) reaches two commands that read the ledger through
completely different paths — `fleet` over a `mode=ro` `sqlite3` connection, `progress` through
`Ledger.active_claim`. This test **passes on arrival**; it characterises that agreement before
anyone gives `fleet` its own copy of the rule, which is the mirror #115's scope cut predicted.

**Test** (`tests/test_fleet.py::test_fleet_and_progress_agree_on_a_dead_collector`): with a single
dead-pid claim on `str(repo)`, assert that the `(stale, pid)` pair from
`run_cli(repo, "fleet", "--json")["result"]["collecting"]`'s row for this worktree equals the
`(stale, pid)` pair from `run_cli(repo, "progress", "--json")["result"]` — the single assertion.
Compare **only** `stale` and `pid`: the two commands compute `elapsed_s` independently and round to
different precisions (`fleet._age_s` to 1 dp, `cli._claim_elapsed_s` to 2), so including it would
make the test flaky for no gain. Not a tautology — the two values come from two different modules
reading the database two different ways; the test detects the rule being duplicated or drifting.

**Production target.** None — this is a pin.

**EXPECTED FAILURE:** none — **pin cycle, passes on arrival.** Verified empirically: under the
scratch patch the probe printed `PARITY stale: True True` and `PARITY pid: 14581 14581`. If it
fails on arrival, that is a plan defect: `tdd annotate --key plan_defect` and stop.

### Cycle 5 — fleet lists in-flight advance claims with their holder's liveness

**Behaviour.** `fleet --json` gains a top-level `advancing` list: one row per `advance_claim`, each
carrying the holder's `pid` and computed `stale` (Decision 4).

**Test** (`tests/test_fleet.py::test_fleet_lists_advance_claims_with_holder_liveness`): insert two
advance claims via `Ledger.claim_advance` — one dead pid, one `os.getpid()`, on two worktree paths
(`advance_claim.worktree_path` is `UNIQUE` too) — then assert, as the single assertion, that
`{row["worktree"]: (row["stale"], row["pid"]) for row in out["result"].get("advancing") or []}`
equals the expected two-entry mapping. Same two-form shape as cycle 2, for the same reason.

**Production target.** `src/tddcli/fleet.py` — a new `_advance_claims(conn)` alongside `_claims`,
selecting `SELECT * FROM advance_claim ORDER BY id` and returning
`{"worktree", "hostname", "pid", "stale", "elapsed_s"}` per row (`elapsed_s` via the existing
`_age_s(r["started_at"])`, matching `_claims`), plus `"advancing": _advance_claims(conn)` in
`summarise` — **both** in `summarise`'s normal return and in its `conn is None` early return, where
it is `[]`. **This cycle's GREEN adds the `advancing` key and its row builder and nothing earlier**
— `render` still ignores it until cycle 6.

**EXPECTED FAILURE:** fails with ``AssertionError: assert {} == {...}`` — verified empirically; the
probe's `FLEET_JSON` against `main` with an advance claim held was
`{'runs': [], 'collecting': [], 'suites': {...}}`, with no `advancing` key at all, which is why the
test reads it as `out["result"].get("advancing") or []` rather than by subscript.

### Cycle 6 — the human output prints a line per advance claim and marks a dead holder

**Behaviour.** A human running `tdd fleet` sees the in-flight advance, and sees when its holder is
gone.

**Test** (`tests/test_fleet.py::test_render_lists_advance_claims_and_marks_a_dead_holder`): as in
cycle 3, call `fleet.render(summary)` on a hand-built summary — `"runs": []`, `"collecting": []`,
`"suites": {"active": 0, "total_cores": 8, "workers_each": 8}` and

    "advancing": [
        {"worktree": "/wt-1", "hostname": "h", "pid": 4242, "stale": True, "elapsed_s": 91.0},
        {"worktree": "/wt-2", "hostname": "h", "pid": 4243, "stale": False, "elapsed_s": 2.0},
    ]

and assert the rendered block equals, as the single assertion:

    /wt-1  advance in flight — 91.0s elapsed — holder (pid 4242) is dead
    /wt-2  advance in flight — 2.0s elapsed
    suites executing now: 0 — 8 worker(s) each of 8 cores

Note there is **no** leading "no active runs" line here: that is cycle 7's behaviour, and this
fixture already exercises it, so write cycle 7's test only after this one goes green — if this
block passes without cycle 7's change, the plan is wrong (see cycle 7's EXPECTED FAILURE).

**Production target.** `src/tddcli/fleet.py::render` — a `for a in summary["advancing"]` loop
placed **after** the `collecting` loop and **before** the `suites` line, emitting
`f"{a['worktree']}  advance in flight — {a['elapsed_s']}s elapsed"` plus
` — holder (pid {a['pid']}) is dead` when `a["stale"]` (Decision 5). **This cycle's GREEN adds the
advance-claim loop and nothing else** — the `if not summary["runs"] and not summary["collecting"]`
condition is left exactly as it is; cycle 7 owns it.

**EXPECTED FAILURE:** fails with ``AssertionError`` — on `main` (and after cycle 5) `render` never
reads `summary["advancing"]`, so the rendered block is `'no active runs\nsuites executing now: 0 —
8 worker(s) each of 8 cores\n'`. Verified empirically: that is exactly what `tdd fleet` printed
against a held advance claim in the probe above.

### Cycle 7 — an advance claim alone is not "no active runs"

**Behaviour.** `render` prints `no active runs` only when there is genuinely nothing in flight.
After cycle 6 a worktree holding an advance claim prints both `no active runs` **and** an
`advance in flight` line — a self-contradicting view, which is the exact defect class this issue
is about. This is the guard for the new row kind (the probe shows the state is real: `FLEET_JSON`
reported `runs: []` and `collecting: []` while an advance claim was held).

**Test** (`tests/test_fleet.py::test_an_advance_claim_alone_is_not_no_active_runs`): call
`fleet.render` on a summary with `"runs": []`, `"collecting": []`, one live `advancing` row and the
same `suites` dict, and assert `"no active runs" not in fleet.render(summary)` — the single
assertion.

**Production target.** `src/tddcli/fleet.py::render` — the trailing
`if not summary["runs"] and not summary["collecting"]:` guard gains `and not summary["advancing"]`.
**This cycle's GREEN changes that one condition and nothing else.**

**EXPECTED FAILURE:** fails with ``AssertionError: assert 'no active runs' not in 'no active
runs\n/wt-1  advance in flight — 2.0s elapsed\nsuites executing now: ...'`` — after cycle 6 the
advance line renders but the guard has not moved, so both appear. If this test **passes** on
arrival, cycle 6's GREEN overreached into this cycle's condition: run the sensitivity check the
tool offers, annotate `plan_defect`, and do not delete the test.

### Cycle 8 — refactor: document claim liveness and advance rows in the fleet view

**Behaviour preserved; no test.** Two documents describe `tdd fleet` and after cycles 1–7 both
under-describe it. The 536-test suite is the guard; these are documentation files, which have no
behaviour for the suite to guard.

Every edit, enumerated — do both:

1. `README.md`, the **"Watching every agent at once"** section (search `tdd fleet          # one
   line per active run`) — the paragraph beginning "Each run line carries the worktree, plan,
   cycle N of M". Add that a baseline-claim line names a dead collector as ` — collector (pid N) is
   dead`, that the JSON row carries `stale` and `pid` matching `tdd status` / `tdd progress`
   (#115), and that advance claims held during a `tdd advance` are listed as `advance in flight`,
   with ` — holder (pid N) is dead` when the holder was killed. Keep the existing read-only
   paragraph intact and say explicitly that `fleet` reports staleness but never clears a claim
   (Decision 6) — recovery is `tdd run start` for a baseline claim, and `tdd advance` itself for an
   advance claim.
2. `CHANGELOG.md`, `## [Unreleased]` → `### Added` — one entry naming `tdd fleet`, the new `stale`
   and `pid` fields on `collecting` rows, the new top-level `advancing` list, and issue #122 as a
   follow-up to #115. The existing #115 entry under `### Fixed` (search `without a separate
   `tdd fleet`` ) is **not** rewritten — it describes shipped behaviour accurately.

**No `README.md` command-table change is needed**: the `| `tdd fleet [--json]` |` row in the
command table already reads "all active runs across every worktree; read-only", which stays true.
`docs/PRD.md` and `docs/harness-integration.md` do not mention `tdd fleet` at all (verified:
`grep -n fleet docs/PRD.md docs/harness-integration.md` returns nothing), so neither is edited —
do not invent a PRD requirement for this.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-122-fleet-claim-staleness                  # first, before anything else
    tdd doctor                                                       # must report healthy: true
    tdd run start --plan tasks/issue-122-fleet-claim-staleness.md    # captures baselines, opens cycle 1

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. Expected summary
  line for `tddcli`: `536 passed` (0 baseline failures); anything else means the branch moved.
- The referee is the **released** tdd-cli (see the comment at the top of `tdd.toml`), not this
  working tree. The `tdd` on PATH here is the venv's *editable* install of the tree you are
  editing, so run every `tdd` command in this plan as `uvx --from tdd-cli==0.10.1 tdd <args>` (or
  `uv tool install tdd-cli==0.10.1` once and use that binary). Note the `--from` form: the package
  is `tdd-cli` but the executable is `tdd`, so `uvx tdd-cli@0.10.1` fails with "An executable named
  `tdd-cli` is not provided by package `tdd-cli`".
- Verbs this plan will hit: `write_test` / `write_implementation` / `refactor_or_advance` on cycles
  2, 3, 5, 6, 7; `write_test` then `refactor_or_advance` on the pin (cycle 4), where the tool
  expects the test to pass on arrival; `refactor_or_advance` alone on cycles 1 and 8 (refactor
  cycles, no test); `run_sensitivity_check` → `tdd sensitivity begin|check|end` if a standard
  cycle's test passes on arrival (not expected — every RED above was probed empirically);
  `create_stub` — not expected, no cycle creates a module; `annotate_cycle` — none, this plan
  declares no `annotation_keys`; `resolve_blocker` → `tdd blocker --kind --detail` with kinds
  `regression`, `plan_defect`, or `tooling`; `confirm_cycle_applicable` on a non-existent cycle →
  `tdd cycle skip --reason` (not expected: every cycle is applicable).

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-122-fleet-claim-staleness-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Ancillary docs are deliverables, not hopes. Each of these must be non-empty, or the PR body says
which cycle dropped it and why:

    git diff --stat origin/main -- README.md
    git diff --stat origin/main -- CHANGELOG.md

Also confirm `grep -n "os.kill\|timedelta" src/tddcli/fleet.py` returns **nothing**: the staleness
rule lives in `src/tddcli/ledger.py` only (Decision 7), and `git diff origin/main --
src/tddcli/cli.py` is **empty** — this plan changes no command behaviour outside `fleet`.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-122-fleet-claim-staleness-friction.md
    git commit -m "docs: friction log for issue-122-fleet-claim-staleness"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.
