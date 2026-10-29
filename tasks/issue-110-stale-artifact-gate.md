---
closes: 110
cycles:
  - n: 1
    project: tddcli
    title: "an unresolved stale artifact at cycle close replies fix_regression naming it"
    test: "tests/test_artifact_regeneration.py::test_unresolved_stale_artifact_at_close_replies_fix_regression"
    files: ["src/tddcli/machine.py", "src/tddcli/advance.py", "docs/PRD.md", "docs/harness-integration.md"]
    commit_red: "test: an unresolved stale artifact blocks the cycle close"
    commit_green: "fix: an unresolved stale artifact is a close-sweep failure (R9.12)"
    commit_refactor: "refactor: tidy the stale-artifact close gate"
  - n: 2
    project: tddcli
    pin_cycle: true
    title: "a stale artifact whose regenerate hook commits nothing gets the same reply"
    test: "tests/test_artifact_regeneration.py::test_stale_artifact_whose_hook_commits_nothing_replies_fix_regression"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: pin — a hook that commits nothing leaves the artifact stale"
    commit_refactor: "refactor: tidy the unresolved-stale branch"
  - n: 3
    project: tddcli
    pin_cycle: true
    title: "once the artifact is fresh again, the next advance closes the cycle"
    test: "tests/test_artifact_regeneration.py::test_cycle_closes_once_the_stale_artifact_is_fresh_again"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: pin — a freshened artifact lets the cycle close"
    commit_refactor: "refactor: tidy the close path after the artifact gate"
  - n: 4
    project: tddcli
    title: "run start refuses on an unresolved stale artifact and ends the run refused"
    test: "tests/test_artifact_regeneration.py::test_unresolved_stale_artifact_at_run_start_refuses"
    files: ["src/tddcli/cli.py", "docs/PRD.md", "CHANGELOG.md"]
    modifies_tests:
      - "tests/test_artifact_regeneration.py::test_unresolved_stale_artifact_still_emits_event"
      - "tests/test_artifact_regeneration.py::test_failed_regenerate_after_stale_check_reports_hook_failure_not_stale"
    commit_red: "test: run start refuses on an unresolved stale artifact"
    commit_green: "fix: run start refuses when a declared artifact is stale and unresolved"
    commit_refactor: "refactor: tidy the run-start artifact refusals"
---

# Issue 110: an unresolved `stale_artifact` blocks the close

https://github.com/geuben/tdd-cli/issues/110
Task file: `tasks/issue-110-stale-artifact-gate.md`
Predecessor: #107 (`tasks/issue-107-regenerate-hook-failure.md`), which cut this gate out of
its scope and gave `check_artifacts` the structured `ArtifactOutcome` this plan extends.
**Blocked by #99** (`tasks/issue-99-inherited-artifacts-unreadable-baseline.md`, plan merged):
implement this plan only after #99 has landed on `main` (decision 10).

## Context

PRD R9.12 says that when the tool cannot resolve staleness itself (no `regenerate` command, or
the regenerate hook produced no commit) it "emits `stale_artifact` and **blocks the close**",
and §12 lists "A cycle cannot close with a stale declared artifact" among the hard gates. The
code only records the event. `Engine.check_artifacts` (`src/tddcli/machine.py`) writes
`stale_artifact` in its `if not resolved:` branch and returns. `advance.py::_handle_refactor`
then runs the close sweep and closes the cycle. `cli.py::cmd_run_start` records the run-level
event and opens cycle 1. Nothing reads the event back as a gate, so an artifact declared with
only a `check` can be stale for a whole run that reports itself delivered.

The issue asks for the gate (or a PRD change, which nobody wants: see decision 1):

- at cycle close, an unresolved stale artifact is a close-sweep failure, replied as
  `fix_regression` naming the artifact, in the shape #107 adopted for a failed hook, and the
  cycle stays open until the check passes or the hook produces a commit;
- at `run start`, the command refuses, as #107 does for a failed hook;
- the benign auto-regenerated path (#56) stays exactly as it is.

Probed on `main` at 37accb5 in a fresh scratch `git worktree` (it needed no setup; this repo
has no `.claude/worktree-setup.sh`). The suite there: `722 passed`. Each probe below was a
throwaway test file, now deleted with the worktree:

| Case (artifact `spec`, path `backend/spec.json`) | Today |
|---|---|
| `check = "test ! -f <marker>"`, marker created after `run start`, then `advance` | `complete`, `result.stale_artifacts` absent |
| same `check` plus `regenerate = "true"` (exits 0, changes nothing) | `complete` |
| `check = "false"` at `run start` | `ok: true`, cycle 1 open, `status` shows the live run |

A sketch of the whole change (the field, the close reply, the run-start refusal) gave
`720 passed, 2 failed` in that worktree. Both failures came from the run-start refusal and are
this plan's `modifies_tests` (cycle 4). With the close gate alone, the suite stayed green. The
issue's earlier planning comment
(https://github.com/geuben/tdd-cli/issues/110#issuecomment-6506417445) reported the same
numbers on b487ce1. The sketch was deleted.

#99's plan was merged while this one was being written, and is not implemented yet. It
rewrites the same branch of `check_artifacts`, so this plan runs after it (decision 10). The
probes above ran before #99. Its code cannot change their outcome, because every artifact in
this plan is produced by the plan's own project (decision 9). #99's tests are new, so this
sketch could not run them. Decision 10 records what reading them shows.

## Design decisions (locked)

1. **The gate is real. The code changes and the PRD keeps its meaning.** *Evidence:* R9.12
   ("blocks the close … one of the few hard gates (§12)") and §12 ("A cycle cannot close with a
   stale declared artifact"). The issue's alternative, making the event advisory, would rewrite
   the spec to match a bug. §12 and the IntegrityEvent list do not change. R9.12 gains two
   clarifying sentences (cycles 1 and 4).
2. **`ArtifactOutcome` gains `stale: list[str]`**, the names of the artifacts for which this
   check wrote a `stale_artifact` event. `check_artifacts` appends `art.name` at the
   `self.ledger.event(..., "stale_artifact", art.name)` call in its `if not resolved:` branch,
   and **only there**. The event stays. That branch covers both unresolved forms: no hook, or a
   hook that exited 0 and staged nothing, so `commit_generated` returned no sha. After #99 that
   branch also has an `artifact_stale_inherited` arm, for `run start` with an artifact outside
   the run's reachable set. That arm does **not** add to `stale`. #99's
   `test_run_start_reports_outside_stale_artifacts_once_as_inherited` already guards this: its
   `run start` must succeed with two inherited stale artifacts. *Evidence:* the issue's scope note
   names `ArtifactOutcome` as the place, and #107's decision 5 made it the outcome type. #99's
   plan ("Interactions with other open plans") says the #110 gate "gates only what still emits
   `stale_artifact`, the in-scope and touched artifacts".
   *Mechanism note:* the field has no default. `ArtifactOutcome` is built in exactly one
   place, the `return` at the end of `check_artifacts`, with keyword arguments
   (`grep -rn "ArtifactOutcome(" src/ tests/` → that line only), so pass
   `stale=...` there.
3. **The close reply is `fix_regression` with `result.stale_artifacts: [names]` and
   `commit=sha`, issued before `engine.sweep` and before `close_cycle`.** In
   `_handle_refactor` it goes directly after the existing `artifact_outcome.failed` reply, so a
   failed hook still wins when both happen (the #107 precedence). The cycle stays open and the
   downstream suites are not run against a stale contract. *Convention:* #107's decision 1
   (the issue asks for "the same shape #107 adopts"). The key is `stale_artifacts`, not
   `artifact_failures`, because those entries carry `code`/`stderr` and a stale artifact has
   neither. It is a list of names, like `result.regenerated`. Result keys here are snake_case
   plural nouns for what they list (`failures`, `gates`, `missing_annotations`,
   `artifact_failures`). Detail text (not asserted): ``"Declared artifact(s) stale and not
   regenerated: <names>. Rebuild and commit them, or fix the regenerate hook, until the check
   passes, then re-run `tdd advance`."``
4. **No new blocker kind.** *Convention:* #107's decision 1. An executor that cannot make the
   artifact fresh files an existing kind: `regression` if the run made it stale, `tooling` if
   the producer cannot run on this machine. `BLOCKER_KINDS` in `cli.py` is not touched.
5. **`run start` refuses with `reason="stale_artifact"` and `result.stale_artifacts`, and ends
   the run `refused`.** In `cmd_run_start`, directly after the existing
   `artifact_outcome.failed` refusal (so a failed hook still gets its own reason), when
   `artifact_outcome.stale` is non-empty, call `ledger.end_run(run_id, "refused")` and return
   `failure(<message naming the artifacts>, reason="stale_artifact",
   stale_artifacts=artifact_outcome.stale)`. The existing `finally: ledger.release_claim(...)`
   covers the early return. The run-level `stale_artifact` event and `artifact_check` rows stay
   on the refused run. *Evidence:* the issue's Expected ("refuse (as #107 does for a failed
   hook)") and R9.12 ("Before a run starts … checked for staleness"). *Convention:* #107's
   decision 2 (`end_run(..., "refused")`, rows kept), and a refusal's `reason` is the event
   kind, as `artifact_regenerate_failed` is. The reason lives under `result.reason`
   (`envelope.failure(error, **result)`). Message (not asserted beyond naming the artifact):
   ``f"artifact(s) stale and not regenerated: {names}. A stale contract gives a green wrong
   answer; rebuild and commit the artifact (or fix its regenerate hook) so its check passes,
   then retry."``
6. **The benign path does not change.** A hook that produces a commit is resolution, and no
   `stale_artifact` is emitted (#56). The tool does not re-run `check` after a hook commit:
   R9.12 counts the commit as resolution. Existing tests guard both:
   `test_regeneration_commits_the_artifacts_own_path`, `test_resolved_stale_artifact_emits_no_event`,
   `test_successful_regeneration_marks_artifact_check_regenerated` and
   `test_friction_log_reports_regenerated_artifacts_benignly`. *Evidence:* the issue ("Keep the
   benign auto-regenerated path exactly as it is") and R9.12.
7. **`regenerated.append(art.name)` for a hook that committed nothing is left as it is.** Today
   that is a false `result.regenerated: ["spec"]` on `complete`. Once the gate exists, that case
   replies `fix_regression`, which carries no `regenerated`. `run start` never reports it. So
   the false report can no longer be seen, and no test could drive a change. *Evidence:* the
   reply paths in `_handle_refactor` and `cmd_run_start`. A minimal GREEN does not touch it.
8. **No ledger change.** No table or column changes, there is no new ledger method, and
   `SCHEMA_VERSION` stays where it is, so no frozen referee is needed. *Evidence:*
   `artifact_check.stale` and the `stale_artifact` event already record everything; the gate
   reads the in-memory outcome.
9. **Test fixtures.** *Evidence:* the probes. Every test declares `[artifact.spec]` with
   `path = "backend/spec.json"` (the file need not exist) and `produced_by = "backend"`. Close
   tests use `check = "test ! -f <tmp_path>/stale"`: it passes at `run start`, and the test
   creates the marker before `advance`. The marker is outside the repo, so it changes no tree
   hash and fires no `undeclared_file_touched`. The run-start test uses `check = "false"`. The
   plan is the file's existing `PLAN` (one refactor cycle on `backend`), which opens straight
   into `AWAITING_REFACTOR`, so the first `advance` reaches `check_artifacts`. `spec`'s
   producer, `backend`, is the plan's own project, so under #99's scoping `spec` is in scope at
   `run start` and at every close. The fixtures mean the same before and after #99.
10. **This plan lands after #99.** #99's merged plan scopes artifact checks to the run's
    reachable projects and turns inherited staleness into `artifact_stale_inherited`. Its
    cycle 2 and 3 tests declare an out-of-scope `check = "false"` artifact and need `run start`
    to succeed. If this gate landed first, those `run start` calls would be refused before #99's
    cycle 3 could exempt them, and #99's run could not proceed. Landed in the other order, #99's
    tests still pass under this gate (decision 2). The one difference is the reply in its
    cycle 2 "touched" case: `fix_regression` instead of `blocked`, and that test does not assert
    the reply. The issue is marked blocked by #99 through GitHub's issue dependencies. The
    Execution section checks the precondition. *Evidence:* #99's plan (its decisions 1–3, its
    cycle 2 and 3 setups, and its "Interactions" section).

## Deliberate scope cuts (do not build)

None. The issue asks for the close gate, the run-start refusal and an unchanged benign path,
and all three are built. Rendering the run-level event in the friction log is not asked for: a
refused run is visible in its envelope and in `tdd status`.

## Fake and real divergence

| Seam | Fake behaviour | Real behaviour | Path left untested | Ruling |
|---|---|---|---|---|
| `check` command | `test ! -f <marker>` / `false`, a real shell command | a real freshness check (`git diff --exit-code`, a schema diff) | none: the tool only reads the exit code | acceptable |
| `regenerate = "true"` (cycle 2) | exits 0, writes nothing | a real generator that writes nothing because its inputs did not change | none: the tool only sees an exit code and `git status` | acceptable |

## Forms of "stale" (E-12c)

| Form | Reply at close | At `run start` | Pinned by |
|---|---|---|---|
| `check` fails, no `regenerate` | `fix_regression`, `stale_artifacts: [name]` | refused, `reason: stale_artifact` | cycles 1 and 4 |
| `check` fails, hook exits 0, nothing staged | `fix_regression`, `stale_artifacts: [name]` | refused, `reason: stale_artifact` | cycle 2 (same branch as cycle 4) |
| hook exits non-zero | `fix_regression`, `artifact_failures` (unchanged) | refused, `reason: artifact_regenerate_failed` (unchanged) | existing #107 tests |
| hook commits | `complete`, `regenerated` (unchanged) | run opens (unchanged) | existing #56 tests (decision 6) |
| stays stale, outside the run's reachable set (#99) | not checked (unless the cycle touched its producer, then as row 1) | run opens, `artifact_stale_inherited` | #99's cycle 2 and 3 tests (decision 10) |

## Cycles

Every test lives in `tests/test_artifact_regeneration.py`, at file scope like its existing
tests, and takes `(repo, tmp_path)`. They reuse the file's imports (`git`, `run_cli`,
`write_plan` from `conftest`; `gitutil`; `Ledger`) and its `PLAN`. No cycle creates a module
or a test file, so nothing is declared in `stub_expected`.

Cycle 1's RED also adds a module-level helper beside `_start_run_with_id`, used by every test
in this plan:

    def _register_spec_artifact(repo, toml_lines: str) -> str:
        """Declare artifact `spec` (with `toml_lines` appended), commit, register PLAN."""
        with (repo / "tdd.toml").open("a") as f:
            f.write(
                "\n[artifact.spec]\n"
                'path        = "backend/spec.json"\n'
                'produced_by = "backend"\n' + toml_lines
            )
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "declare spec artifact")
        plan = write_plan(repo, PLAN)
        assert run_cli(repo, "plan", "register", plan)["ok"]
        return plan

### Cycle 1: an unresolved stale artifact at close replies `fix_regression`

- **Behaviour:** at cycle close, an artifact whose `check` fails and that has no `regenerate`
  hook makes `tdd advance` reply `fix_regression` with `result.stale_artifacts` naming it, and
  the cycle does not close.
- **Test:** `test_unresolved_stale_artifact_at_close_replies_fix_regression`.
  `marker = tmp_path / "stale"`; `plan = _register_spec_artifact(repo, f'check       = "test !
  -f {marker}"\n')`; `run start` (assert `ok`); `marker.touch()`; `adv = run_cli(repo,
  "advance")`. Single assertion:
  `(adv["next_action"]["verb"], adv["result"].get("stale_artifacts")) == ("fix_regression", ["spec"])`.
- **Target:** `machine.py`: `ArtifactOutcome.stale`, and the append at `check_artifacts`'s
  `stale_artifact` event call, not at the `artifact_stale_inherited` arm (decision 2). `advance.py::_handle_refactor`: the reply directly
  after the `artifact_outcome.failed` reply (decision 3).
- **Docs, in this cycle's GREEN:**
  - `docs/PRD.md` R9.12: after "blocks the close — this is one of the few hard gates (§12),
    because a stale contract produces a *green* wrong answer.", add: "At cycle close the block
    is surfaced as `fix_regression` with `result.stale_artifacts` naming the artifacts. The
    cycle stays open until the check passes or the hook produces a commit."
  - `docs/harness-integration.md`: the `fix_regression` row's "the tool observed" cell becomes
    "tests outside the cycle are failing at GREEN, or the close sweep / lint / typecheck gates
    failed, or a declared artifact is stale or failed to regenerate".
- **EXPECTED FAILURE:** `AssertionError: assert ('complete', None) == ('fix_regression', ['spec'])`
  (probed on main).
- **Minimal GREEN:** the field, the append and the reply. Nothing in `cli.py` (that is cycle 4).

### Cycle 2 (pin): a stale artifact whose hook commits nothing gets the same reply

- **Behaviour:** an artifact whose `check` fails and whose `regenerate` hook exits 0 without
  changing anything is also unresolved, and gets the same reply.
- **Test:** `test_stale_artifact_whose_hook_commits_nothing_replies_fix_regression`. As cycle 1,
  with `toml_lines = f'check       = "test ! -f {marker}"\nregenerate  = "true"\n'`. Single
  assertion: `(adv["next_action"]["verb"], adv["result"].get("stale_artifacts")) ==
  ("fix_regression", ["spec"])`.
- **Target:** `machine.py::Engine.check_artifacts` (the same `if not resolved:` branch;
  unchanged in this cycle).
- **EXPECTED:** passes on arrival. On main it fails (`('complete', None)`, probed), and it passes
  once cycle 1's append sits in the `if not resolved:` branch (probed on the sketch). It pins
  R9.12's second unresolved form ("the regenerate hook produced no commit"). If it fails on
  arrival, cycle 1's GREEN keyed the gate on "no hook" instead of "not resolved". That is a
  semantic change, so do not make it under this pin's refactor phase: file
  `tdd blocker --kind plan_defect --detail '...'`.

### Cycle 3 (pin): once the artifact is fresh again, the next advance closes the cycle

- **Behaviour:** after a `fix_regression` reply for a stale artifact, making the check pass and
  running `tdd advance` again closes the cycle.
- **Test:** `test_cycle_closes_once_the_stale_artifact_is_fresh_again`. Cycle 1's setup; `first
  = run_cli(repo, "advance")`, then `assert first["next_action"]["verb"] == "fix_regression",
  first` as a precondition; `marker.unlink()`; `second = run_cli(repo, "advance")`. Single
  assertion: `second["next_action"]["verb"] == "complete"`.
- **Target:** `advance.py::_handle_refactor` (unchanged in this cycle).
- **EXPECTED:** passes on arrival (probed on the sketch: `complete`, `terminal: true`). It
  catches a GREEN that replies after `close_cycle`, or that records a blocker or ends the run.
  If it fails, cycle 1's reply is in the wrong place. That is a semantic change: file
  `plan_defect`, and do not fix it under a refactor phase.

### Cycle 4: `run start` refuses on an unresolved stale artifact

- **Behaviour:** when a declared artifact is stale and unresolved at `run start`, the command
  fails with `result.reason == "stale_artifact"` and `result.stale_artifacts` naming it, the
  error names it, the run row is ended with outcome `refused`, and no run is left active.
- **Test:** `test_unresolved_stale_artifact_at_run_start_refuses`.
  `plan = _register_spec_artifact(repo, 'check       = "false"\n')`; `out = run_cli(repo,
  "run", "start", "--plan", plan)`; `status = run_cli(repo, "status")`; `run_row =
  Ledger(gitutil.repo_identity(repo)).one("SELECT outcome FROM run ORDER BY id DESC LIMIT 1")`.
  Single assertion:

      (
          out["ok"],
          "spec" in (out.get("error") or ""),
          out["result"].get("reason"),
          out["result"].get("stale_artifacts"),
          run_row["outcome"],
          status["result"].get("active"),
      ) == (False, True, "stale_artifact", ["spec"], "refused", False)

  (`reason` is under `result`, never at the envelope's top level.)
- **Target:** `cli.py::cmd_run_start`, directly after the `artifact_outcome.failed` refusal
  (decision 5).
- **Existing tests this cycle breaks** (probed: exactly these two fail with the refusal in
  place). Edit both in the RED step, next to the new test. Both edits pass before and after the
  change (probed), so they do not disturb RED:
  - `test_unresolved_stale_artifact_still_emits_event`: its `check = "false"` run is now
    refused. Replace `out = run_cli(...)`, `assert out["ok"], out` and `run_id =
    out["run"]["id"]` with a bare `run_cli(repo, "run", "start", "--plan", plan)`, and look up
    the event without a run id: `ledger.one("SELECT * FROM integrity_event WHERE cycle_id IS
    NULL AND kind = 'stale_artifact' AND detail = 'spec'")`. Its assertion (`event is not
    None`) is unchanged. The test now shows that the refused run keeps its event.
  - `test_failed_regenerate_after_stale_check_reports_hook_failure_not_stale`: change its
    `'check       = "false"\n'` line to `f'check       = "test ! -f {marker}"\n'`, so `run
    start` finds the artifact fresh and the stale-then-hook-fails path still runs at close.
    Update the comment above `run start` to say the start-time check passes. Its assertion
    (`kinds == ["artifact_regenerate_failed"]`) is unchanged.
- **Docs, in this cycle's GREEN:**
  - `docs/PRD.md` R9.12: directly after the sentence "`run start` refuses when a regenerate hook
    fails before the first cycle; the run row is ended with outcome `refused`." (anchor on that
    sentence; #99 adds other sentences to R9.12), add: "It likewise refuses, with reason
    `stale_artifact`, when an artifact records `stale_artifact` before the first cycle; that run
    row is also ended `refused`. An inherited artifact (`artifact_stale_inherited`) does not
    refuse."
  - `CHANGELOG.md`, under `## [Unreleased]`'s `### Fixed` heading (#99 creates it; create it if
    it is absent), one bullet:
    "**An unresolved stale artifact now blocks the close, as PRD R9.12 specifies** (#110). An
    artifact whose `check` fails and that the tool cannot regenerate (no `regenerate` hook, or
    the hook commits nothing) used to record `stale_artifact` and let the cycle close. `tdd
    advance` now replies `fix_regression` with `result.stale_artifacts` naming it, and the
    cycle stays open until the check passes. `tdd run start` refuses with `reason:
    "stale_artifact"` and ends the run `refused`. An artifact the tool regenerates and
    commits is unaffected, and so is inherited staleness (`artifact_stale_inherited`, #99)."
- **EXPECTED FAILURE:** `AssertionError: assert (True, False, None, None, None, None) ==
  (False, True, 'stale_artifact', ['spec'], 'refused', False)` (probed on main: `run start`
  succeeds, its result has neither key, a live run's `outcome` is NULL, and a live run's
  `status` result has no `active` key).
- **Minimal GREEN:** the refusal block and the docs. Nothing in `machine.py` or `advance.py`.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-110-stale-artifact-gate   # first, before anything else
    tdd doctor                                      # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-110-stale-artifact-gate.md   # captures baselines, opens cycle 1

`tdd doctor` checks every project; `tdd run start` probes only the ones the plan declares and
those downstream of them through an `[artifact]`. A failing check on a project outside that set
does not stop the run: note it and go on. Any other failing check stops it.

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

**Precondition: #99 has landed.** Before `tdd run start`, `grep -n artifact_stale_inherited
src/tddcli/machine.py` must print a line. If it prints nothing, #99 is not on `main` yet: do not
start the run. Stop and say so (decision 10).

**Referee.** Use the released `tdd` on `PATH`, never `uv run tdd` from this tree (the note at
the top of `tdd.toml`). This plan changes no ledger table, so `SCHEMA_VERSION` does not move
and no frozen referee is needed. This repo's own `tdd.toml` declares no `[artifact]`, so the
gate this plan adds cannot fire on the run itself.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite was
  green at 37accb5, in a fresh worktree (`722 passed`), and #99 adds tests of its own, so the
  count will be higher. Expect `baselines: {tddcli: 0}` and no standing failures. Anything else
  means the branch moved: stop and find out why.
- #99's tests in `tests/test_artifact_regeneration.py` must stay green through every cycle
  (decision 10). If one fails, the GREEN that preceded it added an inherited artifact to
  `stale`. Fix that GREEN, never #99's test.
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`: the pins (cycles 2 and 3), and
    any standard cycle that pre-passes.
  - `create_stub`: no cycle declares a stub (every RED imports only existing symbols), so any
    request means an undeclared import.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|regression|tooling> --detail '...'`.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.
  - This plan declares no annotation keys, so `annotate_cycle` should not appear.
- If a pin (cycle 2 or 3) fails on arrival or after a later GREEN, the GREEN that preceded it
  is wrong. Fix the GREEN through a `plan_defect` blocker, never the pin. Never commit a
  semantic change under a refactor phase.

**Minimal GREEN, per cycle: add this and nothing earlier.**

- cycle 1 adds `ArtifactOutcome.stale`, a `stale_names.append(art.name)` (or equivalent) beside
  the `stale_artifact` event call and nowhere else (not in #99's inherited arm), the `fix_regression` reply in
  `_handle_refactor` after the `failed` reply, and the two doc edits. It does not touch
  `cmd_run_start`, and it does not move `regenerated.append` (decision 7).
- cycles 2 and 3 add no production code.
- cycle 4 adds the refusal in `cmd_run_start` after the `failed` refusal, the R9.12 sentence and
  the CHANGELOG bullet, and edits the two existing tests in its RED step.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-110-stale-artifact-gate-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-110-stale-artifact-gate-friction.md
    git commit -m "docs: friction log for issue-110-stale-artifact-gate"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #110`.

Docs are deliverables, not hopes:

- `git diff --stat origin/main -- docs/PRD.md` must be non-empty (cycles 1 and 4), or the PR body says why.
- `git diff --stat origin/main -- docs/harness-integration.md` must be non-empty (cycle 1), or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty (cycle 4), or the PR body says why.

Nothing a user *sees* changes outside the JSON envelopes of `tdd advance` and `tdd run start`,
so no demo recording is required.
