---
closes: 115
cycles:
  - n: 1
    project: tddcli
    title: "status on a stale baseline claim replies confirm_cycle_applicable, not await_baseline"
    test: "tests/test_progress.py::test_status_on_a_stale_claim_does_not_tell_the_agent_to_wait"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: status on a dead baseline collector must not reply await_baseline"
    commit_green: "fix: a stale baseline claim replies confirm_cycle_applicable"

  - n: 2
    project: tddcli
    title: "the collecting_baseline result body reports the claim's liveness and owner pid"
    test: "tests/test_progress.py::test_collecting_baseline_result_reports_claim_liveness"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: collecting_baseline body carries stale and pid"
    commit_green: "feat: surface stale and pid in the collecting_baseline result"

  - n: 3
    project: tddcli
    pin_cycle: true
    title: "progress --json and status agree on a stale claim — one seam, two commands"
    test: "tests/test_progress.py::test_progress_json_and_status_agree_on_a_stale_claim"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: pin — progress --json shares status's stale-claim reply"

  - n: 4
    project: tddcli
    title: "bare progress names the dead collector and the command that clears it"
    test: "tests/test_progress.py::test_bare_progress_names_the_dead_collector_and_the_recovery_command"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: bare progress names the dead collector"
    commit_green: "feat: bare progress reports a dead baseline collector"

  - n: 5
    project: tddcli
    refactor_cycle: true
    title: "document the stale-claim reply across every verb table that claims await_baseline is unconditional"
    files:
      - "docs/harness-integration.md"
      - "docs/PRD.md"
      - "README.md"
      - "CHANGELOG.md"
      - "examples/skills/tdd-drive/SKILL.md"
    commit_refactor: "docs: a dead baseline collector no longer replies await_baseline"
ancillary_files:
  - "docs/harness-integration.md"
  - "docs/PRD.md"
  - "README.md"
  - "CHANGELOG.md"
  - "examples/skills/tdd-drive/SKILL.md"
---

# Issue #115 — a dead baseline collector bricks the worktree

https://github.com/geuben/tdd-cli/issues/115
Task file: `tasks/issue-115-stale-baseline-claim.md`

## Context

`Ledger.active_claim` (`src/tddcli/ledger.py`) computes `claim["stale"]` correctly: same host,
`os.kill(pid, 0)` raises `ProcessLookupError`, so a `SIGKILL`ed `run start` leaves a claim whose
`stale` is `True`. `cli._collecting_envelope` — the single seam shared by `cmd_status` and
`cmd_progress` — then drops that flag on the floor and emits `Verb.AWAIT_BASELINE`
unconditionally, whose `detail` is "poll `tdd progress` again".

`await_baseline` is non-terminal, so a well-behaved autonomous executor polls forever. The only
command that clears the claim is `run start` (`cmd_run_start` does `release_claim` + reclaim when
`existing["stale"]`), and both `docs/harness-integration.md` and `examples/skills/tdd-drive/SKILL.md`
tell the agent never to re-run it. Following the tool's own instructions is what keeps the agent
stuck. No run row is created, so the failure does not appear in `tdd metrics` at all.

**Probed empirically on `main` before drafting** (throwaway test, deleted; tree confirmed clean).
A claim inserted with the pid of an exited `subprocess.Popen(["true"])`:

    CLAIM:         {... 'pid': 28852, 'projects_done': 0, 'stale': True}
    STATUS:        result {'status': 'collecting_baseline', 'projects_done': 0,
                           'projects_total': 1, 'current_project': None, 'elapsed_s': 0.08}
                   next_action {'verb': 'await_baseline', 'terminal': False}
    PROGRESS_JSON: identical envelope
    PROGRESS_TEXT: 'collecting baseline: 0/1 projects — 0.22s elapsed\n'

The bug reproduces exactly as the issue describes. The suite is green on `main`: **491 passed**.

A scratch patch of `_collecting_envelope` (branch on `claim["stale"]`, add `stale`/`pid` to the
body) was then applied and the **full suite still passed, 491 passed** — so this change has **no
test-side blast radius**: no cycle needs `modifies_tests`. Under that patch `progress --json`
flipped for free (shared seam) while the bare-text branch in `cmd_progress` did **not** — which is
why cycle 3 is a pin and cycle 4 is standard.

## Design decisions (locked)

1. **A stale claim replies `Verb.CONFIRM_CYCLE_APPLICABLE`; the verb set is unchanged**
   (`verb_set_version` stays `2`). *User decision, 2026-09-09.* `cmd_status` already emits this
   verb for the "no active run" case, and `docs/harness-integration.md` documents it as "a
   judgement point outside the cycle loop: config scaffolded, no active run, doctor passed →
   review / register / **start** as the `detail` names". A claim whose owner is dead is
   semantically "no run here, start one". The rejected alternative was a new `restart_run` verb:
   R8.3a makes adding a verb a specification change, bumping `VERB_SET_VERSION` to 3, which
   harness consumers are documented to treat as drift they must stop on. Do **not** add a verb.

2. **Observers stay pure — `cmd_status` and `cmd_progress` never delete the claim row.**
   *Issue #115, "Suggested fix", and the `active_claim` docstring's append-only contract.* The
   fix is in what the envelope *says*. `run start` remains the only command that releases and
   reclaims. Do not "helpfully" call `release_claim` from an observer.

3. **`stale` and `pid` go in the `collecting_baseline` result body, not only in `detail`.**
   *Issue #115.* `detail` is explicitly non-authoritative (R8.3a); a consumer that wants to
   distinguish a live collector from a dead one needs a machine-readable field.

4. **Cross-host claims need no new rule.** `Ledger._claim_is_stale` already falls back to a
   60-minute age check when `hostname` differs, and `tests/test_run_claim.py` pins both
   directions (`test_a_fresh_cross_host_claim_is_not_stale`,
   `test_an_old_cross_host_claim_is_stale`). Reading `claim["stale"]` inherits that rule for
   free. *Codebase evidence.*

5. **Scope is the issue's core fix only.** *User decision, 2026-09-09.* See the two cuts below.

## Deliberate scope cuts (do not build)

- **`tdd fleet` does not gain a staleness column.** *Premise:* the issue names `fleet`'s "suites
  executing now: 0" vs "collecting baseline" contradiction as the symptom a *human* spotted, not
  as the deadlock itself; the deadlock is fixed once the polling commands tell the truth.
  `fleet._claims` (`src/tddcli/fleet.py`) is a **mirror** of the claim rendering in
  `_collecting_envelope` and after this plan the two diverge: `status` reports liveness, `fleet`
  does not. Nothing enforces their agreement — `fleet` opens the ledger `mode=ro` and does not go
  through `Ledger`, so it cannot drift-detect. **Raise a follow-up issue** naming
  `src/tddcli/fleet.py::_claims` and `Ledger._claim_is_stale` (a `@staticmethod`, importable from
  read-only code) before closing this one. *Re-evaluation trigger:* if any cycle's probe shows
  that `fleet` is what an executor is actually told to consult when a claim looks wedged, stop and
  raise a blocker — do not absorb the fleet change into an in-scope cycle.

- **`cmd_run_start`'s `baseline_in_progress` refusal text is left as written.** *Premise:*
  `cmd_run_start` releases and reclaims a stale claim *before* attempting the insert, so
  `baseline_in_progress` is only ever raised against a **live** claim — where "do not re-run
  `run start` — poll `tdd progress` instead" is correct advice. Verified in
  `src/tddcli/cli.py::cmd_run_start` (the `existing["stale"]` branch precedes `ledger.claim`) and
  pinned by `tests/test_run_claim.py::test_a_claim_from_a_dead_process_is_reclaimed`. Changing it
  would mean editing `test_baseline_in_progress_tells_the_agent_to_poll` for no behavioural gain.
  *Re-evaluation trigger:* if cycle 1's probe shows `run start` reaching the
  `sqlite3.IntegrityError` branch with a **stale** claim in the ledger, that premise is false —
  stop and raise a blocker rather than editing the refusal text inside a cycle.

- **No `plan_path` column on `baseline_claim`.** *Premise:* the claim row does not record which
  plan was being started (schema at `src/tddcli/ledger.py`, `CREATE TABLE baseline_claim`), so the
  recovery `detail` must say `tdd run start --plan <path>` generically. Adding the column is a
  ledger schema bump (v9 → v10) for a cosmetic improvement to one string.

## Cycles

### Cycle 1 — `status` on a stale claim does not tell the agent to wait

**Behaviour.** When `cmd_status` finds a `baseline_claim` whose owner process is gone, the reply
must be a verb the executor can discharge, not `await_baseline`.

**Test** (`tests/test_progress.py::test_status_on_a_stale_claim_does_not_tell_the_agent_to_wait`):
insert a claim naming the pid of an exited `subprocess.Popen(["true"])` (the idiom already used by
`tests/test_run_claim.py::test_a_claim_from_a_dead_process_is_reclaimed`), then assert
`run_cli(repo, "status")["next_action"]["verb"] == "confirm_cycle_applicable"` — the single
assertion.

**Production target.** `src/tddcli/cli.py::_collecting_envelope` — branch on `claim["stale"]`
(already computed by `Ledger.active_claim`, no ledger change) and return
`NextAction(Verb.CONFIRM_CYCLE_APPLICABLE, ...)` whose `detail` names the dead pid and
`tdd run start --plan <path>`. Do not release the claim (Decision 2). Do not add a verb
(Decision 1).

**EXPECTED FAILURE:** fails with ``AssertionError: assert 'await_baseline' ==
'confirm_cycle_applicable'`` — verified empirically; the probe's `STATUS` envelope above is the
exact pre-fix output.

### Cycle 2 — the result body reports the claim's liveness and owner pid

**Behaviour.** The `collecting_baseline` result carries machine-readable `stale` and `pid`, so a
consumer never has to parse `detail` (R8.3a) to tell a live collector from a dead one.

**Test** (`tests/test_progress.py::test_collecting_baseline_result_reports_claim_liveness`): with
the same dead-pid claim, assert `run_cli(repo, "status")["result"]` reports
`{"stale": True, "pid": <the dead pid>}`. These are one fact — *who held the claim and whether
they are alive* — deliberately not split: splitting adds a third consecutive standard cycle on
`cli.py` for no design value (skill rule 7), and a `stale` flag with no owner pid is not
actionable evidence.

**Production target.** `src/tddcli/cli.py::_collecting_envelope` — add both keys to the `result`
dict on **both** branches, so a live claim reports `stale: False` too. Use
`.get("stale")` / `.get("pid")` in the test so a missing key fails on an assertion, not a
`KeyError`.

**EXPECTED FAILURE:** fails with ``AssertionError`` on the missing keys — the probe's pre-fix
`result` body is exactly `{'status', 'projects_done', 'projects_total', 'current_project',
'elapsed_s'}`, with no `stale` and no `pid`. Cycle 1's minimal GREEN reads `claim["stale"]` for
the branch only and does not put it in the body.

### Cycle 3 — pin: `progress --json` and `status` agree

**Behaviour.** `cmd_progress`'s JSON path routes through the same `_collecting_envelope` seam as
`cmd_status`, so the fix reaches the command the wedged executor was actually polling. This test
**passes on arrival** — it characterises the shared seam before anyone "helpfully" gives
`cmd_progress` its own copy of the envelope.

**Test** (`tests/test_progress.py::test_progress_json_and_status_agree_on_a_stale_claim`): with a
dead-pid claim, assert `run_cli(repo, "progress", "--json")["next_action"]["verb"] ==
run_cli(repo, "status")["next_action"]["verb"]`. Both sides are read from the tool, but they are
**two different commands**, so this is not a tautology: it detects the seam being duplicated.

**Production target.** None — `src/tddcli/cli.py::cmd_progress` already delegates to
`_collecting_envelope` (line-free anchor: the `if claim is not None: envelope =
_collecting_envelope(claim)` branch inside `cmd_progress`).

**EXPECTED FAILURE:** none — **pin cycle, passes on arrival.** Verified empirically: under the
scratch patch the probe's `PROGRESS_JSON` envelope was byte-identical to `STATUS` apart from
`elapsed_s`. If it fails on arrival, that is a plan defect: `tdd annotate --key plan_defect` and
stop.

### Cycle 4 — bare `progress` names the dead collector and the command that clears it

**Behaviour.** The human-readable `tdd progress` line currently reads `collecting baseline: 0/1
projects — 970s elapsed`, which is a lie for a dead collector and is what a human has to read to
notice the wedge. It must say the collector is not running.

**Test** (`tests/test_progress.py::test_bare_progress_names_the_dead_collector_and_the_recovery_command`):
with a dead-pid claim, assert `"not running" in run_cli_text(repo, "progress")` — the single
assertion. (Assert on the phrase, not on the pid digits: `run_cli_text` returns the rendered line
and the pid is incidental.)

**Production target.** `src/tddcli/cli.py::cmd_progress` — the non-`--json` branch that writes
`f"collecting baseline: {...} projects{current} — {...}s elapsed\n"`. Append a stale suffix driven
by `envelope.result["stale"]` (added in cycle 2), naming the pid and `tdd run start`.

**EXPECTED FAILURE:** fails with ``AssertionError: assert 'not running' in 'collecting baseline:
0/1 projects — 0.22s elapsed\n'`` — verified empirically; the probe's `PROGRESS_TEXT` above is the
exact pre-fix output, and it was **unchanged** by the scratch patch to `_collecting_envelope`, so
this cycle has real work to do.

### Cycle 5 — refactor: document the stale-claim reply

**Behaviour preserved; no test.** Four documents currently assert, in prose, that
`await_baseline` is the unconditional reply while a claim is open and that the agent must *never*
re-run `run start`. After cycles 1–4 that is true only of a **live** claim, and a doc that
contradicts the tool is how this bug survived. The 491-test suite is the guard: no production
behaviour changes here. (This is not an unguarded refactor of production code — the files are
documentation, which has no behaviour for the suite to guard.)

Every edit, enumerated — do all five:

1. `docs/harness-integration.md`, verb table row `| await_baseline |` — qualify "**never** re-run
   `tdd run start`" as applying to a live collector, and say that a dead one replies
   `confirm_cycle_applicable` with `result.stale: true`.
2. `docs/harness-integration.md`, verb table row `| confirm_cycle_applicable |` — add "a dead
   baseline collector" to the list of judgement points ("config scaffolded, no active run, doctor
   passed").
3. `docs/harness-integration.md`, "Concurrent-command refusals" → the **`baseline_in_progress`**
   paragraph — note that a *stale* claim is reclaimed by `run start` and that `status`/`progress`
   now say so, so "Never re-run `run start`" applies while the holder is alive.
4. `docs/PRD.md`, the **`verb_set_version: 2`** paragraph in §8 (search `added `await_baseline`
   (issue #2)`) — record that `await_baseline` is emitted only while the claim's owner is live,
   and that a stale claim replies `confirm_cycle_applicable`; state explicitly that
   `verb_set_version` is **unchanged** (Decision 1).
5. `README.md`, the numbered "3. **Poll.**" item under the baseline-timeout guidance (search
   `next_action.verb ==`) — same qualification.
6. `examples/skills/tdd-drive/SKILL.md`, the `- **await_baseline**` bullet (search
   `Never re-run`) — same qualification. This file is a **mirror** of the harness verb table;
   leaving it stale reproduces the exact failure mode the issue describes, in the document the
   executor actually reads.
7. `CHANGELOG.md`, `## [Unreleased]` → `### Fixed` — one entry for the deadlock, naming
   `status`/`progress`, the `confirm_cycle_applicable` reply, and the new `stale`/`pid` result
   fields.

**No `verb_set_version` bump and no `VERB_SET_VERSION` edit in `src/tddcli/envelope.py`.**
`tests/test_contract.py::test_await_baseline_is_a_non_terminal_verb` asserts
`verb_set_version == 2`; if you find yourself wanting to change that test, Decision 1 has been
violated — stop and raise a blocker.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-115-stale-baseline-claim              # first, before anything else
    tdd doctor                                                  # must report healthy: true
    tdd run start --plan tasks/issue-115-stale-baseline-claim.md   # captures baselines, opens cycle 1

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. Expected summary
  line for `tddcli`: `491 passed` (0 baseline failures); anything else means the branch moved.
- The referee is the **released** tdd-cli (see the comment at the top of `tdd.toml`), not this
  working tree. The `tdd` on PATH here is the venv's *editable* install of the tree you are
  editing, so run every `tdd` command in this plan as `uvx --from tdd-cli==0.10.1 tdd <args>` (or
  `uv tool install tdd-cli==0.10.1` once and use that binary). Note the `--from` form: the
  package is `tdd-cli` but the executable is `tdd`, so `uvx tdd-cli@0.10.1` fails with
  "An executable named `tdd-cli` is not provided by package `tdd-cli`" — verified at plan time.
- Verbs this plan will hit: `write_test` / `write_implementation` / `refactor_or_advance` on
  cycles 1, 2, 4; `write_test` then `refactor_or_advance` on the pin (cycle 3), where the tool
  expects the test to pass on arrival; `refactor_or_advance` alone on cycle 5 (refactor cycle, no
  test); `run_sensitivity_check` → `tdd sensitivity begin|check|end` if a standard cycle's test
  passes on arrival (not expected — every RED above was probed empirically); `create_stub` — not
  expected, no cycle creates a module; `annotate_cycle` — none, this plan declares no
  `annotation_keys`; `resolve_blocker` → `tdd blocker --kind --detail` with kinds `regression`,
  `plan_defect`, or `tooling`; `confirm_cycle_applicable` on a non-existent cycle →
  `tdd cycle skip --reason` (not expected: every cycle is applicable).

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-115-stale-baseline-claim-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Ancillary docs are deliverables, not hopes. Each of these must be non-empty, or the PR body says
which cycle dropped it and why:

    git diff --stat origin/main -- docs/harness-integration.md
    git diff --stat origin/main -- docs/PRD.md
    git diff --stat origin/main -- README.md
    git diff --stat origin/main -- CHANGELOG.md
    git diff --stat origin/main -- examples/skills/tdd-drive/SKILL.md

Also confirm `git diff origin/main -- src/tddcli/envelope.py` is **empty**: no verb was added and
`VERB_SET_VERSION` is still 2 (Decision 1).

Raise the follow-up issue named in the first scope cut (`fleet._claims` does not report claim
staleness) and reference it in the PR body.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-115-stale-baseline-claim-friction.md
    git commit -m "docs: friction log for issue-115-stale-baseline-claim"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.
