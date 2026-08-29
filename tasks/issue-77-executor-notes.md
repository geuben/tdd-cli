---
closes: 77
cycles:
  - n: 1
    project: tddcli
    title: "tdd note attaches to the open cycle with its phase"
    test: "tests/test_executor_notes.py::test_note_attaches_to_the_open_cycle_with_its_phase"
    files: ["src/tddcli/ledger.py", "src/tddcli/cli.py"]
    commit_red: "test: tdd note stores a cycle-scoped, phase-stamped row"
    commit_green: "feat: tdd note — executor-narrative rows in a new note table"

  - n: 2
    project: tddcli
    title: "a v7 ledger is upgraded in place to v8"
    test: "tests/test_executor_notes.py::test_v7_ledger_is_upgraded_in_place_to_v8"
    files: ["src/tddcli/ledger.py"]
    commit_red: "test: reopening a v7 ledger yields the note table and version 8"
    commit_green: "feat: schema v8 — note table, empty MIGRATIONS[7] entry"

  - n: 3
    project: tddcli
    title: "a note after the run ends is run-level on the latest run"
    test: "tests/test_executor_notes.py::test_note_after_run_end_is_run_level_on_the_latest_run"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: post-terminal tdd note lands run-level, no active run required"
    commit_green: "feat: tdd note falls back to the latest run after the run ends"

  - n: 4
    project: tddcli
    title: "cycle notes render as blockquotes inside their cycle section"
    test: "tests/test_executor_notes.py::test_cycle_notes_render_as_blockquotes_in_their_cycle"
    files: ["src/tddcli/render.py"]
    commit_red: "test: a cycle note renders as a phase-stamped blockquote"
    commit_green: "feat: friction log renders cycle notes as blockquote claims"

  - n: 5
    project: tddcli
    title: "run-level notes render in an Executor narrative section"
    test: "tests/test_executor_notes.py::test_run_level_notes_render_in_the_executor_narrative_section"
    files: ["src/tddcli/render.py"]
    commit_red: "test: run-level notes render under ## Executor narrative"
    commit_green: "feat: Executor narrative section for run-level notes"

  - n: 6
    project: tddcli
    title: "no Executor narrative section without run-level notes"
    test: "tests/test_executor_notes.py::test_no_narrative_section_without_run_level_notes"
    files: ["src/tddcli/render.py"]
    commit_red: "test: the narrative section is omitted when no run-level note exists"
    commit_green: "feat: suppress the empty Executor narrative section"

  - n: 7
    project: tddcli
    title: "an integrity event's envelope nudges for a note"
    test: "tests/test_executor_notes.py::test_integrity_event_envelope_nudges_for_a_note"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: red_first_violation envelope suggests tdd note"
    commit_green: "feat: soft note nudge on integrity-event envelopes"

  - n: 8
    project: tddcli
    title: "the nudge stops once the cycle has a note"
    test: "tests/test_executor_notes.py::test_nudge_stops_once_the_cycle_has_a_note"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: a noted cycle is not nudged again"
    commit_green: "feat: silence the note nudge once the cycle carries a note"

  - n: 9
    project: tddcli
    title: "the terminal advance envelope invites a closing note"
    test: "tests/test_executor_notes.py::test_terminal_advance_invites_a_closing_note"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: COMPLETE via advance mentions the closing tdd note"
    commit_green: "feat: closing-narrative prompt on the terminal advance envelope"

  - n: 10
    project: tddcli
    title: "the terminal skip envelope invites a closing note"
    test: "tests/test_executor_notes.py::test_terminal_skip_invites_a_closing_note"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: COMPLETE via final-cycle skip mentions the closing tdd note"
    commit_green: "feat: closing-narrative prompt on the terminal skip envelope"
---

# Issue #77 — friction log: an executor-narrative channel

https://github.com/geuben/tdd-cli/issues/77
Task file: `tasks/issue-77-executor-notes.md`

## Context

The friction log is pure telemetry — events, verdicts, commits, timings — with no field
where the executor can say *why* something happened. Reviews of machine-generated logs had
to reverse-engineer every judgement call from event lines and git archaeology; the
executor's reasoning existed at the time and was discarded. This plan adds an
executor-notes channel: a `tdd note "<text>"` command scoped to the current cycle and
phase (run-level once the run has ended), rendered in the friction log visually distinct
from telemetry, with a **soft** nudge when high-value integrity events fire and a **soft**
closing-narrative prompt on the terminal envelope. Notes are free text and unverified by
design — claims, not measurements — captured at the moment the intent exists. (Distinct
from #58's authored-at-plan-time metadata; this is authored-at-run-time narrative.)

## Design decisions (locked)

- **Storage is a new `note` table** (`run_id NOT NULL`, `cycle_id` nullable, `phase`
  nullable, `text`, `at`), not reuse of `annotation`. Decided by codebase evidence:
  `annotation` has no phase column, and its keys feed the `missing_annotations` close
  gate (`Engine.missing_annotations` in `machine.py`) — a reserved `note` key would
  spuriously satisfy a plan-declared `annotation_keys: ["note"]`. PRD draws the same
  line: annotations are *keyed judgement fields*; notes are narrative.
- **Schema v8 with an empty migration entry.** `SCHEMA_VERSION = 8`,
  `MIGRATIONS[7] = ""` — the new-table precedent (v1→v4 entries are empty strings;
  `CREATE TABLE IF NOT EXISTS` in the idempotent SCHEMA script covers it). The
  migration loop indexes `MIGRATIONS[stored]`, so the entry is mandatory, and the
  existing `test_older_ledger_is_migrated_forward` walk enforces it.
- **Event prompting is a soft nudge, never a gate** (user decision,
  AskUserQuestion 2026-08-29). Seam: the central `_reply` helper in `advance.py` — the
  nudge-worthy cycle-scoped events (`red_first_violation`, `undeclared_file_touched`,
  `implementation_during_red`) are all recorded inside the advance flow, whose envelopes
  all pass through `_reply`. When the open cycle has at least one event of those kinds
  and **zero** notes, one sentence is appended to `next_action.detail` suggesting
  `tdd note "<why>"`. It repeats on subsequent envelopes until a note exists or the
  cycle closes — deliberate: silencing per-envelope would need nudge-tracking state.
- **Run close asks softly for a narrative** (user decision, same round). Both terminal
  `COMPLETE` sites — `_handle_refactor`'s all-cycles-closed return in `advance.py` and
  `cmd_cycle_skip`'s final-cycle return in `cli.py` — extend their message: closing note
  first (hardest cycle and why, plan inaccuracies, deviations), then `tdd log render`.
  Never blocking; `next_action.terminal` stays `true`.
- **`tdd note` scoping**: the open cycle of the run if one exists (stamped with the
  cycle's current `phase`); otherwise run-level (`cycle_id`/`phase` NULL). After the run
  ends, `_context(require_run=False)` plus the latest-run-for-worktree fallback —
  verbatim the `cmd_log_render` precedent — so the closing narrative is writable after
  the terminal advance (the run row is already `ended_at`-stamped by
  `Engine.close_cycle` before the COMPLETE envelope is emitted).
- **`tdd note` next_action mirrors `cmd_status`**: live run →
  `Verb.REFACTOR_OR_ADVANCE` with a "resume the phase in progress" message; ended run →
  `Verb.COMPLETE` pointing at `tdd log render`. No new verb; `VERB_SET_VERSION`
  untouched.
- **Rendering**: cycle notes render inside their cycle section, after annotations, as
  `> **note** _(during <PHASE>)_: <text>` — blockquote = visually distinct claim.
  Run-level notes render in a `## Executor narrative` section between the cycle
  sections and Blockers, opened by the caption line
  `_Claims from the executor, unverified by design._`, one blockquote per note. The
  section is omitted entirely when no run-level note exists.

## Verified repo facts

*Anchors are symbol names — grep for them; no line numbers anywhere in this plan.*

- **Annotation machinery, read from code.** `cmd_annotate` (`cli.py`) inserts keyed rows
  with nullable `cycle_id`; `friction_log` (`render.py`) selects only
  `WHERE cycle_id = ?` — run-level annotations never render, a separate deliberate gap
  this plan does not touch. `Engine.missing_annotations` gates cycle close on
  plan-declared keys, which is why notes must not be annotation rows.
- **Ledger**: `SCHEMA_VERSION = 7`; `MIGRATIONS` keyed by from-version with empty
  strings for new-table versions; `Ledger.__init__` runs the idempotent SCHEMA script,
  then walks `MIGRATIONS[stored]` up to `SCHEMA_VERSION`, then rewrites
  `meta.schema_version`. `PRAGMA foreign_keys=ON` — note rows staged by render tests
  must use real `run_id`/`cycle_id` values from the fixture's ledger.
- **Event sites**: `red_first_violation` is recorded in `_handle_test_phase`
  (`advance.py`, the `passed_all` branch) which then transitions to
  `SENSITIVITY_REQUIRED` and replies through `_reply`; `undeclared_file_touched` and
  `implementation_during_red` are recorded in `_stage_and_commit`'s classification
  block, also inside the advance flow. All advance envelopes funnel through `_reply`.
- **Terminal sites**: `Engine.close_cycle` marks the run
  `ended_at`/`outcome="complete"` and returns `None`; `_handle_refactor` then emits
  `Verb.COMPLETE` ("All declared cycles are complete. Run `tdd log render`.").
  `cmd_cycle_skip` has its own final-cycle COMPLETE ("Final cycle skipped; run
  complete."). No test asserts either message text, and every existing
  `next_action.detail` assertion in the suite is a substring `in` check on other flows —
  `modifies_tests` is empty for every cycle.
- **Test harness inherited verbatim from passing tests.** The conftest `repo` fixture +
  `run_cli`/`write_plan`/`git` helpers; `tests/test_sensitivity_evidence.py` drives the
  exact single-cycle backend plan (`PLAN`/`TEST_ADD`/`CALC_WORKING`) this plan's e2e
  cycles reuse, including the pass-on-arrival → sensitivity → refactor → terminal
  advance walk; `tests/test_progress.py` constructs `Ledger(...)` directly under the
  conftest `ledger_home` fixture for staging rows.
- **Empirical probe (deleted, tree clean).** A throwaway test calling
  `run_cli(repo, "note", "why it happened")` fails today with
  `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` — argparse
  rejects the unknown subcommand (`invalid choice: 'note'`) to stderr, stdout stays
  empty, and `run_cli`'s `json.loads` fails in-test. A legitimate RED; no stubs needed
  (the test imports only conftest helpers and `Ledger`, which exist), so
  **no cycle declares `stub_expected`**.
- **Suite is green now**: 451 passed, 1m46s, on `main` at `0fb4459`. Expected
  `run start` baseline: `{"tddcli": 0}` — anything else means a moved branch; stop.
- **Lint is ruff-only** (`tdd.toml`: `lint = ["uv run ruff check"]`), single project
  `tddcli` rooted at `.`.

## Cycle detail

*Single project `tddcli`; every test lives in the new `tests/test_executor_notes.py`,
built on the conftest `repo` fixture and the `test_sensitivity_evidence.py` plan/flow
constants. Minimum GREEN throughout.*

**Cycle 1 — `tdd note` attaches to the open cycle with its phase.** Test: register and
start the single-cycle backend plan (sensitivity-evidence pattern); the run opens cycle 1
in `AWAITING_TEST`. `run_cli(repo, "note", "the fixture assumption was wrong")` → assert
the envelope is `ok`, then open `Ledger(gitutil.repo_identity(repo))` and assert the one
`note` row has this run's id, a non-NULL `cycle_id`, `phase == "AWAITING_TEST"`, and the
text. *EXPECTED FAILURE (probed):* `json.decoder.JSONDecodeError: Expecting value: line 1
column 1 (char 0)` — argparse rejects the unknown subcommand. *GREEN:* `ledger.py` — add
the `note` CREATE TABLE to SCHEMA (no version bump yet; cycle 2 demands it); `cli.py` —
`cmd_note` (`_context()`, `ledger.open_cycle(run["id"])`, insert
run/cycle/phase/text/at, reply per the locked next_action decision) and the
`note` subparser with one positional `text` argument. Production targets: `SCHEMA` /
`cmd_note` / `build_parser`.

**Cycle 2 — a v7 ledger upgrades in place to v8.** Test: construct `Ledger(tmp_path /
"somerepo")` under `ledger_home`, then via its connection `UPDATE meta SET value='7'
WHERE key='schema_version'` and `DROP TABLE note`, close; reopen `Ledger(...)`; assert
`SELECT * FROM note` succeeds (returns `[]`) **and** the recorded `schema_version` is
`8`. *EXPECTED FAILURE:* the reopened ledger rewrites version `7`
(`SCHEMA_VERSION` is still 7) — `AssertionError` on the `== 8` comparison (the table
itself is recreated by the idempotent SCHEMA script). *GREEN:* `SCHEMA_VERSION = 8`,
`MIGRATIONS[7] = ""` with the customary comment. The existing
`test_older_ledger_is_migrated_forward` keeps the walk honest — a bump without the
entry raises `KeyError` there. Production target: `ledger.py` schema constants.

**Cycle 3 — a note after the run ends is run-level on the latest run.** Test: start the
single-cycle plan, `run_cli(repo, "cycle", "skip", "--reason", "probe")` → terminal
COMPLETE, run ended. Then `run_cli(repo, "note", "closing narrative")` → assert `ok` and
that the `note` row carries the run's id with `cycle_id IS NULL`. *EXPECTED FAILURE:*
cycle 1's minimal `_context()` requires an active run — the envelope is the
`no active run in this worktree` failure, so the `ok` assertion fails
(`AssertionError`). *GREEN:* `cmd_note` switches to `_context(require_run=False)` plus
the `cmd_log_render` latest-run fallback; no open cycle → `cycle_id`/`phase` NULL and
the ended-run next_action (`Verb.COMPLETE`, point at `tdd log render`). Production
target: `cmd_note`.

**Cycle 4 — cycle notes render as blockquotes in their cycle.** Test: start the plan
(cycle open in `AWAITING_TEST`), open the fixture's `Ledger` and insert a `note` row
directly with the real run and cycle ids, `phase="AWAITING_TEST"`,
`text="the plan's route name was stale"`; `run_cli(repo, "log", "render", "--out", …)`;
assert the file contains
`> **note** _(during AWAITING_TEST)_: the plan's route name was stale`. *EXPECTED
FAILURE:* `friction_log` never reads the `note` table — the blockquote line is absent,
`AssertionError`. *GREEN:* in `friction_log`'s per-cycle block, after the annotations
loop, select `note WHERE cycle_id = ?` ordered by id and emit the blockquote line per
row. Production target: `render.friction_log`.

**Cycle 5 — run-level notes render in the Executor narrative section.** Test: start the
plan, insert a `note` row with the run id and `cycle_id=None`,
`text="hardest part was the fixture"`; render; assert the output contains
`## Executor narrative`, the caption line
`_Claims from the executor, unverified by design._`, and
`> hardest part was the fixture`. *EXPECTED FAILURE:* section absent —
`AssertionError`. *GREEN:* after the cycle loop and before the Blockers block, select
`note WHERE run_id = ? AND cycle_id IS NULL`; emit header, caption, and one blockquote
per note. Production target: `render.friction_log`.

**Cycle 6 — no narrative section without run-level notes.** Test: start the plan, insert
nothing, render; assert `Executor narrative` does **not** appear. Given cycle 5's
minimal GREEN this may already hold (a loop over an empty selection emits nothing only
if the header was made conditional); if the test **passes on arrival, that is a defect
of sequencing, not a pin** — run the sensitivity check the tool demands honestly
(mutate the guard to emit the header unconditionally, watch this test fail, restore); do
not relabel the cycle. *EXPECTED FAILURE (if RED):* the unconditional header renders —
`AssertionError` on the not-in check. *GREEN:* emit header and caption only when the
selection is non-empty. Production target: `render.friction_log`.

**Cycle 7 — an integrity event's envelope nudges for a note.** Test: working
`calc.py` + passing `TEST_ADD` (pass-on-arrival flow), start the run, `tdd advance` →
the `red_first_violation` envelope (phase `SENSITIVITY_REQUIRED`); assert
`"tdd note" in out["next_action"]["detail"]`. *EXPECTED FAILURE:* the detail is the
unmodified sensitivity instruction — `AssertionError`. *GREEN:* in `advance.py`, a
helper (`_note_nudge(engine, cycle)`) returning one sentence — e.g. ``An integrity
event was recorded on this cycle — consider `tdd note "<why>"` while the reason is
fresh.`` — when the cycle has any `integrity_event` with kind in
`NUDGE_KINDS = {"red_first_violation", "undeclared_file_touched",
"implementation_during_red"}`; `_reply` appends it to `detail`. Minimum GREEN for this
cycle needs no zero-notes condition. Production targets: `_reply` / `_note_nudge`.

**Cycle 8 — the nudge stops once the cycle has a note.** Test: same flow through the
violation envelope, then `run_cli(repo, "note", "the plan predicted this pass")`, then
`tdd advance` again (still `SENSITIVITY_REQUIRED`, asking for the check); assert
`"tdd note" not in out["next_action"]["detail"]`. *EXPECTED FAILURE:* cycle 7's minimal
nudge fires whenever events exist — `AssertionError`. *GREEN:* `_note_nudge` returns
nothing when a `note` row exists for the cycle. Production target: `_note_nudge`.

**Cycle 9 — the terminal advance envelope invites a closing note.** Test: drive the
sensitivity-evidence walk to its genuine terminal (pass-on-arrival → `sensitivity
begin`/mutate/`check`/`end` → `advance` → `advance`); on the final envelope assert
`next_action.terminal is True` and `"tdd note" in next_action.detail`. *EXPECTED
FAILURE:* the COMPLETE message is the unmodified "All declared cycles are complete. Run
`tdd log render`." — `AssertionError`. *GREEN:* extend that message in
`_handle_refactor`'s terminal return: closing note first (hardest cycle and why, plan
inaccuracies, deviations), then `tdd log render`. Note: this envelope does not pass
through the nudge (it is built inline, not via `_reply`) — the invitation is authored
in the message itself. Production target: `_handle_refactor` terminal return.

**Cycle 10 — the terminal skip envelope invites a closing note.** Test: start the
single-cycle plan, `run_cli(repo, "cycle", "skip", "--reason", "outgrown")`; assert
`terminal is True` and `"tdd note" in next_action.detail`. *EXPECTED FAILURE:* the
message is the unmodified "Final cycle skipped; run complete." — `AssertionError`.
*GREEN:* extend `cmd_cycle_skip`'s final-cycle COMPLETE message the same way.
Production target: `cmd_cycle_skip`.

## Deliberate scope cuts (do not build)

- **No hard gates anywhere.** Both prompts are soft by user decision; a coerced note is
  boilerplate and pollutes the audit signal. *Re-evaluation trigger:* if during this run
  an integrity event fires and the nudge proves easy to ignore, note it via
  `tdd note` — do not add a gate mid-run.
- **No nudge on blocker paths.** Premise: `tdd blocker --detail` already captures the
  executor's "why" at filing time, and `resume --unblock --note` records the human's;
  the issue's lost-reasoning complaint targets events with no prose channel at all.
- **Run-level *annotations* stay unrendered.** That is a separate, deliberate gap
  (reserved per-run keys are undocumented on purpose); notes are a distinct channel and
  this plan does not touch annotation rendering.
- **No note↔event linkage columns.** Premise: cycle scope + timestamps are enough for a
  retrospective to correlate a note with the event it explains; a foreign key adds
  schema for speculative precision.
- **No length cap or truncation on note text**, in storage or render. Premise: the
  entire point is preserving executor prose; caps destroy exactly what the issue wants
  kept. Notes are executor-authored sentences, not runner output.
- **No note editing or deletion.** The ledger is append-only by doctrine; a wrong note
  is corrected by a later note.
- **The nudge repeats until noted or the cycle closes** — accepted behaviour, not a bug
  to fix with nudge-tracking state.
- **No new verb.** `tdd note` is out-of-band; `VERB_SET_VERSION` unchanged.
- **Mirrors: none.** The note path lives once (`ledger.py` → `cli.py` → `advance.py` →
  `render.py`); no counterpart implementation exists in this repo, and there is no
  `docs/INVARIANTS.md` registry.
- **Documentation** (README command table + friction-log section, PRD command table and
  §8.5/§11.2, `docs/harness-integration.md`, `examples/skills/tdd-drive/SKILL.md`) is a
  post-run doc follow-up, not a cycle (see Done-criteria).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not
ask the user to start the run. `tdd run start` records which model is executing, resolved
from your own session; a run started by anyone else attributes this work to the wrong
agent.

**Referee rule — stricter than usual for this plan:** run the *released* tdd-cli
**0.8.0** at `~/.local/bin/tdd` (the `uv tool` install), never the working tree's
editable install. Verify before starting: `~/.local/bin/tdd --version` → `tdd-cli 0.8.0`,
and `which tdd` — if it is not `~/.local/bin/tdd`, invoke the referee by its full path in
every command below. This matters doubly here: this plan raises the product's ledger
schema to v8, and any working-tree `tdd` invocation against this repository would upgrade
the shared ledger and permanently lock the 0.8.0 referee out (`LedgerVersionError`). The
repo's test suite exercises v8 only in isolated per-test ledgers.

    git checkout -b feat/77-executor-notes          # first, before anything else
    ~/.local/bin/tdd doctor                         # must report healthy: true
    ~/.local/bin/tdd run start --plan tasks/issue-77-executor-notes.md

If the branch already exists, do not force-checkout and do not pick another name: check it
out only if it carries this plan's commit and no unrelated work, otherwise stop and ask.
If `tdd doctor` fails on *other* uncommitted `tasks/issue-*.md` files (sibling plans),
commit, stash, or gitignore them before `run start`.

Then repeat until done: read `next_action.verb`, do exactly what it says, run
`~/.local/bin/tdd advance`. Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it,
and raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase; the tool stages and commits from
  the phase — do not `git add`/`git commit` yourself.
- Expected baseline for this repo: `{"tddcli": 0}` — anything else means a moved branch;
  stop.
- This plan declares **no `annotation_keys`**, so `annotate_cycle` will not appear. Verbs
  it will hit: all ten cycles are standard `write_test` → `write_code` → optional
  refactor. Cycle 6 may pass on arrival (see its body) — if so the tool drives
  `run_sensitivity_check` → `~/.local/bin/tdd sensitivity begin|check|end` (mutate the
  section guard to emit unconditionally, observe the failure, restore); run it honestly,
  do not relabel the cycle. If blocked, `resolve_blocker` → `tdd blocker --kind --detail`
  (kinds: `plan_defect`, `tooling`, `regression`, `pre_existing_failure`);
  `confirm_cycle_applicable` on a cycle the code has outgrown → `tdd cycle skip
  --reason`.

## Done-criteria

**Before finishing:** run
`~/.local/bin/tdd log render --out tasks/friction-logs/issue-77-executor-notes-friction.md`
(the `tasks/friction-logs/` at the **repository root**) and `~/.local/bin/tdd metrics`.
Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity
event. Do not narrate what the ledger already records.

Then the documentation follow-up, committed as ordinary commits after the run is terminal:
add `tdd note "<text>"` to the command table and the friction-log capture section of
`README.md`; in `docs/PRD.md`, add a Note entity beside Annotation (free-text narrative,
cycle- or run-scoped, unverified by design), add `tdd note` to the command table, and
note schema v8 wherever the ledger schema version is documented; mention the note
channel in `docs/harness-integration.md` and `examples/skills/tdd-drive/SKILL.md` where
`tdd annotate` is described.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-77-executor-notes-friction.md
    git commit -m "docs: friction log for issue-77-executor-notes"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes
the branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If
a gate fails, fix it and re-run the skill — a failed gate is work, not a reason to hand
back.
