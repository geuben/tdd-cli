---
closes: 97
cycles:
  - n: 1
    project: tddcli
    title: "run start refuses a plan path whose run completed, naming the delivering run, before any suite runs"
    test: "tests/test_delivered_plan.py::test_a_delivered_plan_is_refused_before_its_suite_runs"
    files: ["src/tddcli/ledger.py", "src/tddcli/cli.py"]
    modifies_tests: ["tests/test_run_abandon.py::test_abandon_refuses_a_run_that_already_ended"]
    commit_red: "test: run start refuses a plan that a completed run already delivered"
    commit_green: "feat: run start refuses a plan path whose run completed (plan_already_delivered)"
    commit_refactor: "refactor: tidy the delivered-plan lookup"
  - n: 2
    project: tddcli
    pin_cycle: true
    title: "a blocked or abandoned run does not deliver its plan"
    test: "tests/test_delivered_plan.py::test_a_blocked_or_abandoned_run_does_not_deliver_its_plan"
    files: []
    commit_pin: "test: pin that blocked and abandoned runs do not deliver a plan"
    commit_refactor: "refactor: tidy the delivered-plan tests"
  - n: 3
    project: tddcli
    pin_cycle: true
    title: "an unchanged plan is refused after its delivery"
    test: "tests/test_delivered_plan.py::test_an_unchanged_plan_is_refused_after_its_delivery"
    files: []
    commit_pin: "test: pin that an unchanged delivered plan is refused"
    commit_refactor: "refactor: tidy the unchanged-plan pin"
  - n: 4
    project: tddcli
    pin_cycle: true
    title: "a plan delivered under one ledger-service source does not refuse another source"
    test: "tests/test_ledger_service.py::test_a_plan_delivered_under_one_source_does_not_refuse_another"
    files: []
    commit_pin: "test: pin that plan delivery is per ledger-service source"
    commit_refactor: "refactor: tidy the per-source delivery pin"
  - n: 5
    project: tddcli
    refactor_cycle: true
    title: "document the plan_already_delivered refusal"
    files: ["README.md", "docs/PRD.md", "CHANGELOG.md"]
    commit_refactor: "docs: run start refuses a plan that was already delivered"
---

# Issue 97: `run start` refuses a plan that a completed run already delivered

## Context

[Issue #97](https://github.com/geuben/tdd-cli/issues/97). A second `tdd run start` against a plan
whose earlier run already completed is treated like a fresh run. The code is already there, so
every declared target passes on its first run. In the issue's case, a 15-cycle plan was started
again two hours after its real red→green run had completed in the same worktree. The re-run
recorded 15/15 `red_first_violation`, `Commits: none` on every cycle and `Outcome: complete`.
Its friction log overwrote the delivering run's log at the same path. In a 56-run audit those 15
events were 12% of all `red_first_violation` events.

`cmd_run_start` in `src/tddcli/cli.py` checks only for an active run in the worktree
(`ledger.active_run`) and for the latest registered contract of the path
(`ledger.latest_contract`). It never looks at earlier runs. `tdd plan register` reuses the
contract row for an unchanged blob (`ledger.contract_by_blob`), and registers a new row for an
edited one.

The issue offered two designs: refuse unless `--reverify` is passed, or proceed as a stamped
re-verification run. An earlier planning run asked four questions
([comment](https://github.com/geuben/tdd-cli/issues/97#issuecomment-6508600277)). The answer
([comment](https://github.com/geuben/tdd-cli/issues/97#issuecomment-6508778202)) replaced all
four options with a simpler design. `run start` refuses to run a plan **path** that any
completed run has delivered. To deliver it again, register the plan under a new path. There
are no override flags, and re-verification is out of scope. This plan builds exactly that.

## Design decisions (locked)

The answer comment was posted from the dispatch bot account
(`geuben-dispatch`). It says its decisions were "made with the maintainer, 2026-10-29" and are
final, and the labels were then swapped back to `needs-plan` as the earlier comment asked. This
plan treats it as the person's answer. Decisions marked *person* below come from it.

1. **The rule.** `run start` refuses when any run of a contract whose `plan_path` equals the
   plan being started has `outcome = 'complete'`. The check keys on the **path**, not on
   `(plan_path, git_blob_sha)`. If it keyed on the blob, a trivial plan edit would get around
   it and reproduce the 15/15 re-run. *Decided by: person.*
2. **Only `complete` delivers.** Runs that ended `blocked`, `abandoned` or `refused` (`refused`
   is the outcome for an `artifact_regenerate_failed` start) do not count. The query compares
   `run.outcome = 'complete'` and nothing wider. *Decided by: person* ("Blocked and abandoned
   runs don't count"). `refused` falls under the same rule, since only `complete` counts.
3. **Refusal shape.** `envelope.failure(...)` with `result.reason: "plan_already_delivered"`,
   `result.prior_run_id` and `result.ended_at` (that run's `ended_at`). `reason` is under
   `result`, never at the envelope's top level. No new verb (R8.3a), and no `next_action`, like
   every other `run start` refusal. The `error` message names the path, the run and its end,
   and says that delivering again means copying the plan to a new path, committing it and
   registering that path. For example:

       tasks/x.md was delivered by run 12 (ended 2026-08-28T10:02:11+00:00); a delivered plan
       is not run again. To deliver it again, copy it to a new path, commit it, and run
       `tdd plan register <new path>`.

   *Decided by: person* (`reason`, `prior_run_id`, `ended_at`, and the message's content).
   *Convention* for the envelope: `run_already_active`, `target_lint` and `baseline_implausible`
   are all `failure(..., reason=...)`. `run_already_active` names its fields the same way
   (`run_id`, `started_at`).
4. **Which run is named.** When several completed runs share the path, `prior_run_id` is the
   **earliest** (lowest `run.id`): the run that delivered the plan. A later completed run of the
   same path can only be a pre-upgrade re-run like the issue's. *Decided by: evidence* (the
   issue: the delivering run came first and the re-run two hours later). Ledgers written by
   earlier releases hold exactly this history.
5. **Where the check sits.** In `cmd_run_start`, right after the `contract_row is None`
   refusal ("is not registered") and before the R7.11 blob comparison. It therefore comes after
   `run_already_active` and the registration check, and before the dirty-tree,
   `--allow-undeclared`, `target_lint`, health-command, claim and baseline steps. Nothing runs
   and nothing is written. *Decided by: person* ("checked before the baseline claim, so no suite
   runs"). Putting it before the other refusals is *convention*: a terminal refusal comes
   first, so a harness is not sent to fix a dirty tree or a lint finding for a run that can
   never start.
6. **No override flags.** There is no `--reverify` and no `--redeliver`. Redelivery, for
   example after the delivering PR was closed unmerged, means copying or renaming the plan to a
   new path. `tdd plan register` treats a new path as a new contract. *Decided by: person.*
7. **The lookup is a new `Ledger` method, `delivered_run(plan_path)`.** It returns the earliest
   completed `run` row of any `plan_contract` with that `plan_path`, or `None`:
   `SELECT run.* FROM run JOIN plan_contract ON plan_contract.id = run.plan_contract_id WHERE
   plan_contract.plan_path = ? AND run.outcome = 'complete'` plus the source scope, then
   `ORDER BY run.id LIMIT 1`. Only `ledger.py` speaks SQL (`test_no_module_but_the_ledger_speaks_sql`).
   *Convention*: `contract_by_blob` and `latest_contract` sit beside it.
8. **It is a guest read, scoped to the ledger's source.** `delivered_run` goes into
   `GUEST_READS` and `SOURCE_ROOTED`, beside `latest_contract`. Its scope clause is
   `self._scoped("run.source")`: both tables have a `source` column, so a bare `source` is
   ambiguous. As a result, a plan delivered under one ledger-service source neither refuses
   another source's start nor shows that source its run id. *Convention*: every SOURCE_ROOTED
   method filters by the ledger's source, and `_foreign` never lets a guest learn another
   source's ids. `test_every_ledger_method_is_classified_and_scoped` forces the classification:
   with no `run_id`/`cycle_id`/`contract_id` parameter, the method must be SOURCE_ROOTED.
   **Trap:** classifying it `HOST_ONLY` passes that test, but every socket-mode `run start` then
   fails with `method_not_allowed` (`tests/test_ledger_service.py`'s guest tests catch it).
9. **No schema change.** No table or column is added, so `SCHEMA_VERSION` does not move and no
   frozen referee is needed. *Decided by: the code* (a read over existing columns).
10. **Version skew in socket mode.** A guest on this version calls `delivered_run`. A host
    ledger service on 0.15.0 refuses it with `method_not_allowed`, so every guest `run start`
    fails until the host is upgraded. The host must be upgraded together with its guests or
    before them. The CHANGELOG entry says so. *Convention*: #105's plan, decision 8, records
    the same constraint for every ledger-surface change since #169.
11. **Which ledger is searched.** The ledger is the repository's (R13.3: keyed by the common
    git dir), so every worktree of one clone shares it. Runs recorded before this release
    count, and the issue's own case (the same worktree) is caught. A separate clone of the
    repository at another path has its own ledger and is not searched. *Decided by: the code*
    (`gitutil.repo_identity`, `ledger.ledger_path`). Nothing in the issue asks for a search
    across clones.
12. **Path spelling.** The check uses the same `rel = str(Path(args.plan))` that
    `latest_contract` uses, so any spelling that finds the contract also finds its delivery
    (`./tasks/x.md` and `tasks/x.md` are the same). A spelling that does not find the contract
    is refused earlier as "not registered". The plan adds no accepted form. *Decided by: the
    code.*
13. **The one existing test this breaks.** I simulated the whole change in a scratch worktree
    and ran the full suite: exactly one test failed (721 passed, 1 failed),
    `tests/test_run_abandon.py::test_abandon_refuses_a_run_that_already_ended`. It completes run A
    with `cycle skip` and then starts run B on the same `tasks/plan.md`. Cycle 1's RED changes
    it to deliver B from a copy registered at `tasks/plan-again.md`, which is the sanctioned way
    to redeliver. The assertion (`["run_ended", "run_ended"]`) does not change. *Decided by:
    evidence.*
14. **Docs.** The `tdd run start` row of PRD §8.2's table, where the `run start` surface is
    specified, gets the refusal. The answer comment says "§8.3", but the `run start` row is in
    §8.2; §8.3 holds the loop verbs. The README gets a short subsection, and `CHANGELOG.md` a
    line under `## [Unreleased]`. *Decided by: person* (which docs), *evidence* (the section
    number), *convention* (`RELEASING.md`: the changelog is hand-edited).

## Deliberate scope cuts (do not build)

- **Re-verification**: `--reverify`, a run `kind`, a `run_reverify` table, a reverify header,
  friction-log path suffixing, a `null` red-first rate, and `kind` in `tdd status`, `tdd fleet`
  and `tdd metrics`. Premise: *user-deferred*. The answer comment says "Re-verification is out
  of scope" and that `--reverify` can be added on top of this refusal later. A renamed plan run
  against code that is already delivered is **not** a supported way to re-verify.
- **An override flag (`--redeliver` or any other).** Premise: *user-deferred* (decision 6).
- **Harnesses treating `plan_already_delivered` as terminal**: the user-level
  `implement-issue` skill (`~/.claude/skills/implement-issue/SKILL.md`, its "`run start`
  refusals" paragraph) and dispatch's retries. Premise: *unreachable*: both live outside this
  repository. The README subsection this plan adds tells harnesses to stop on the reason, and
  the plan PR asks a person to update the skill.

## Fake and real divergence

| Seam | Fake behaviour | Real behaviour | Path left untested | Ruling |
|---|---|---|---|---|
| A completed run made with `tdd cycle skip` on a one-cycle plan | ends the run `complete` with no RED/GREEN commits | a run ends `complete` when its last cycle closes (`Engine.close_cycle`) | none: both call `ledger.end_run(run_id, "complete")`, and the check reads only `outcome` | acceptable |
| A second completed run of one path, made by setting run A's `outcome` to `abandoned` with `Ledger.update`, delivering B, then setting A back to `complete` | builds the history a pre-upgrade ledger holds | two completed runs of one path exist only in ledgers written before this release | the release upgrade itself | acceptable: the ledger rows are identical |
| in-process ledger service (`ledger_service`, `split_guest`) | a thread in the test process, over a real unix socket | `tdd ledger serve` on the host, socket forwarded into the VM | the forwarding | acceptable: the same seam #169 uses, unchanged by this plan |

## Cycles

Cycles 1–3 live in a new file, `tests/test_delivered_plan.py`, at file scope. It imports
`run_cli` and `write_plan` from `conftest`, `gitutil` from `tddcli`, and `Ledger` from
`tddcli.ledger`. All of these exist, so no cycle declares a stub. It uses the `repo` fixture
(project `backend`, one passing `tests/test_smoke.py::test_smoke`). Give it the module-level
`PLAN` that `tests/test_run_abandon.py` uses: one `backend` cycle targeting
`tests/test_add.py::test_add_two_numbers`, with no `commit_*` keys. Give it two helpers:

- `ledger(repo)`: `Ledger(gitutil.repo_identity(repo))`.
- `deliver(repo, plan)`: `run_cli(repo, "run", "start", "--plan", plan)["run"]["id"]`, then
  `run_cli(repo, "cycle", "skip", "--reason", "delivered")`. Skipping the only cycle ends the
  run `complete` (`cmd_cycle_skip`). It returns the run id.

Cycle 4 lives in `tests/test_ledger_service.py`, at file scope beside the file's other guest
tests. It uses that file's existing `start_run(repo)` helper (it registers and starts
`tasks/plan.md`, `MINIMAL_PLAN`) and the already-imported `guest_config`.

### Cycle 1: `run start` refuses a delivered plan path before any suite runs

- **RED test-file edit (declared in `modifies_tests`):** in
  `tests/test_run_abandon.py::test_abandon_refuses_a_run_that_already_ended`, replace the second
  `start(repo, plan)` (the one after `cycle skip`) with three lines: `again = write_plan(repo,
  PLAN, "tasks/plan-again.md")`, `run_cli(repo, "plan", "register", again)`, and
  `start(repo, again)`. The assertion does not change. The test passes both before and after
  this cycle's GREEN (probed).
- **Test:** `test_a_delivered_plan_is_refused_before_its_suite_runs(repo, tmp_path)`. It
  reproduces the issue's history, then edits the plan:
  1. Point the suite at a counter **outside the repository** (the
     `testing-execution-counter-flake` note): `counter = tmp_path / "suite-runs"`. Rewrite
     `repo / "backend/tests/test_smoke.py"` so `test_smoke` appends `"x"` to `str(counter)`,
     with the absolute path written into the source.
  2. `plan = write_plan(repo, PLAN)`, which commits the test file and the plan. Then register
     it.
  3. `first = deliver(repo, plan)`.
  4. Simulate the pre-upgrade re-run: `ledger(repo).update("run", first, outcome="abandoned")`,
     `deliver(repo, plan)`, then `ledger(repo).update("run", first, outcome="complete")`. There
     are now two completed runs of the path, `first` and a later one.
  5. Edit the plan and re-register: `write_plan(repo, PLAN + "\nEdited after delivery.\n")`,
     then `run_cli(repo, "plan", "register", plan)`. That makes a new blob and a new contract
     (probed: `reused: False`, `contract_id: 2`).
  6. `before = counter.read_text()`, then `out = run_cli(repo, "run", "start", "--plan",
     plan)`.
  - **Single assertion:**
    `{"reason": out["result"].get("reason"), "prior_run_id": out["result"].get("prior_run_id"),
    "ended_at": out["result"].get("ended_at"), "suite_ran": counter.read_text() != before}
    == {"reason": "plan_already_delivered", "prior_run_id": first, "ended_at":
    ledger(repo).run(first)["ended_at"], "suite_ran": False}`.
  - The four keys are one behaviour, the refusal's whole contract. Each fails on its own under
    a wrong implementation, which the probe confirmed. Keying on the contract or blob instead of
    the path fails `reason`, because the edited plan is a new contract with no runs. Ordering
    newest-first fails `prior_run_id` (probed: `2 != 1`). Checking after the baseline probe
    fails `suite_ran`.
- **Target:** `src/tddcli/ledger.py`: a new `Ledger.delivered_run(plan_path)` (decisions 7, 8),
  placed after `latest_contract`, and added to `GUEST_READS` and `SOURCE_ROOTED` in
  alphabetical order. `src/tddcli/cli.py::cmd_run_start`: the check and refusal (decisions 3,
  5), right after the `if contract_row is None:` refusal.
- **EXPECTED FAILURE** (probed on main): `AssertionError` with differing items
  `{'reason': None} != {'reason': 'plan_already_delivered'}`, `{'suite_ran': True} != {'suite_ran': False}`,
  `{'prior_run_id': None} != {'prior_run_id': 1}` and `{'ended_at': None} != {'ended_at': '<timestamp>'}`.
  The third start succeeds and runs the baseline.

### Cycle 2 (pin): a blocked or abandoned run does not deliver its plan

- **Test:** `test_a_blocked_or_abandoned_run_does_not_deliver_its_plan(repo)`. Write and
  register `PLAN`. Then:
  1. `run start`, then `run_cli(repo, "run", "abandon", "--reason", "x")`.
  2. `after_abandon = run start`, then `run_cli(repo, "blocker", "--kind", "plan_defect",
     "--detail", "x")`.
  3. `after_block = run start`.
  - **Single assertion:** `[after_abandon["ok"], after_block["ok"]] == [True, True]`.
- **Target:** `Ledger.delivered_run`'s `run.outcome = 'complete'` (decision 2). No production
  change.
- **EXPECTED:** passes on arrival (probed on main and against the cycle-1 state).
- **Sensitivity mutation:** in `delivered_run`, widen `run.outcome = 'complete'` to
  `run.outcome IS NOT NULL`. Probed: `assert [False, False] == [True, True]`. Restore it.

### Cycle 3 (pin): an unchanged plan is refused after its delivery

This is the issue's literal case: the same blob, the same worktree.

- **Test:** `test_an_unchanged_plan_is_refused_after_its_delivery(repo)`. Write and register
  `PLAN`, then `deliver(repo, plan)`, then `out = run start` on the same path with no edit and
  no re-registration.
  - **Single assertion:** `out["result"].get("reason") == "plan_already_delivered"`.
- **Target:** cycle 1's check. No production change.
- **EXPECTED:** passes on arrival after cycle 1 (probed). On main it fails with
  `assert None == 'plan_already_delivered'`.
- **Sensitivity mutation:** make `delivered_run` return `None`. Restore it.

### Cycle 4 (pin): delivery is per ledger-service source

- **Test:** `tests/test_ledger_service.py::test_a_plan_delivered_under_one_source_does_not_refuse_another(repo,
  split_guest, ledger_service)`:
  1. `start_run(repo)`, then `run_cli(repo, "cycle", "skip", "--reason", "delivered")`. Source
     `vm-1` has delivered `tasks/plan.md`.
  2. `ledger_service.service.add_source("vm-2", ledger_service.dir / "vm-2.sock",
     executor=None)`.
  3. `same = run_cli(repo, "run", "start", "--plan", "tasks/plan.md")`, still on vm-1's socket.
  4. `guest_config(split_guest.runner, ledger_service.dir / "vm-2.sock")`, then
     `run_cli(repo, "plan", "register", "tasks/plan.md")`. vm-2 has no contract of its own
     until it registers one, because `latest_contract` is source-scoped.
  5. `other = run_cli(repo, "run", "start", "--plan", "tasks/plan.md")`.
  - **Single assertion:** `{"same_source": same["result"].get("reason"), "other_source":
    other["ok"]} == {"same_source": "plan_already_delivered", "other_source": True}`.
  - It also proves that a guest gets an answer to `delivered_run` through the service: if the
    method were not in `GUEST_READS`, both starts would fail with `ledger_refused`.
- **Target:** decision 8's `self._scoped("run.source")` and the `GUEST_READS` entry. No
  production change.
- **EXPECTED:** passes on arrival after cycle 1 (probed). On main it fails with
  `{'same_source': None} != {'same_source': 'plan_already_delivered'}`.
- **Sensitivity mutation:** drop the scope clause from `delivered_run`. Probed: vm-2 is then
  refused with vm-1's run id. Restore it.

### Cycle 5 (refactor, docs): document the refusal

Behaviour is unchanged, and the existing suite guards it.

- `docs/PRD.md`, §8.2, the `tdd run start --plan <path\|id>` row: after "refuses with
  `reason: "target_lint"` if findings appear", add the new refusal. If a completed run of any
  contract registered under the same plan path exists in this source's ledger, `run start`
  refuses with `reason: "plan_already_delivered"`, `prior_run_id` (the earliest such run) and
  `ended_at`, before anything is claimed or run. Blocked, abandoned and refused runs do not
  count. There is no override: to deliver the plan again, register a copy under a new path.
- `README.md`: a new `### A delivered plan is not run again` subsection, placed directly after
  the `### Abandoning a run` subsection's paragraph that begins "Refusals, under
  `result.reason`, write nothing". Cover:
  - the rule, keyed on the path so an edited plan is still refused;
  - which outcomes count;
  - the refusal's fields;
  - that it comes before any suite runs;
  - the redelivery recipe (copy the plan to a new path, commit it, `tdd plan register` the new
    path);
  - that re-verifying delivered code is not supported;
  - that a harness must treat `plan_already_delivered` as terminal, not retry it.
- `CHANGELOG.md`, under `## [Unreleased]`: add a `### Changed` entry. `tdd run start` refuses a
  plan path that a completed run already delivered, with `reason: "plan_already_delivered"`,
  `prior_run_id` and `ended_at`, before any suite runs (#97). Re-running a delivered plan used
  to record a fresh run whose every cycle was a `red_first_violation`. To redeliver, register
  the plan under a new path. Blocked and abandoned runs do not count. With a ledger service,
  upgrade the host with or before its guests: a 0.15.0 host refuses the new `delivered_run`
  read with `method_not_allowed`.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-97-delivered-plan-refusal   # first, before anything else
    tdd doctor                                        # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-97-delivered-plan-refusal.md   # captures baselines, opens cycle 1

`tdd doctor` checks every project; `tdd run start` probes only the ones the plan declares and
those downstream of them through an `[artifact]`. A failing check on a project outside that set
does not stop the run: note it and go on. Any other failing check stops it.

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

**Referee.** Use the released `tdd` on `PATH`, never `uv run tdd` from this tree (the note at
the top of `tdd.toml`). This plan changes no ledger table, so `SCHEMA_VERSION` does not move
and no frozen referee is needed. The released referee does not yet refuse delivered plans,
and this plan's own path has never been delivered, so `run start` is not affected.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is
  green at the plan's base (verified in a fresh worktree: `722 passed`). Expect
  `baselines: {tddcli: 0}` and no standing failures.
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`: pin cycles 2, 3 and 4 (each
    cycle names its mutation), and any standard cycle that pre-passes.
  - `create_stub`: no cycle declares a stub (every RED imports only existing symbols), so any
    request means an undeclared import.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|environment> --detail '...'`.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.
  - This plan declares no annotation keys, so `annotate_cycle` should not appear.
- Cycle 1's GREEN builds the whole lookup as decisions 2, 4, 5, 7 and 8 give it:
  `outcome = 'complete'` only, the earliest run, scoped by `run.source`, classified in
  `GUEST_READS` and `SOURCE_ROOTED`. Cycles 2–4 are pins over it, so if a pin fails on
  arrival, cycle 1's GREEN departed from those decisions. Fix the GREEN, never the pin.
- If any test outside `modifies_tests` breaks in cycle 1's GREEN, a test is starting a second
  run of a delivered path that the scratch-worktree simulation did not find. Raise
  `plan_defect` naming it. Do not relax the refusal.
- Cycle 5 is docs only. If it turns out to need a code change, raise `plan_defect`. Never
  commit a semantic change under a refactor phase.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-97-delivered-plan-refusal-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-97-delivered-plan-refusal-friction.md
    git commit -m "docs: friction log for issue-97-delivered-plan-refusal"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #97`. It also says that the user-level `implement-issue` skill and
dispatch's retries should treat `plan_already_delivered` as terminal. That change is outside
this repository and must be made by a person.

Docs are deliverables, not hopes. Cycle 5 owns them:

- `git diff --stat origin/main -- docs/PRD.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- README.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.

What a user sees is one new JSON refusal from `run start`, and no screen changes, so no demo
recording is required.
