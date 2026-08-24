---
closes: 56
cycles:
  - n: 1
    project: tddcli
    title: "a resolved regeneration marks its artifact_check row regenerated=1"
    test: "tests/test_artifact_regeneration.py::test_successful_regeneration_marks_artifact_check_regenerated"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: successful regeneration sets artifact_check.regenerated"
    commit_green: "fix: mark artifact_check regenerated after a committed regen"

  - n: 2
    project: tddcli
    title: "a stale artifact the tool regenerates and commits emits no stale_artifact event"
    test: "tests/test_artifact_regeneration.py::test_resolved_stale_artifact_emits_no_event"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: resolved staleness emits no bare stale_artifact event"
    commit_green: "fix: stop emitting stale_artifact when regen resolves it"

  - n: 3
    project: tddcli
    title: "a stale artifact with no regenerate hook still emits stale_artifact"
    test: "tests/test_artifact_regeneration.py::test_unresolved_stale_artifact_still_emits_event"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: unresolved staleness still emits stale_artifact"
    commit_green: "fix: gate stale_artifact emission on unresolved staleness"

  - n: 4
    project: tddcli
    title: "the friction log reports regenerated artifacts benignly, not as a stale event"
    test: "tests/test_artifact_regeneration.py::test_friction_log_reports_regenerated_artifacts_benignly"
    files: ["src/tddcli/render.py"]
    commit_red: "test: friction log surfaces auto-regenerated artifacts"
    commit_green: "feat: friction log run header lists auto-regenerated artifacts"
---

# Issue #56 — stale_artifact reported as a bare event even when the tool auto-regenerates and commits

https://github.com/geuben/tdd-cli/issues/56
Task file: `tasks/issue-56-stale-artifact-reporting.md`

## Context

`Engine.check_artifacts` (`machine.py`) records that a generated artifact is stale and
then, when the artifact declares a `regenerate` hook, regenerates it and commits the
generated chain in the same call. The staging half of this flow was hardened earlier
(the artifact's own path now lands in the `chore(...): regenerate` commit). The
**residual** defect is purely reporting: staleness is reported the same whether the tool
silently fixed it or left it for the agent.

Two facts combine to make a routine, fully-handled regeneration read like an unresolved
problem:

1. `check_artifacts` emits `ledger.event(..., "stale_artifact", art.name)`
 **unconditionally** the moment an artifact is found stale — *before* it knows whether
 its own regenerate hook will resolve the staleness.
2. The `artifact_check` row it inserts carries a `regenerated` column, but that column is
 written `0` at insert time and is **never updated to 1** anywhere in the codebase, so
 the ledger has no positive record that the tool resolved the staleness itself.

The friction log then keys off the raw `integrity_event` table and renders every event
uniformly as `- **Event — {kind}:** {detail}`, so a stale-and-immediately-regenerated
artifact surfaces as a bare `stale_artifact` line indistinguishable from a genuine
integrity concern — and it inflates the `integrity_events` map in `metrics`.

**Chosen fix — proposal (1), recording resolution at the source rather than pairing it
back together in every projection.** When staleness is resolved by the tool (a
regenerate hook ran and produced a commit), we (a) update the `artifact_check` row to
`regenerated=1` and (b) suppress the `stale_artifact` event. The event is emitted only
when staleness is *unresolved* — no regenerate hook, or the hook produced no commit. The
friction log then reports resolved regenerations from `artifact_check` as a benign run
header line. This is more faithful and more testable than proposal (2): a resolved
regeneration is not an integrity event, so it correctly disappears from `metrics`
`integrity_events`, from `progress`, and from the per-cycle event stream at once, instead
of each projection having to re-derive resolution by joining events back to
`artifact_check.regenerated`. It also closes the standing bug that `regenerated` is never
set to 1.

Ordering: cycle 1 makes the ledger tell the truth (flag → 1 on a committed regen); cycle
2 stops the bare event for the resolved case; cycle 3 re-establishes the event for the
genuinely-unresolved case (triangulating against cycle 2's minimal deletion); cycle 4
surfaces the resolved regenerations benignly in the friction log.

## Verified repo facts

*Every fact below was read from the code during hardening — none from memory. Locators
are function/line names; grep for them at execution time.*

- **`check_artifacts` (`machine.py`)** does exactly this per artifact:
 skips artifacts with neither `check` nor `regenerate`; computes `stale =
 self._artifact_stale(art)`; inserts an `artifact_check` row with `regenerated=0`
 (hard-coded); `if not stale: continue`; else emits `ledger.event(...,
  "stale_artifact", art.name)`; then `if art.regenerate:` runs the
 regenerate command, builds `self.config.artifact_chain(art)`, computes the changed
 paths, calls `staging.commit_generated(...)` → `(sha, staged)`, and `if sha:` inserts a
 `commit_record`; finally `regenerated.append(art.name)`. The event is emitted **before
 and independently of** whether regeneration succeeds.
- **`artifact_check.regenerated` is never updated to 1 anywhere.** `grep -rn
 artifact_check src/` returns only the `CREATE TABLE` (`ledger.py`, column
 `regenerated INTEGER NOT NULL DEFAULT 0`) and the single `insert`
 (`machine.py`). There is no `UPDATE`. The flag is permanently 0 — this is itself
 part of the fix (cycle 1).
- **`Ledger.insert` returns `lastrowid`** (`ledger.py`), and `Ledger.update(table,
 row_id, **cols)` exists (`ledger.py`). Cycle 1's GREEN captures the
 `artifact_check` insert's rowid and calls `self.ledger.update("artifact_check", row_id,
 regenerated=1)` after a successful commit — no new ledger method needed.
- **Resolution signal.** `staging.commit_generated` returns a truthy `sha` when a commit
 was produced; the existing `test_regeneration_commits_the_artifacts_own_path` proves a
 regenerate hook that rewrites the artifact's own path (even without `generated = true`)
 yields a real `chore(openapi): regenerate` commit. So `resolved = bool(sha)` inside the
 `if art.regenerate:` block is a faithful, already-exercised signal.
- **`run start` checks artifacts with `cycle_row=None`.** `cmd_run_start`
 (`cli.py`) calls `engine.check_artifacts(None)` right after the baseline probe,
 before opening the first cycle. `_handle_refactor` (`advance.py`) calls
 `engine.check_artifacts(cycle)` with a real cycle. So a regeneration that fires at run
 start writes `artifact_check`/`integrity_event` rows with `cycle_id = NULL`.
- **The friction log never reads `artifact_check`, and drops `cycle_id = NULL` events.**
 `render.friction_log` (`render.py`) queries `integrity_event` ,
 `commit_record`, `invocation`, `annotation`, `blocker` — never `artifact_check`. Events
 are bucketed `events[e["cycle_id"]]` and rendered only inside the
 `for cycle in reversed(cycles)` loop as `- **Event — {kind}:**` , so
 an event with `cycle_id = NULL` (as a run-start regeneration produces) is **not rendered
 at all** today. Resolved regenerations therefore need a **run-level** line in the header,
 not a per-cycle one — this is why cycle 4 adds it beside the `Baseline failures at start`
 line (render.py), reading from `artifact_check WHERE regenerated=1`.
- **`metrics` counts `stale_artifact` today.** `render.metrics` builds `integrity_events`
 by grouping `integrity_event` on `kind` ; a resolved regeneration's
 `stale_artifact` currently lands in that map. Suppressing the event (cycle 2) removes it
 from `metrics` and `progress` automatically — no change to either function.
- **No test references `stale_artifact` or asserts on it.** `grep -rn stale_artifact
 tests/` is empty; the two existing tests in `tests/test_artifact_regeneration.py` assert
 only the commit contents and `next_action.verb == "complete"`. So cycle 2's minimal
 GREEN (removing the emit) breaks no existing test, and cycle 3 is a genuine RED, not a
 guard against an existing assertion.
- **Existing fixture reused as-is.** `tests/test_artifact_regeneration.py` already carries
 `_start_run(repo, artifact_toml)` (writes `schema/openapi.json = "v1\n"`, appends the
 artifact TOML, commits, registers, `run start`) and a single-cycle refactor `PLAN`. Its
 `openapi` artifact has `regenerate = "printf 'v2\n' > schema/openapi.json"` and no
 `check`, so at `run start` `_artifact_stale` (regenerate-only branch, `machine.py`)
 regenerates to `v2`, sees the tree change, returns stale, and `check_artifacts(None)`
 regenerates+commits it → a resolved regeneration with `cycle_id = NULL`. This is the
 cheapest resolved-case fixture; cycles 1, 2 and 4 build on it.
- **Ledger access pattern for tests** is established: `Ledger(gitutil.repo_identity(repo))`
 then `ledger.all("SELECT ... FROM integrity_event WHERE run_id = ?", (run_id,))`
 (`tests/test_baseline_integrity.py`). `run start`'s envelope exposes
 `out["run"]["id"]`. `run_cli`, `git`, `write_plan` are imported from `conftest` at the
 top of `test_artifact_regeneration.py`.
- **`_artifact_stale` check-only branch** (`machine.py`): `if art.check:` runs the
 command and returns `code != 0` — it does not touch `art.path`. So a `check = "false"`
 artifact with no `regenerate` is reliably stale at run start with no file setup, which is
 cycle 3's unresolved fixture.

## Cycle detail

*Expected failure per cycle, minimum GREEN, and what future-cycle behaviour to resist.*

### Cycle 1 — resolved regeneration sets `regenerated=1`

**Expected RED (probe-verified):** `assert 0 == 1` — the `artifact_check` row for `openapi`
(the stale one) has `regenerated == 0`, because nothing ever updates the column. Confirmed
empirically during hardening: the existing `openapi` regenerate fixture, run through
`run start`, produces exactly one `artifact_check` row `{artifact: openapi, stale: 1,
regenerated: 0, cycle_id: NULL}`, a `stale_artifact` event with `cycle_id = NULL`, and a
`chore(openapi): regenerate` commit — so the resolution signal (`sha` truthy) is real and
the flag is indeed stuck at 0.

Test: reuse `_start_run` with the existing `openapi` regenerate TOML (copy the literal
from `test_regeneration_commits_the_artifacts_own_path`). After `run start` succeeds, open
`Ledger(gitutil.repo_identity(repo))` and read
`SELECT stale, regenerated FROM artifact_check WHERE run_id = ? AND artifact = 'openapi'
AND stale = 1`. Assert the row exists and `regenerated == 1`. (Capture `run_id` from the
`run start` envelope; `_start_run` returns nothing, so inline its body or extend it to
return the plan and re-run `run start` capturing the envelope — simplest is to not use the
helper and assert on the `run start` envelope directly.)

GREEN: in `check_artifacts`, capture the insert rowid (`check_id =
self.ledger.insert("artifact_check", ...)`), and inside the `if art.regenerate:` block,
after `commit_generated`, when `sha` is truthy call `self.ledger.update("artifact_check",
check_id, regenerated=1)`. Do not touch the event emission yet — that is cycle 2.

### Cycle 2 — resolved staleness emits no `stale_artifact` event

**Expected RED:** the `stale_artifact` event exists — assert it is absent, RED shows one
row.

Test: same `openapi` fixture and `run start`. Assert
`ledger.all("SELECT * FROM integrity_event WHERE run_id = ? AND kind = 'stale_artifact'",
(run_id,))` is empty.

GREEN (minimal): stop emitting `stale_artifact` in the resolved path. The smallest change
a minimal implementer makes here is to move the emit *after* the regenerate/commit block
and drop it — cycle 3 is what forces the conditional back in. Concretely: remove the
unconditional emit at; the event is re-introduced, gated, in cycle 3.

Resist: do not add the run-level render line here (cycle 4); do not special-case the
check-only artifact (cycle 3).

### Cycle 3 — unresolved staleness still emits `stale_artifact`

**Expected RED:** after cycle 2 deleted the emit, a stale artifact the tool cannot fix
produces **no** event — assert one exists, RED shows none.

Test: a new fixture variant — append an artifact with a failing `check` and no
`regenerate`, e.g.

    [artifact.spec]
    path        = "backend/spec.json"
    produced_by = "backend"
    check       = "false"

(`check = "false"` exits non-zero → stale; no `regenerate` → nothing the tool can do.)
After `run start`, assert
`ledger.one("SELECT * FROM integrity_event WHERE run_id = ? AND kind = 'stale_artifact'
AND detail = 'spec'", (run_id,))` is not None.

GREEN: re-introduce the emit, gated on unresolved staleness. Track a local `resolved =
False`, set it `True` only when `art.regenerate` ran and produced a `sha`, and after the
regenerate/commit block emit `stale_artifact` only `if not resolved`. This leaves cycle
2's resolved case silent and cycle 1's flag update intact (both keyed on the same `sha`),
while the no-hook artifact — `resolved` never set — emits as before.

Resist: keep the emit detail as `art.name` (unchanged wire shape); do not invent a new
event kind for the resolved case — resolution is recorded by the flag, not by a second
event.

### Cycle 4 — friction log reports regenerated artifacts benignly

**Expected RED:** the rendered friction log does not contain the word `auto-regenerated`
(and, having no `artifact_check` reader, does not mention `openapi` at all now that the
event is gone).

Test: run the `openapi` fixture through to completion (`run start`, then `advance` →
`next_action.verb == "complete"`, mirroring `test_regeneration_commits_the_artifacts_own_path`),
then `run_cli(repo, "log", "render", "--out", str(repo / "friction.md"))` and read the
text. Assert it contains `auto-regenerated` and `openapi`, and — proving the benign
framing — assert `stale_artifact` is **not** in the text.

GREEN: in `friction_log`, beside the `Baseline failures at start` line (render.py),
query `SELECT DISTINCT artifact FROM artifact_check WHERE run_id = ? AND regenerated = 1`
and, when non-empty, append `- Artifacts auto-regenerated: ` + `_fmt_list([...])`. Emit the
line only when there is at least one such artifact, so the existing
`test_friction_log_and_metrics_render_from_the_ledger` (a repo with no artifacts) is
unaffected. Depends on cycle 1's flag; place after it (it is cycle 4, so this holds).

## Deliberate scope cuts (do not build)

- **Rendering unresolved stale artifacts in the run header.** Cycle 3 keeps the
 `stale_artifact` *event*; a run-start unresolved staleness (`cycle_id = NULL`) is still
 invisible in the friction log because the per-cycle event loop drops NULL-cycle events.
 Making unresolved staleness visible at run level is a separate reporting gap, not what
 #56 is about (#56 is resolved regenerations reading as problems). Do not build a
 symmetric "unresolved stale artifacts" header line.
- **Detecting a regenerate hook that errors.** `check_artifacts` ignores the regenerate
 command's exit code (`adapters.base.run_command` return value is discarded). This plan
 treats "produced a commit" (`sha` truthy) as resolution and "no commit" as unresolved,
 which correctly routes a no-op/failed hook to the event. Wiring the command's exit code
 into a distinct failure signal is out of scope — do not change `run_command`'s contract.
- **`metrics` / `progress` changes.** Both read `integrity_event` by kind; suppressing the
 resolved event (cycle 2) removes `stale_artifact` from them automatically. Do not add a
 dedicated metrics field or a `progress` line — no cycle, no test.
- **A new event kind for resolved regenerations.** Resolution is recorded by
 `artifact_check.regenerated = 1`, not by a second integrity event; adding an
 `artifact_regenerated` event would re-pollute `metrics.integrity_events`. Do not add it.
- **PRD/README documentation** of the reporting change: same PR, after the run completes,
 as ordinary commits — not a cycle (see Done-criteria).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do
not ask the user to start the run. `tdd run start` records which model is executing,
resolved from your own session; a run started by anyone else attributes this work to the
wrong agent.

**Referee rule:** run the *released* `tdd` **0.7.0**, never this working tree's editable
install. Do not work in a shell with this repo's `.venv` activated. Verify before
starting: `tdd --version` → **0.7.0**.

> **Environment blocker found at hardening (2026-08-23):** `~/.local/bin/tdd` is stale at
> **0.6.0**, which understands ledger schema only up to v2 and *cannot open this repo's
> v3 ledger* — `tdd doctor` fails with "written by a newer tdd-cli". Meanwhile `which tdd`
> may resolve to a `.venv` on `PATH`. Before starting you MUST have 0.7.0 as the `tdd` you
> invoke: `uv tool upgrade tdd-cli` (or reinstall) so `~/.local/bin/tdd --version` → 0.7.0,
> and confirm `which tdd` is a 0.7.0 binary that is **not** `/Volumes/SSD/repos/tdd-cli/.venv`
> (this working tree's own editable install). A separate 0.7.0 clone is fine.

The suites under test are still this working tree's code; only the controller is pinned.

The branch `feat/56-stale-artifact-reporting` already exists — it was created at hardening
and carries this plan's commit. Check it out; if it has grown unrelated work, stop and ask.

    git checkout feat/56-stale-artifact-reporting       # exists: created at hardening, carries this plan
    tdd doctor                                          # must report healthy: true
    tdd run start --plan tasks/issue-56-stale-artifact-reporting.md

`tdd doctor` must be green first: if it reports "worktree clean" failing on *other*
uncommitted `tasks/issue-*.md` files (sibling plans not part of this work), commit, stash,
or gitignore them before `run start`.

Then repeat until done: read `next_action.verb`, do exactly what it says, run
`tdd advance`. Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it,
and raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit`
 — the tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. Expected
 baseline for this repo: `{"tddcli": 0}` — anything else means a moved branch; stop.
- Verbs this plan can hit: `run_sensitivity_check` → `tdd sensitivity begin|check|end`
 (only if a RED passes on arrival — none is expected to); `resolve_blocker` →
 `tdd blocker --kind --detail` (kinds: `plan_defect`, `tooling`, `regression`,
 `pre_existing_failure`); `confirm_cycle_applicable` on a cycle the codebase has outgrown
 → `tdd cycle skip --reason`. This plan declares no `annotation_keys`.

## Done-criteria

**Before finishing:** run
`tdd log render --out tasks/friction-logs/issue-56-stale-artifact-reporting-friction.md`
and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped —
and every integrity event. Do not narrate what the ledger already records.

Then the documentation follow-up, committed as ordinary commits on the branch after the
run is terminal: note in the PRD's artifact/reporting section (R9.12/R9.20 family) that a
tool-resolved regeneration is recorded via `artifact_check.regenerated` and reported as an
"auto-regenerated" line, and that `stale_artifact` now signals only unresolved staleness;
update the README's friction-log section if it enumerates event kinds.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-56-stale-artifact-reporting-friction.md
    git commit -m "docs: friction log for issue-56-stale-artifact-reporting"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes
the branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If
a gate fails, fix it and re-run the skill — a failed gate is work, not a reason to hand
back.
