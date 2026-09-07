---
closes: 107
cycles:
  - n: 1
    project: tddcli
    title: "a regenerate hook that exits non-zero marks its artifact_check row regenerate_failed=1"
    test: "tests/test_artifact_regeneration.py::test_failed_regenerate_hook_marks_artifact_check_regenerate_failed"
    files: ["src/tddcli/machine.py", "src/tddcli/ledger.py"]
    commit_red: "test: a failed regenerate hook is recorded on artifact_check"
    commit_green: "fix: capture the regenerate hook's exit code; record regenerate_failed"

  - n: 2
    project: tddcli
    title: "a v8 ledger is migrated in place to v9 and gains the regenerate_failed column"
    test: "tests/test_release_surface.py::test_artifact_check_gains_regenerate_failed_column"
    files: ["src/tddcli/ledger.py"]
    commit_red: "test: v8 ledger gains artifact_check.regenerate_failed on open"
    commit_green: "feat: ledger schema v9 — artifact_check.regenerate_failed migration"

  - n: 3
    project: tddcli
    title: "a failed regenerate hook emits artifact_regenerate_failed carrying the exit code and stderr"
    test: "tests/test_artifact_regeneration.py::test_failed_regenerate_hook_emits_artifact_regenerate_failed_event"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: failed regenerate hook emits artifact_regenerate_failed"
    commit_green: "feat: artifact_regenerate_failed integrity event with code and stderr"

  - n: 4
    project: tddcli
    title: "a failed regenerate hook at cycle close replies fix_regression, not complete"
    test: "tests/test_artifact_regeneration.py::test_failed_regenerate_hook_at_close_replies_fix_regression"
    files: ["src/tddcli/machine.py", "src/tddcli/advance.py"]
    commit_red: "test: failed regenerate hook at close replies fix_regression"
    commit_green: "fix: a failed regenerate hook is a close-sweep failure, not a fresh artifact"

  - n: 5
    project: tddcli
    pin_cycle: true
    title: "once the hook recovers, the next advance closes the cycle normally"
    test: "tests/test_artifact_regeneration.py::test_cycle_closes_once_the_regenerate_hook_recovers"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: pin — a recovered regenerate hook lets the cycle close"

  - n: 6
    project: tddcli
    title: "a stale artifact whose regenerate hook fails reports the hook failure, not bare stale_artifact"
    test: "tests/test_artifact_regeneration.py::test_failed_regenerate_after_stale_check_reports_hook_failure_not_stale"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: stale-then-failed regenerate reports artifact_regenerate_failed only"
    commit_green: "fix: route the check-then-regenerate path through the hook-failure outcome"

  - n: 7
    project: tddcli
    title: "run start refuses when a regenerate hook fails before cycle 1"
    test: "tests/test_artifact_regeneration.py::test_failed_regenerate_hook_at_run_start_refuses"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: run start refuses on a failed regenerate hook"
    commit_green: "fix: run start refuses when an artifact cannot be regenerated"

  - n: 8
    project: tddcli
    pin_cycle: true
    title: "the friction log lists the hook failure under its cycle"
    test: "tests/test_artifact_regeneration.py::test_friction_log_lists_failed_regeneration_under_its_cycle"
    files: ["src/tddcli/render.py"]
    commit_red: "test: pin — friction log renders artifact_regenerate_failed per cycle"
ancillary_files:
  - "docs/PRD.md"
  - "CHANGELOG.md"
---

# Issue #107 — a failed regenerate hook is recorded as "not stale"

https://github.com/geuben/tdd-cli/issues/107
Task file: `tasks/issue-107-regenerate-hook-failure.md`
Companion: #108 (accept-failures folds run-introduced failures into the baseline) — separate plan.

## Context

`Engine._artifact_stale` (`src/tddcli/machine.py`) decides staleness for an artifact that has a
`regenerate` hook but no `check` by running the hook and comparing the artifact path's tree hash
before and after. The hook's exit code is discarded. A hook that fails leaves the path untouched,
so the hash is unchanged and the artifact is recorded as **fresh**: `artifact_check.stale = 0`, no
event, no blocker, and `tdd advance` replies `complete`. The second hook invocation inside
`Engine.check_artifacts` (the `check`-then-`regenerate` path) discards the exit code the same way;
there the only symptom is a bare `stale_artifact` event with no stderr, which today blocks nothing.

Probed empirically on `main` before drafting (throwaway test, deleted):

- Close-time failure (hook `exit 1` with `boom` on stderr): `advance` → `next_action.verb =
  "complete"`; `artifact_check` rows `{stale: 0, regenerated: 0}`; zero integrity events.
- Run-start failure: `run start` → `ok: true`, run opened, cycle 1 `AWAITING_REFACTOR`.
- `artifact_check` columns today: `id, run_id, cycle_id, artifact, stale, regenerated, at`.

The suite is green on `main` (483 passed).

## Design decisions (locked)

1. **Close-time reply is `fix_regression`, gate-style** — *user decision, 2026-09-07.* A failed
   hook is surfaced the way a red lint gate is (`advance.py` `_handle_refactor`, the
   `outcome.gates` branch): verb `fix_regression`, result carries
   `artifact_failures: [{artifact, code, stderr}]`, the reply is issued **before** `engine.sweep`
   and before `close_cycle`, so the cycle stays open and the downstream suites are not run against
   an artifact that could not be rebuilt. The executor fixes the producer and re-advances. **No new
   blocker kind**: the escape hatch is the existing `regression` blocker (a defect the run
   introduced). The `BLOCKER_KINDS` set in `cli.py` is not touched.
2. **Run start refuses** — *user decision, 2026-09-07.* When `check_artifacts(None)` in
   `cmd_run_start` reports a failed hook, the command returns `failure(...)` naming the artifact
   and quoting the hook's stderr, with `reason="artifact_regenerate_failed"`. Because
   `check_artifacts` needs an `Engine`, which needs the run row, the row already exists at that
   point: the refusal ends it in place (`ledger.update("run", run_id, ended_at=now(),
   outcome="refused")`) so `Ledger.active_run` (which filters `ended_at IS NULL`) no longer finds
   it and `tdd status` reports no active run. A refused row is inert and auditable; do not
   delete rows. The `artifact_check` rows and `artifact_regenerate_failed` event written during
   the probe stay attached to the refused run.
3. **Ledger records the failure as a column, not a tri-state** — *evidence.* `artifact_check`
   gains `regenerate_failed INTEGER NOT NULL DEFAULT 0`. `stale` keeps its meaning (0 when the
   probe could not decide — it is not a claim of freshness once `regenerate_failed = 1`).
   Schema goes v8 → v9 with `MIGRATIONS[8] = "ALTER TABLE artifact_check ADD COLUMN
   regenerate_failed INTEGER NOT NULL DEFAULT 0;"`, following the v4/v5/v6 precedent.
4. **Integrity event `artifact_regenerate_failed`** — *evidence.* Detail is a JSON object
   `{"artifact": <name>, "code": <int>, "stderr": <last 2000 chars>}`. Emitted from
   `check_artifacts` for both hook call sites. It **supersedes** `stale_artifact` for that check:
   when the hook fails, `stale_artifact` is not emitted for the same artifact in the same check
   (the check-then-regenerate path today emits `stale_artifact` because `resolved` stays False;
   cycle 6 changes that branch).
5. **`check_artifacts` returns a structured outcome** — *evidence.* Replace the `list[str]`
   return with a dataclass `ArtifactOutcome(regenerated: list[str], failed: list[dict])` in
   `machine.py` (same style as `SweepOutcome`). `_artifact_stale` becomes a probe that returns
   `(stale: bool, failure: dict | None)` so the caller sees the exit code. Both callers
   (`advance.py` `_handle_refactor`, `cli.py` `cmd_run_start`) are updated in the cycle that
   needs the new field; the `result["regenerated"]` shape in the `complete` envelope is
   unchanged (`outcome.regenerated or None`).
6. **Friction log needs no new rendering** — *evidence.* `render.py` already prints every
   per-cycle integrity event as `- **Event — <kind>:** <detail[:300]>`, so the new event lists
   under its cycle for free; cycle 8 pins that. Run-level events (cycle_id NULL) are not rendered
   today, which is why decision 2 refuses rather than warns.
7. **Test fixture shape** — *evidence.* Every close-time test declares an artifact whose hook is
   `test ! -f <tmp_path>/fail || { echo boom >&2; exit 1; }`: it succeeds at `run start`, and the
   test creates the marker (outside the repo, so no `undeclared_file_touched`) before `advance`.
   Proven by the probe. Only cycle 7 creates the marker before `run start`.

## Deliberate scope cuts (do not build)

- **`stale_artifact` (no hook, or hook produced no commit) still does not block the close.**
  PRD R9.12 calls it a hard gate; the code only records the event. Premise: #107 is about a
  *failed* hook being read as fresh; the unresolved-stale gate is a separate contradiction between
  PRD and code and gets its own issue. Re-evaluation trigger: if cycle 6's minimal green cannot
  distinguish "hook failed" from "hook ran, nothing changed" without also changing what
  `stale_artifact` does, stop and file a `plan_defect` blocker — do not absorb the gate into this
  plan.
- **A crashing `check` command (e.g. exit 127, command not found) is still read as "stale".**
  Premise: a non-zero `check` is stale by contract; distinguishing a crash needs a convention
  (exit-code ranges) the config schema does not have. Not built.
- **No run-header line "Artifacts failed to regenerate: …" in the friction log.** Per-cycle event
  lines suffice for the audit; a header line is #108-adjacent reporting work.
- **`stderr` in the event is truncated to the last 2000 chars**, matching `target_failure[:2000]`
  in `machine.py`. Full output is not persisted.
- **Companion #108 is not touched.** Nothing in this plan changes baselines or `--accept-failures`.

## Cycles

Every test lives in `tests/test_artifact_regeneration.py` unless stated; that file's helpers
(`_start_run_with_id`, `PLAN`, `git`, `run_cli`, `write_plan`) are reused. All test ids are
relative to the `tddcli` project root (`.`). No `stub_expected` anywhere: no cycle creates a
module or test file.

### Cycle 1 — record the failure on `artifact_check`

**Behaviour.** At cycle close, a regenerate hook that exits non-zero leaves an `artifact_check`
row for that cycle with `regenerate_failed = 1`.

**Test.** `test_failed_regenerate_hook_marks_artifact_check_regenerate_failed`: declare the
`wasm` artifact per decision 7, start the run, create the marker, `advance`, then read the row
`SELECT * FROM artifact_check WHERE run_id = ? AND cycle_id IS NOT NULL AND artifact = 'wasm'`.
Single assertion: `dict(row).get("regenerate_failed") == 1`.

**Production target.** `machine.py`: `Engine._artifact_stale` captures the hook's
`(code, out, err)` and returns the failure alongside the staleness flag;
`Engine.check_artifacts` writes `regenerate_failed=int(bool(failure))` on the inserted row.
`ledger.py`: `SCHEMA` adds the column to `artifact_check`. Minimal green may leave
`SCHEMA_VERSION` at 8 (fresh ledgers get the column from `CREATE TABLE`); cycle 2 handles
existing ledgers.

**EXPECTED FAILURE:** fails with `AssertionError: assert None == 1` (the column does not exist,
so `.get` returns `None`).

### Cycle 2 — migrate existing ledgers

**Behaviour.** A ledger stored at schema v8 is upgraded in place on open and gains
`artifact_check.regenerate_failed`.

**Test.** `tests/test_release_surface.py::test_artifact_check_gains_regenerate_failed_column`,
mirroring `test_plan_contract_gains_ancillary_files_column`: open a fresh ledger, force
`meta.schema_version` back to `'8'`, `ALTER TABLE artifact_check DROP COLUMN regenerate_failed`
(SQLite ≥ 3.35, available under the project's Python 3.12), close, reopen, read
`PRAGMA table_info(artifact_check)`. Single assertion: `"regenerate_failed" in cols`.

**Production target.** `ledger.py`: `SCHEMA_VERSION = 9`; `MIGRATIONS[8] = "ALTER TABLE
artifact_check ADD COLUMN regenerate_failed INTEGER NOT NULL DEFAULT 0;"` with the usual comment
line.

**EXPECTED FAILURE:** fails with `AssertionError: assert 'regenerate_failed' in {...}` — with
`SCHEMA_VERSION` still 8 the migration loop does not run, and `CREATE TABLE IF NOT EXISTS`
does not add columns to an existing table. (If cycle 1's green already bumped the version and
added the migration, this test passes on arrival: record it as the tool directs — the
sensitivity check will show the migration line is load-bearing.)

### Cycle 3 — the integrity event

**Behaviour.** The same failure emits one `artifact_regenerate_failed` integrity event on the
cycle, whose detail is JSON with the artifact name, exit code, and the hook's stderr.

**Test.** `test_failed_regenerate_hook_emits_artifact_regenerate_failed_event`: same setup as
cycle 1; read `SELECT detail FROM integrity_event WHERE run_id = ? AND kind =
'artifact_regenerate_failed'`; parse it. Single assertion:
`(detail["artifact"], detail["code"], "boom" in detail["stderr"]) == ("wasm", 1, True)`.

**Production target.** `machine.py` `Engine.check_artifacts`: when the probe reports a failure,
`self.ledger.event(run_id, cycle_id, "artifact_regenerate_failed", json.dumps({...}))` and
`continue` (do not fall into the stale/regenerate branch).

**EXPECTED FAILURE:** fails with `TypeError: 'NoneType' object is not subscriptable` at the
`event["detail"]` read (no row) — guard it: write the test as
`event = ledger.one(...)` then `detail = json.loads(event["detail"]) if event else {}` so the
failure is `AssertionError: assert (None, None, False) == ('wasm', 1, True)`.

### Cycle 4 — the advance reply

**Behaviour.** At cycle close a failed hook makes `tdd advance` reply `fix_regression` with
`result.artifact_failures` naming the artifact, and the cycle does not close.

**Test.** `test_failed_regenerate_hook_at_close_replies_fix_regression`: same setup; capture the
`advance` envelope. Single assertion:
`(adv["next_action"]["verb"], [f["artifact"] for f in adv["result"].get("artifact_failures", [])])
== ("fix_regression", ["wasm"])`.

**Production target.** `machine.py`: `check_artifacts` returns `ArtifactOutcome` (decision 5).
`advance.py` `_handle_refactor`: after `outcome = engine.check_artifacts(cycle)`, if
`outcome.failed` return `_reply(engine, cycle, Verb.FIX_REGRESSION, "Artifact regenerate hook
failed for: <names>. Fix the producer and re-run `tdd advance`.", artifact_failures=outcome.failed,
commit=sha)` before the sweep; `regenerated` later reads `outcome.regenerated`. `cli.py`
`cmd_run_start` keeps compiling: it ignores the return value today, so only the call site type
changes. Also in this cycle: update `docs/PRD.md` R9.12 and R9.20 to state that a non-zero
regenerate exit is a close-sweep failure surfaced as `fix_regression` (never "fresh"), and add
`artifact_regenerate_failed` to the IntegrityEvent list in §5.

**EXPECTED FAILURE:** fails with `AssertionError: assert ('complete', []) == ('fix_regression',
['wasm'])` (probe-verified: today's reply is `complete`).

### Cycle 5 — pin: recovery closes the cycle *(pin_cycle)*

**Behaviour.** After a `fix_regression` reply for a failed hook, removing the cause and running
`tdd advance` again closes the cycle (`complete`).

**Test.** `test_cycle_closes_once_the_regenerate_hook_recovers`: same setup; first `advance`
(hook fails), delete the marker, second `advance`. Single assertion:
`second["next_action"]["verb"] == "complete"`.

**Why a pin.** Cycle 4 delivers this if its reply is issued before `close_cycle`; the pin exists
to catch a green that replies `fix_regression` *after* closing the cycle. It must pass on
arrival. If it fails, cycle 4's implementation is wrong — fix it under cycle 5's refactor phase,
do not weaken the test.

### Cycle 6 — the check-then-regenerate path

**Behaviour.** An artifact with `check` that reports stale and a `regenerate` hook that then
fails records the hook failure (`artifact_regenerate_failed`) and does **not** emit
`stale_artifact` for that cycle.

**Test.** `test_failed_regenerate_after_stale_check_reports_hook_failure_not_stale`: declare the
artifact with `check = "false"` plus the decision-7 hook; start the run (the start-time check
finds it stale, the hook succeeds but changes nothing, so a run-level `stale_artifact` is
recorded — that is existing behaviour and outside the assertion); create the marker; `advance`;
read `SELECT kind FROM integrity_event WHERE run_id = ? AND cycle_id IS NOT NULL ORDER BY id`.
Single assertion: `kinds == ["artifact_regenerate_failed"]`.

**Production target.** `machine.py` `Engine.check_artifacts`, the `if art.regenerate:` branch
under `if not stale: continue`: capture the second `run_command` result; on non-zero exit write
`regenerate_failed=1` on the check row, emit `artifact_regenerate_failed`, append to
`outcome.failed`, and skip the `stale_artifact` emission for this artifact.

**EXPECTED FAILURE:** fails with `AssertionError: assert ['stale_artifact'] ==
['artifact_regenerate_failed']`.

### Cycle 7 — run start refuses

**Behaviour.** When a regenerate hook fails during `run start`, the command fails, names the
artifact, and leaves no active run.

**Test.** `test_failed_regenerate_hook_at_run_start_refuses`: create the marker **before**
`run start`; capture the start envelope and then `run_cli(repo, "status")`. Single assertion:
`(out["ok"], "wasm" in (out.get("error") or ""), status["result"].get("active")) == (False,
True, False)`.

**Production target.** `cli.py` `cmd_run_start`: `outcome = engine.check_artifacts(None)`; if
`outcome.failed`: `ledger.update("run", run_id, ended_at=now(), outcome="refused")` and return
`failure(f"artifact {name}: regenerate hook exited {code} — {stderr tail}. The artifact cannot be
kept fresh on this machine; fix the hook or the toolchain and retry.",
reason="artifact_regenerate_failed", artifacts=outcome.failed)`. The `finally: release_claim`
already covers the early return. Also in this cycle: add a sentence to `docs/PRD.md` R9.12
("`run start` refuses when a regenerate hook fails before the first cycle; the run row is ended
with outcome `refused`"), and add the `CHANGELOG.md` `[Unreleased]` entries (a **Fixed** bullet
for the close-time behaviour, an **Added** bullet for the event/column and the run-start
refusal, and a note that the ledger schema is now v9).

**EXPECTED FAILURE:** fails with `AssertionError: assert (True, False, None) == (False, True,
False)` (probe-verified: `run start` succeeds today and `status` shows the live run).

### Cycle 8 — pin: friction log lists the failure *(pin_cycle)*

**Behaviour.** `tdd log render` on a run whose cycle hit a failed hook prints an
`artifact_regenerate_failed` event line under that cycle.

**Test.** `test_friction_log_lists_failed_regeneration_under_its_cycle`: same setup as cycle 4
(the run is left open after the `fix_regression` reply — `log render` renders a live run with
`Outcome: live`); render to `repo / "friction.md"`. Single assertion:
`"Event — artifact_regenerate_failed" in text`.

**Why a pin.** `render.py` already prints every per-cycle event generically; this locks that the
new event is reachable by that path. Must pass on arrival; if it does not, the event was written
with `cycle_id=None` — fix `check_artifacts`, not the renderer.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-107-regenerate-hook-failure     # first, before anything else
    tdd doctor                                            # must report healthy: true
    tdd run start --plan tasks/issue-107-regenerate-hook-failure.md   # captures baselines, opens cycle 1

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. Expected summary
  line for `tddcli`: `483 passed` (0 baseline failures); anything else means the branch moved.
- The referee is the **released** tdd-cli (see the comment at the top of `tdd.toml`), not this
  working tree. The `tdd` on PATH here is the venv's *editable* install of the tree you are
  editing, so run every `tdd` command in this plan as `uvx tdd-cli@0.10.1 <args>` (or `uv tool
  install tdd-cli==0.10.1` once and use that binary). Cycle 2 bumps the ledger schema the working
  tree writes into *test* ledgers under `TDD_LEDGER_HOME`; the referee's own ledger for this
  repo is untouched.
- Verbs this plan will hit: `write_test` / `write_implementation` / `refactor_or_advance` on
  cycles 1–4, 6, 7; `write_test` then `refactor_or_advance` on the pins (5, 8), where the tool
  expects the test to pass on arrival; `run_sensitivity_check` → `tdd sensitivity begin|check|end`
  if a standard cycle's test passes on arrival (cycle 2 is the likely one); `annotate_cycle` —
  none, this plan declares no `annotation_keys`; `resolve_blocker` → `tdd blocker --kind
  --detail` with kinds `regression`, `plan_defect`, or `tooling`; `confirm_cycle_applicable` on
  a non-existent cycle → `tdd cycle skip --reason` (not expected: every cycle is applicable).

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-107-regenerate-hook-failure-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Ancillary docs are deliverables: `git diff --stat origin/main -- docs/PRD.md` must be non-empty
(R9.12, R9.20, IntegrityEvent list) and `git diff --stat origin/main -- CHANGELOG.md` must be
non-empty (`[Unreleased]` entries), or the PR body says which cycle dropped them and why.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-107-regenerate-hook-failure-friction.md
    git commit -m "docs: friction log for issue-107-regenerate-hook-failure"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.
