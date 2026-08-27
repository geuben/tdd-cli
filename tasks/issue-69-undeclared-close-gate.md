---
closes: 69
cycles:
  - n: 1
    project: tddcli
    title: "an uncommitted flagged file blocks the run at close"
    test: "tests/test_undeclared_close_gate.py::test_uncommitted_flagged_file_blocks_at_close"
    files: ["src/tddcli/machine.py", "src/tddcli/advance.py"]
    commit_red: "test: an uncommitted flagged file blocks the run at close"
    commit_green: "feat: run-close gate blocks on undeclared_file_touched paths"

  - n: 2
    project: tddcli
    title: "a flagged file committed during the run does not block"
    test: "tests/test_undeclared_close_gate.py::test_a_committed_flagged_file_does_not_block"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: a committed flagged file does not block at close"
    commit_green: "feat: close gate blocks only on paths still dirty in the worktree"

  - n: 3
    project: tddcli
    title: "a flagged file that vanished is reported, not blocked"
    test: "tests/test_undeclared_close_gate.py::test_a_vanished_flagged_file_is_reported_not_blocked"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: a vanished flagged file is reported, not blocked"
    commit_green: "feat: emit undeclared_file_dropped for flagged files that vanished"
---

# Issue #69 — undeclared_file_touched is advisory; flagged files can be silently dropped at run close

https://github.com/geuben/tdd-cli/issues/69
Task file: `tasks/issue-69-undeclared-close-gate.md`

## Context

`undeclared_file_touched` is advisory: the event fires when a cycle touches a file outside
its project roots, the run proceeds, and nothing later enforces that the flagged file was
committed. Observed in a real agent-driven run: a documentation file read by one of the
plan's tests was edited during the run, the event fired repeatedly across cycles, and the
file still never shipped — the working-tree edit was silently lost between run close and the
PR. A sibling run the same week committed its equivalent edit fine, so the outcome is
executor luck, not policy.

This issue adds a **run-close gate**. When the last declared cycle closes, the tool gathers
the cumulative set of `undeclared_file_touched` paths for the run and compares it against the
worktree:

- a flagged path **still dirty/untracked** → a typed blocker `undeclared_file_uncommitted`;
  the run ends `blocked` instead of `complete`, listing the paths. A human resolves it by
  committing the files and `tdd resume --unblock --note ...`, or by unblocking with a
  discard justification. The event becomes a gate that **fails closed** instead of a log line
  someone must remember to grep.
- a flagged path **committed during the run** → fine, no block (executor luck becomes an
  explicit allow).
- a flagged path **neither committed nor present any more** → an `undeclared_file_dropped`
  integrity event, so a silent drop is at least *visible* in the run summary, and the run
  completes.

### Dependency — land after #70 (sequencing, not code)

This work has **no code dependency** on #70 (ancillary files): the gate reads
`undeclared_file_touched` events (which already exist, deduped per-cycle by #55/#61) and
inspects the worktree; it never references `ancillary_files` or `Classification.ancillary`.
It compiles, tests, and merges without #70.

But it **must be sequenced after #70** for soundness. Without the `ancillary_files`
vocabulary, a plan that legitimately touches a cross-project file (a regenerated client's
import site, a companion doc) has no way to *declare* it, so every such file fires
`undeclared_file_touched` — and this gate would then block every legitimate cross-project run.
With #70 merged first, declared paths never fire the event, so this gate blocks only on
*genuinely* undeclared drift, which is its whole purpose. **Do not merge #69 before #70.**

The executor's own run of *this* plan will not trip the new gate: every file it touches
(`machine.py`, `advance.py`, `tests/...`, the friction log) lives inside the single `tddcli`
project root `.`, so nothing classifies as `outside` and no `undeclared_file_touched` fires.

## Verified repo facts

*Every fact below was read out of the codebase during hardening — none are asserted from
memory. Several were probed empirically (noted inline). Locators are real names and paths.*

- **This repo is a single project.** `tdd.toml` declares `[project.tddcli]`, `root = "."`,
  `adapter = "pytest"`, `test_paths = ["tests/"]`. Contract paths are repo-root-relative. The
  integration cycles run against the **synthetic** `repo` fixture in `tests/conftest.py`
  (a single-project repo rooted at `backend`, where a repo-root file like `notes.md` is
  genuinely `outside`) — the same harness `tests/test_undeclared_dedup.py` uses.
- **The event and its detail.** `_stage_and_commit` in `src/tddcli/advance.py` emits
  `undeclared_file_touched` with `detail = json.dumps(classification.outside)` — a JSON list
  of worktree-root-relative paths — gated on `if classification.outside:` and deduped per
  cycle via `_last_outside_emitted` (issue #55). The gate must **not** touch this emission;
  it only *reads* the events afterward.
- **Reading the events for a run.** `Ledger.all("SELECT ... FROM integrity_event WHERE
  run_id = ? AND kind = 'undeclared_file_touched'", (run_id,))` returns every such event;
  each `detail` is a JSON list. The cumulative flagged set is the union of the parsed lists.
  (`render.py` already reads `integrity_event WHERE run_id = ?` this way.)
- **Run completion seam.** `Engine.close_cycle(cycle_row)` (`src/tddcli/machine.py`)
  transitions the cycle to `CLOSED`, then `nxt = next((c for c in self.declared if c.ordinal
  > cycle_row["ordinal"]), None)`; when `nxt is None` it does `self.ledger.update("run",
  self.run["id"], ended_at=now(), outcome="complete")` and returns `None`. The **advance
  final handler** (`advance.py`, the block after `nxt = engine.close_cycle(cycle)` where
  `if nxt is None:` returns the `Verb.COMPLETE` envelope) is where the gate is injected —
  after `close_cycle` returns `None`, before the COMPLETE envelope. `sha` and `regenerated`
  are in scope there. **Do not change `close_cycle`'s return contract**; the gate lives in the
  handler.
- **Blocker machinery (mirror it).** `cmd_blocker` (`src/tddcli/cli.py`) inserts into the
  `blocker` table (`run_id, cycle_id, kind, detail, at` — `kind` is free `TEXT`, no CHECK/FK)
  and does `ledger.update("run", run["id"], ended_at=now(), outcome="blocked")`, returning an
  envelope with `phase: "BLOCKED"` and `NextAction(Verb.BLOCKED, "...`tdd resume --unblock
  --note ...`")`. `Verb.BLOCKED` is in `TERMINAL_VERBS` (`src/tddcli/envelope.py`), so
  `next_action.terminal` is `True`. The gate replicates this insert+update directly (it is
  not a CLI command). **`BLOCKER_KINDS` (`cli.py`) need not gain the new kind** — it validates
  only the manual `tdd blocker` command, and the `blocker` table accepts any string; the gate
  writes the row itself. (Adding it there is a harmless optional courtesy, not required, and
  is left out to keep the change minimal.)
- **Resolution path already exists.** `cmd_resume --unblock --note` (`cli.py`) requires the
  note, clears `outcome`, inserts a `human_intervention`, then `open_cycle` returns `None`
  (all cycles closed) so it returns `Verb.COMPLETE`. So after the gate blocks, the human
  commits (or discards) the files and `tdd resume --unblock --note ...` completes the run.
  `test_blocker_releases_the_run_and_a_human_can_unblock` in `tests/test_end_to_end.py` is the
  template for this shape.
- **Git helpers (probed empirically during hardening).** `gitutil.dirty_paths(worktree)`
  returns worktree-root-relative paths of tracked modifications *and* untracked files (via
  `git status --porcelain=v1 -uall`); `gitutil.tracked_at_head(worktree, paths)` returns which
  of `paths` exist in `HEAD`. Verified in a scratch git repo: an untracked root-level
  `notes.md` → `dirty_paths` includes `"notes.md"`, `tracked_at_head(["notes.md"])` is empty;
  after committing it → `dirty_paths` drops it, `tracked_at_head` returns `{"notes.md"}`;
  a deleted-untracked file appears in neither. So the partition is exactly:
  - `p in dirty` → **uncommitted** (block),
  - `p in tracked and p not in dirty` → **committed** (ok),
  - `p not in dirty and p not in tracked` → **vanished** (dropped event).
  Both `dirty` strings and the event `detail` strings are worktree-root-relative, so plain
  set membership matches — confirmed with the same relativization the classifier uses.
- **`Engine`** exposes `self.ledger`, `self.run`, `self.config`, `self.worktree` (used by
  `_stage_and_commit` and the sweep). The gate method reads `self.worktree` and
  `self.run["id"]` and calls `gitutil` — no new state.
- **`Ledger.event(run_id, cycle_id, kind, detail)`** (`src/tddcli/ledger.py`) inserts an
  `integrity_event`; the gate uses it with `cycle_id=None` (run-scoped) for
  `undeclared_file_dropped`, exactly as `baseline_amended` is emitted run-scoped in `cli.py`.
- **Metrics/events readout for tests.** `run_cli(repo, "metrics")["result"]["runs"][0][
  "integrity_events"]` is a `{kind: count}` dict (used by `tests/test_undeclared_dedup.py`);
  the envelope's `next_action.verb` is `"blocked"`/`"complete"` and `next_action.terminal` is
  a bool. Cycles assert on these.
- **Baseline for this repo is `{"tddcli": 0}`** — suite green today. `run start` captures it;
  anything else at arrival means a moved branch — stop.
- **Test-side blast radius — no existing test breaks (verified).** The gate flips a run's
  outcome to `blocked` whenever a flagged path is uncommitted at close. The only existing
  tests that end a run with an uncommitted *outside* file are the three in
  `tests/test_undeclared_dedup.py` (`test_unchanged_outside_file_is_flagged_once_per_cycle`,
  `test_a_new_undeclared_path_re_emits`, `test_dedup_is_per_cycle_not_per_run`). Each asserts
  **only** `undeclared_file_touched` event counts (and one renders the friction log for a
  substring) — all **gate-invariant**: the gate adds a `blocker` row, never removes an
  `undeclared_file_touched` event, and emits `undeclared_file_dropped` only for *vanished*
  paths (these are dirty, not vanished). Confirmed against the code: `metrics`
  (`render.py`, `metrics(...)`) enumerates runs with `SELECT * FROM run WHERE worktree_path=?
  ORDER BY id` — **no outcome filter** — so a blocked run still appears at `runs[0]` and its
  `integrity_events` are unchanged. Those three tests therefore keep passing; they just now
  incidentally end on a blocked run. **They must NOT be edited or added to `modifies_tests`.**
  The `tests/test_artifact_regeneration.py` completion tests are also safe: their artifact
  path (`schema/openapi.json`) is committed by the regenerate hook before close (they assert
  it is clean), so the gate classifies it as *committed*, not blocking.

## Cycle detail

*Each RED genuinely fails given the previous GREEN; minimum GREEN; resist later cycles.*

The gate lives in one new `Engine` method — call it `close_undeclared_gate(cycle) -> list[str]`
— that returns the paths that must block (and, from cycle 3, emits the dropped event as a
side effect). The three cycles refine that one method; cycle 1 also adds the handler wiring.

### Cycle 1 — an uncommitted flagged file blocks at close

**Expected RED (probe-verified):** the run **completes** — `next_action.verb == "complete"`,
`terminal: true` — because no gate exists. The test asserts `verb == "blocked"` and a
`undeclared_file_uncommitted` blocker row, both of which fail. **Confirmed empirically during
hardening**: a throwaway probe drove exactly this shape (single-cycle plan, `notes.md` written
at the repo root and never committed, advance RED → GREEN → REFACTOR) and observed
`FINAL verb: complete`, `integrity_events: {undeclared_file_touched: 1, ...}`, and
`git status` showing `?? notes.md` (untracked, i.e. dirty) at close — precisely the pre-gate
state this cycle turns into a block.

**Harness note:** writing the production file inline during RED (as `test_undeclared_dedup.py`
does — `calc.py` = `raise NotImplementedError`) also emits an `implementation_during_red`
event. That is expected noise from the synthetic inner plan and does not affect these cycles'
assertions, which target the final `verb`, the `undeclared_file_uncommitted` blocker, and the
`undeclared_file_dropped` event specifically. Do not try to suppress it.

Test (`test_uncommitted_flagged_file_blocks_at_close`, new
`tests/test_undeclared_close_gate.py`, harness = `test_undeclared_dedup.py`): a single-cycle
plan for the synthetic `backend` project; register, run start, write `notes.md` at the repo
root (fires `undeclared_file_touched` on the first advance), write the RED test + stub, then
advance RED → GREEN → REFACTOR. Leave `notes.md` **uncommitted**. Assert:
- the final advance envelope has `next_action["verb"] == "blocked"` and
  `next_action["terminal"] is True`;
- the run outcome is `blocked` (e.g. via a `blocker` row of kind `undeclared_file_uncommitted`
  whose detail names `notes.md`, or via `metrics`/`status` — confirm the exact readout at
  execution time).

GREEN (minimal, crude on purpose): add `Engine.close_undeclared_gate(self, cycle)` that unions
the `undeclared_file_touched` details for the run and returns **all** flagged paths. In the
advance final handler, after `nxt = engine.close_cycle(cycle)` returns `None`:
```python
blocking = engine.close_undeclared_gate(cycle)
if blocking:
    engine.ledger.insert(
        "blocker", run_id=engine.run["id"], cycle_id=cycle["id"],
        kind="undeclared_file_uncommitted", detail=json.dumps(blocking), at=now(),
    )
    engine.ledger.update("run", engine.run["id"], outcome="blocked")
    return Envelope(
        run={... "phase": "BLOCKED"},
        result={"kind": "undeclared_file_uncommitted", "paths": blocking, "commit": sha},
        next_action=NextAction(
            Verb.BLOCKED,
            f"Run reached its last cycle but {len(blocking)} flagged file(s) are uncommitted: "
            f"{blocking}. Commit them, or `tdd resume --unblock --note ...` to discard.",
        ),
    )
# else: existing COMPLETE envelope
```
Do **not** filter by worktree state yet (cycle 2) and do **not** emit a dropped event (cycle
3). The `outcome="blocked"` override after `close_cycle` set `"complete"` is intentional — a
blocked run legitimately keeps its `ended_at`, exactly as `cmd_blocker` leaves it.

### Cycle 2 — a committed flagged file does not block

**Expected RED:** the run **blocks** — cycle 1's crude gate returns every flagged path
regardless of whether it was committed, so a flagged-then-committed file still trips the
blocker. The test asserts `verb == "complete"`; it gets `"blocked"`.

Test (`test_a_committed_flagged_file_does_not_block`): same shape, but after the first advance
(which fires the event on the dirty `notes.md`), **commit `notes.md` manually** with the
conftest `git` helper (`git(repo, "add", "notes.md")`, `git(repo, "commit", "-m", "manual")`)
before the remaining advances. Advance to close. Assert `next_action["verb"] == "complete"`
and no `undeclared_file_uncommitted` blocker row.

GREEN: in `close_undeclared_gate`, restrict the return to flagged paths still dirty —
`dirty = gitutil.dirty_paths(self.worktree); return sorted(p for p in flagged if p in dirty)`.
A committed path is not dirty, so it drops out and the run completes. Do not add the dropped
event yet.

### Cycle 3 — a vanished flagged file is reported, not blocked

**Expected RED:** the run **completes** (cycle 2 already excludes non-dirty paths from
blocking), but there is **no** `undeclared_file_dropped` event. The test asserts the event is
present; it is absent.

Test (`test_a_vanished_flagged_file_is_reported_not_blocked`): write `notes.md`, advance once
(event fires), then **delete `notes.md`** (`(repo / "notes.md").unlink()`) before the
remaining advances. Advance to close. Assert `next_action["verb"] == "complete"` **and**
`run_cli(repo, "metrics")["result"]["runs"][0]["integrity_events"].get(
"undeclared_file_dropped", 0) >= 1` (confirm the metrics-events readout at execution time).

GREEN: in `close_undeclared_gate`, compute `tracked = gitutil.tracked_at_head(self.worktree,
flagged)` and `dropped = sorted(p for p in flagged if p not in dirty and p not in tracked)`;
if `dropped`, `self.ledger.event(self.run["id"], None, "undeclared_file_dropped",
json.dumps(dropped))`. Keep returning the dirty-only blocking list unchanged.

## Deliberate scope cuts (do not build)

- **The last-cycle-skipped completion path is not gated.** A run whose final cycle is closed
  via `tdd cycle skip` completes through `cmd_cycle_skip` in `cli.py`, a separate path that
  does not call `close_undeclared_gate`. Gating that path too is a straightforward follow-up
  (a second call site), but it is out of scope here — the observed failure is on the normal
  close path. Note it in the friction log if you touch that area.
- **No re-check on resume.** After the gate blocks, `tdd resume --unblock --note` completes
  the run without re-running the gate — deliberately: "commit the files" and "discard with a
  recorded justification" are *both* sanctioned resolutions (the note records which), so the
  human override is trusted. Re-verifying on resume is a possible hardening, not this issue.
- **No tool-assisted `[ancillary]` commit as a resolution.** The issue floats a tool-assisted
  commit of the flagged files; that overlaps with #70's staging and is its own change. The
  resolution here is manual commit (or discard) then `resume --unblock`.
- **Do not touch the `undeclared_file_touched` emission or its #55 dedup.** The gate only
  reads those events.
- **Do not add the new kind to `BLOCKER_KINDS`.** It validates only the manual `tdd blocker`
  command; the gate writes the `blocker` row directly and the column is free text. (Optional,
  omitted to keep the change minimal.)
- **No new ledger column or schema bump.** Everything reuses `integrity_event` and `blocker`.
- **README/PRD documentation** of the gate and the `undeclared_file_uncommitted` /
  `undeclared_file_dropped` kinds is a post-run doc follow-up, not a cycle (see
  Done-criteria).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not
ask the user to start the run. `tdd run start` records which model is executing, resolved
from your own session; a run started by anyone else attributes this work to the wrong agent.

**Referee rule:** run the *released* `tdd` **0.7.0**, never this working tree's editable
install. Do not work in a shell with this repo's `.venv` activated. Verify before starting:
`tdd --version` → **0.7.0**, and confirm `which tdd` is **not**
`/Volumes/SSD/repos/tdd-cli/.venv`. A separate 0.7.0 clone is fine. This plan uses only
0.7.0-supported front-matter keys and adds no ledger schema, so the referee needs nothing new.

**Sequencing:** #70 (ancillary files) must be merged to `main` before this lands — see the
Dependency note above. Branch this work from an up-to-date `main` that already contains #70.

    git checkout -b feat/69-undeclared-close-gate     # first, before anything else
    tdd doctor                                        # must report healthy: true
    tdd run start --plan tasks/issue-69-undeclared-close-gate.md

If the branch already exists, do not force-checkout and do not pick another name: check it
out only if it carries this plan's commit and no unrelated work, otherwise stop and ask.
`tdd doctor` must be green first: if it fails on *other* uncommitted `tasks/issue-*.md` files
(sibling plans not part of this work), commit, stash, or gitignore them before `run start`.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it,
and raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` —
  the tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. Expected
  baseline for this repo: `{"tddcli": 0}` — anything else means a moved branch; stop.
- All three cycles are **standard** — every RED fails before implementation, so no
  `run_sensitivity_check` is expected. Verbs this plan can hit: `resolve_blocker` →
  `tdd blocker --kind --detail` (kinds: `plan_defect`, `tooling`, `regression`,
  `pre_existing_failure`); `confirm_cycle_applicable` on a cycle the codebase has outgrown →
  `tdd cycle skip --reason`. This plan declares no `annotation_keys`. Your own run will not
  trip the new close gate (all touched files are inside the `tddcli` project root).

## Done-criteria

**Before finishing:** run
`tdd log render --out tasks/friction-logs/issue-69-undeclared-close-gate-friction.md` and
`tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and
every integrity event. Do not narrate what the ledger already records.

Then the documentation follow-up, committed as ordinary commits after the run is terminal:
in `README.md` (and PRD if it enumerates integrity events / blocker kinds), document the
run-close gate and the two new kinds — `undeclared_file_uncommitted` (blocker: a flagged path
still uncommitted at close) and `undeclared_file_dropped` (event: a flagged path that vanished
without being committed) — and the resolve-by-commit-or-discard-then-`resume --unblock` path.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-69-undeclared-close-gate-friction.md
    git commit -m "docs: friction log for issue-69-undeclared-close-gate"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back. The PR
description should note it must merge after #70.
