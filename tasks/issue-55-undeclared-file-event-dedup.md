---
closes: 55
cycles:
  - n: 1
    project: tddcli
    title: "an unchanged undeclared file is flagged once per cycle, not once per phase"
    test: "tests/test_undeclared_dedup.py::test_unchanged_outside_file_is_flagged_once_per_cycle"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: undeclared_file_touched floods a cycle across phases"
    commit_green: "feat: skip re-emitting undeclared_file_touched already seen this run"

  - n: 2
    project: tddcli
    title: "a newly-appearing undeclared path re-emits the event"
    test: "tests/test_undeclared_dedup.py::test_a_new_undeclared_path_re_emits"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: a new undeclared path must still be flagged"
    commit_green: "feat: re-emit undeclared_file_touched only when the outside set changes"

  - n: 3
    project: tddcli
    title: "the dedup is scoped to the cycle, not the run"
    test: "tests/test_undeclared_dedup.py::test_dedup_is_per_cycle_not_per_run"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: a later cycle touching the same path gets its own event"
    commit_green: "feat: scope undeclared_file_touched dedup to the cycle"
    commit_refactor: "refactor: extract last-outside lookup helper"
---

# Issue #55 — dedup `undeclared_file_touched` within a cycle

https://github.com/geuben/tdd-cli/issues/55
Task file: `tasks/issue-55-undeclared-file-event-dedup.md`

## Context

When a file outside the cycle's declared project roots is touched and left
uncommitted, `_stage_and_commit` classifies it as `outside` and emits an
`undeclared_file_touched` integrity event. `_stage_and_commit` runs **once per phase
invocation** — RED, GREEN, REFACTOR, and again on every `--retry` and every close-sweep
lap that re-enters a handler. The `outside` classification never stages the file (it is
outside every project root, so no phase commit ever picks it up), so it persists across
every phase and the *same* event is re-emitted verbatim each time. A single cycle that
lingers on one undeclared path can accumulate a handful of identical rows, which the
friction log then renders one-per-line, drowning the cycle's real signal.

The fix is **emit-time**, not render-time: stop writing the redundant rows at the source
so the ledger stays honest and every projection (friction log, metrics, progress)
benefits without each learning to collapse duplicates. Before emitting, compare the
current `outside` set against the last `undeclared_file_touched` detail already recorded
**for this cycle**; emit only when it is the first occurrence or the set has changed
(a genuinely new undeclared path appeared). Render-time collapsing is rejected as a
deliberate scope cut — it would leave the redundant rows in the store and every consumer
carrying the duplication.

This mirrors the shape already used for run-level event dedup in `_check_config_drift`
(`advance.py`), which refuses to re-emit `config_changed` for a `detail` already on the
run — the same "don't record what we already recorded" discipline, narrowed here to a
per-cycle key and a *changed-since-last* comparison rather than pure existence.

Ordering: cycle 1 collapses the identical-set flood (the reported bug); cycle 2 proves
the collapse does not swallow a genuinely new undeclared path; cycle 3 proves the dedup
key is the cycle, not the run, so two cycles touching the same stray path each keep their
own record. The minimal GREEN of each earlier cycle is deliberately the cruder rule the
next cycle then sharpens.

## Verified repo facts

*Every fact below was read from the code during hardening — none are asserted from
memory. Locators are function names; grep for them at execution time.*

- **Emit site** (`_stage_and_commit`, `src/tddcli/advance.py`): after `staging.classify`,
  `if classification.outside:` unconditionally calls
  `engine.ledger.event(engine.run["id"], cycle["id"], "undeclared_file_touched",
  json.dumps(classification.outside))`. There is no prior-event check here today — every
  invocation with a non-empty `outside` writes a row.
- **`_stage_and_commit` runs once per phase handler call**: `_handle_test_phase` calls it
  on the RED path (`staging.RED`) and the PIN path (`staging.PIN`); `_handle_impl` calls
  it (`staging.GREEN`); `_handle_refactor` calls it (`staging.REFACTOR`). Each `tdd advance`
  drives exactly one handler, and `--retry` re-drives the same handler — so a standard
  cycle with one persistent outside file emits at RED, GREEN and REFACTOR: **three
  identical rows today**.
- **`outside` is never staged, so it persists across phases**: `staging.paths_for_phase`
  returns `tests + stubs` (RED), `tests` (PIN), or `tests + stubs + implementation`
  (GREEN/REFACTOR) — `classification.outside` appears in none of them. `staging.classify`
  routes a path to `out.outside` when `config.owning_project(rel) is None or owner.root
  not in roots`. Because the file is never committed, `Engine.authored_changes`
  (`machine.py`, = `gitutil.changed_paths` minus `excluded`) keeps returning it every
  phase, and `changed_paths` includes untracked files (confirmed by
  `test_implementation_written_during_red_is_recorded_and_not_committed`, where an
  untracked `sneaky.py` is classified).
- **`classify` produces a stable, sorted `outside` list**: it iterates `sorted(changed)`
  and appends in that order, so the same set of undeclared paths yields byte-identical
  `json.dumps(...)` across phases — a `detail`-equality comparison is sound and needs no
  set re-parsing (though re-parsing is equally valid).
- **In the `repo` fixture a repo-root file is genuinely "outside"**: `backend` has
  `root = "backend"`, and `Config.owning_project` returns `None` for a path no project
  owns (a `.` root counts as depth 0 but there is no `.` project in the fixture). A file
  such as `notes.md` at the worktree root therefore classifies as `outside`. (Note: this
  repo's *own* `tdd.toml` declares `[project.tddcli]` with `root = "."`, whose `owns`
  short-circuits to `True` — so the plan's own edits under `src/` and `tests/` are never
  "outside" during the dogfood run. This only concerns the fixtures under test.)
- **Dedup query model already in the file**: `_check_config_drift` (`advance.py`) does
  `engine.ledger.one("SELECT id FROM integrity_event WHERE run_id = ? AND kind =
  'config_changed' AND detail = ?", ...)` and skips the emit when a row exists.
  `_stub_directive_issued` uses the same `ledger.one(... WHERE cycle_id = ? AND kind =
  ...)` existence shape. The new helper follows these: `engine.ledger.one("SELECT detail
  FROM integrity_event WHERE cycle_id = ? AND kind = 'undeclared_file_touched' ORDER BY
  id DESC LIMIT 1", (cycle["id"],))`. `Ledger.one` returns a `sqlite3.Row | None`
  (`ledger.py`); `Ledger.event` inserts into `integrity_event(run_id, cycle_id, kind,
  detail, at)`.
- **Counting route for tests** — `metrics` (`render.py`) returns, per run,
  `integrity_events` as a `kind -> COUNT(*)` dict (GROUP BY, so a kind with zero rows is
  *absent*, not `0`). Exercised by `test_end_to_end.py`
  (`metrics["result"]["runs"][0]["integrity_events"]["red_first_violation"] == 1`). Tests
  read counts via `run_cli(repo, "metrics")["result"]["runs"][0]["integrity_events"]` and
  use `.get(kind, 0)`.
- **Detail-content route for tests** — `friction_log` (`render.py`) renders each event as
  `- **Event — {kind}:** {detail[:300]}` inside the owning cycle's section
  (`events[e["cycle_id"]]`). `tdd log render --out <path>` writes it; asserting the
  rendered file contains a given `["a.md", "b.md"]` payload proves both the re-emit and
  which cycle carried it.
- **No existing test asserts the *count* of `undeclared_file_touched`**. The string is
  referenced only in `tests/test_artifact_regeneration.py`'s module docstring (describing
  a since-fixed re-flagging of a regenerated spec) and asserted structurally nowhere, so
  adding dedup breaks no existing assertion. `grep -rn undeclared_file_touched src tests`
  confirms the emit site, the `staging` append, one docstring mention, and the
  `c.outside` classify test in `test_config_and_staging.py` — none count events.
- **Driving a full cycle** — the `test_full_red_green_cycle_commits_and_advances`
  pattern in `test_end_to_end.py`: `run start`; write the test + a raising stub; `advance`
  (→ RED, AWAITING_IMPL); overwrite with real impl; `advance` (→ GREEN, AWAITING_REFACTOR);
  `advance` (→ REFACTOR + close sweep + close). Helpers `run_cli`, `write_plan`, `git`
  live in `tests/conftest.py`; `run_cli` returns the parsed envelope dict.
- **The close sweep does not re-emit**: `Engine.sweep` (`machine.py`) runs suites and
  writes `invocation`/`gate_result` rows but never calls `_stage_and_commit`, so the flood
  is purely per-phase-handler, and with empty `lint`/`typecheck` in the fixture the sweep
  is green and the cycle closes cleanly (a repo-root `notes.md` cannot affect pytest
  collection under `backend/tests/`).
- **New test module**: none of the existing test files owns this behaviour; add
  `tests/test_undeclared_dedup.py` (matching the one-file-per-behaviour convention of
  `test_pin_cycles.py`, `test_refactor_cycles.py`, `test_artifact_regeneration.py`). Test
  ids are pytest nodeids `tests/test_undeclared_dedup.py::<func>`.

## Cycle detail

*Expected failure per cycle, derived from the code above; minimum GREEN; each earlier
cycle's crude rule is sharpened by the next.*

### Cycle 1 — an unchanged undeclared file is flagged once per cycle

**Expected RED (probe-verified):** `assert 3 == 1` — with no dedup, RED/GREEN/REFACTOR
each emit the same `undeclared_file_touched` row. Confirmed empirically during hardening:
a single-cycle plan on `repo` with an uncommitted repo-root `notes.md` drove
RED→GREEN→REFACTOR to `complete` and
`metrics[...]["integrity_events"] == {"undeclared_file_touched": 3}`.

Test (`test_unchanged_outside_file_is_flagged_once_per_cycle`): a single-cycle plan on
the `repo` fixture (backend, one test + a raising stub, as in
`test_full_red_green_cycle_commits_and_advances`). After `run start`, write a repo-root
`notes.md` (outside the `backend` root) and leave it uncommitted for the whole cycle.
Drive RED → GREEN → REFACTOR to close. Assert
`run_cli(repo, "metrics")["result"]["runs"][0]["integrity_events"].get(
"undeclared_file_touched", 0) == 1`.

GREEN (minimal, crude): before the emit, skip when *any* `undeclared_file_touched` row
already exists **for this run** — the existence-check shape of `_stub_directive_issued`
/`_check_config_drift`. This passes cycle 1 (one file, one cycle → one row). It is
deliberately too broad — cycles 2 and 3 expose the two ways it is wrong.

### Cycle 2 — a newly-appearing undeclared path re-emits

**Expected RED:** `assert 1 == 2` — cycle 1's existence check emits only for the first
outside path and swallows the later, different set; the rendered friction log lacks the
`["a.md", "b.md"]` payload.

Test (`test_a_new_undeclared_path_re_emits`): same single-cycle harness. After `run
start`, create repo-root `a.md`; drive `advance` to RED (emits `["a.md"]`). Before the
GREEN advance, also create repo-root `b.md`, so the GREEN classification's `outside` is
`["a.md", "b.md"]` (sorted). Advance through GREEN and REFACTOR. Assert the
`undeclared_file_touched` count is `2`, and `tdd log render` output contains an event
line carrying `["a.md", "b.md"]` (the changed set was recorded).

GREEN: replace the existence check with a **changed-since-last** comparison — still
run-scoped to stay minimal, mirroring `_check_config_drift`'s run key: fetch the *last*
`undeclared_file_touched` `detail` on the run (`... WHERE run_id = ? AND kind = ... ORDER
BY id DESC LIMIT 1`) and skip only when it equals the current `json.dumps(outside)`. Emit
on first occurrence or on any change. (Keeping the key run-scoped here is intentional; it
is what cycle 3 sharpens — do not pre-emptively scope to the cycle, or cycle 3 loses its
RED.)

### Cycle 3 — the dedup is scoped to the cycle, not the run

**Expected RED:** `assert 1 == 2` — cycle 2's run-scoped comparison dedups the second
cycle's identical path against the first cycle's row, so only one event exists across the
run.

Test (`test_dedup_is_per_cycle_not_per_run`): a **two-cycle** plan on `repo` (two
independent backend behaviours, e.g. `add` then `subtract`, following the two-cycle plan
in `test_end_to_end.py`). Create repo-root `shared.md` after `run start` and leave it
uncommitted across *both* cycles. Drive cycle 1 to close, then cycle 2 to close. Assert
the run's `undeclared_file_touched` count is `2` (one per cycle) — each cycle's section
records that it touched the stray path.

GREEN: narrow the comparison's key from `run_id` to `cycle_id` (`... WHERE cycle_id = ?
AND kind = ... ORDER BY id DESC LIMIT 1`, using `cycle["id"]`). Cycle 1 and cycle 2 still
hold: within one cycle the last-seen detail is per-cycle, and a changed set still
re-emits.

REFACTOR (declared `commit_refactor`): extract the last-recorded-`outside` lookup into a
small module-level helper (e.g. `_last_outside_emitted(engine, cycle) -> str | None`)
beside `_stub_directive_issued`, and call it from `_stage_and_commit`. The three new
tests plus the existing suite are the guard; behaviour is unchanged.

## Deliberate scope cuts (do not build)

- **Render-time collapsing** (`friction_log`/`progress` folding duplicate events, with or
  without an `(×N)` count). Rejected: the emit-time fix keeps the ledger free of the
  redundant rows, so no projection needs to learn to collapse them. Do not add
  dedup logic to `render.py`.
- **Retry-path and close-sweep-lap dedup as separate cycles.** They are covered for free:
  a `--retry` re-drives the same handler and hits the same guarded emit, and the close
  sweep never emits at all (`Engine.sweep` does not call `_stage_and_commit`). No
  dedicated cycle — adding one would pass on arrival once cycle 3 lands.
- **Backfilling or de-duplicating rows already written by prior runs.** The ledger is
  append-only (R13); this changes only what future emits write. No migration.
- **Widening dedup to other integrity kinds** (`implementation_during_red`,
  `stub_adopted`, `stale_artifact`, …). Each has its own emit cadence and meaning; leave
  them exactly as they are.
- **A new event recording that a duplicate was suppressed.** Silence is correct here —
  the whole point is fewer rows; do not emit a `undeclared_file_deduped` marker.

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

The branch `feat/55-undeclared-event-dedup` already exists — it was created at hardening
and carries this plan's commit. Check it out; if it has grown unrelated work, stop and ask.

    git checkout feat/55-undeclared-event-dedup         # exists: created at hardening, carries this plan
    tdd doctor                                          # must report healthy: true
    tdd run start --plan tasks/issue-55-undeclared-file-event-dedup.md

`tdd doctor` must be green first: if it reports "worktree clean" failing on *other*
uncommitted `tasks/issue-*.md` files (sibling plans not part of this work), commit, stash,
or gitignore them before `run start`.

Then repeat until done: read `next_action.verb`, do exactly what it says, run
`tdd advance`. Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit
it, and raise the PR — see Done-criteria below.

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
`tdd log render --out tasks/friction-logs/issue-55-undeclared-event-dedup-friction.md`
and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped —
and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-55-undeclared-event-dedup-friction.md
    git commit -m "docs: friction log for issue-55-undeclared-event-dedup"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes
the branch and opens the PR against `main`. Do not push or call the GitHub API by hand.
If a gate fails, fix it and re-run the skill — a failed gate is work, not a reason to hand
back.
