---
closes: 68
cycles:
  - n: 1
    project: tddcli
    title: "pytest evidence is the assertion line, not the xdist worker header"
    test: "tests/test_evidence_extraction.py::test_pytest_evidence_is_the_assertion_line_not_the_xdist_header"
    files: ["src/tddcli/adapters/base.py", "src/tddcli/adapters/pytest_adapter.py"]
    commit_red: "test: pytest evidence line skips the xdist worker header"
    commit_green: "feat: Verdict.target_evidence — pytest extracts the first E-line of longrepr"

  - n: 2
    project: tddcli
    pin_cycle: true
    title: "pytest evidence is empty when longrepr has no assertion line"
    test: "tests/test_evidence_extraction.py::test_pytest_evidence_is_empty_when_no_assertion_line_exists"
    commit_pin: "test: pin empty pytest evidence when no E-line exists"

  - n: 3
    project: tddcli
    title: "xctest evidence is the error line, not interleaved console noise"
    test: "tests/test_evidence_extraction.py::test_xctest_evidence_is_the_error_line_not_console_noise"
    files: ["src/tddcli/adapters/xctest_adapter.py"]
    commit_red: "test: xctest evidence line ignores console noise in the test window"
    commit_green: "feat: xctest evidence is the first ': error:' line of the test's window"

  - n: 4
    project: tddcli
    title: "vitest evidence is the first line of the first failure message"
    test: "tests/test_evidence_extraction.py::test_vitest_evidence_is_the_first_failure_message_line"
    files: ["src/tddcli/adapters/vitest_adapter.py"]
    commit_red: "test: vitest evidence is the first failureMessage line"
    commit_green: "feat: vitest evidence extracted from failureMessages[0]"

  - n: 5
    project: tddcli
    title: "gradle evidence is the first line of the junit failure message"
    test: "tests/test_evidence_extraction.py::test_gradle_evidence_is_the_first_failure_message_line"
    files: ["src/tddcli/adapters/gradle_adapter.py"]
    commit_red: "test: gradle evidence is the junit failure message line"
    commit_green: "feat: gradle evidence extracted from the failure element's message"

  - n: 6
    project: tddcli
    title: "exec evidence falls back to the last non-empty output line"
    test: "tests/test_evidence_extraction.py::test_exec_evidence_is_the_last_nonempty_output_line"
    files: ["src/tddcli/adapters/exec_adapter.py"]
    commit_red: "test: exec evidence is the last non-empty combined-output line"
    commit_green: "feat: exec evidence falls back to the last non-empty line"

  - n: 7
    project: tddcli
    title: "sensitivity check stores the adapter's evidence line in the ledger"
    test: "tests/test_sensitivity_evidence.py::test_sensitivity_check_records_the_evidence_line"
    files: ["src/tddcli/ledger.py", "src/tddcli/cli.py"]
    commit_red: "test: sensitivity check persists evidence_line on its ledger row"
    commit_green: "feat: schema v7 — sensitivity_check.evidence_line stored at check time"

  - n: 8
    project: tddcli
    title: "friction log observed line renders the stored evidence line"
    test: "tests/test_sensitivity_evidence.py::test_friction_log_observed_line_is_the_evidence_line"
    files: ["src/tddcli/render.py"]
    commit_red: "test: observed line shows evidence_line, not the raw first line"
    commit_green: "feat: friction log prefers evidence_line for the observed snippet"

  - n: 9
    project: tddcli
    title: "empty evidence renders an explicit no-assertion-line sentinel"
    test: "tests/test_sensitivity_evidence.py::test_empty_evidence_renders_the_sentinel"
    files: ["src/tddcli/render.py"]
    commit_red: "test: empty evidence renders <no assertion line captured>"
    commit_green: "feat: render the no-assertion-line sentinel instead of wire noise"

  - n: 10
    project: tddcli
    title: "legacy rows with NULL evidence keep the first-line fallback"
    test: "tests/test_sensitivity_evidence.py::test_null_evidence_falls_back_to_first_observed_line"
    files: ["src/tddcli/render.py"]
    commit_red: "test: NULL evidence_line falls back to the old first-line snippet"
    commit_green: "feat: distinguish legacy NULL evidence from computed-empty evidence"

  - n: 11
    project: tddcli
    title: "a long observed line is capped keeping the tail, not the head"
    test: "tests/test_sensitivity_evidence.py::test_long_evidence_is_capped_keeping_the_tail"
    files: ["src/tddcli/render.py"]
    commit_red: "test: an over-long observed line keeps its tail"
    commit_green: "feat: tail-keeping cap on the observed evidence line"
---

# Issue #68 — sensitivity `observed:` evidence captures the wrong output line

https://github.com/geuben/tdd-cli/issues/68
Task file: `tasks/issue-68-sensitivity-evidence.md`

## Context

The sensitivity check stores the target's raw failure text (`observed_failure`) and the
friction log renders its **first line, head-truncated to 160 chars** as the `observed:`
evidence. On pytest+xdist the first line of `longrepr` is the worker header
(`[gw0] darwin -- Python 3.x ...`); on XCTest the per-test window opens with whatever
console noise the host app printed (`Socket SO_ERROR [61: Connection refused]`); and the
head-cut truncates mid-identifier (`-[SomeTests.Rec`). Whenever a cycle degrades to
sensitivity-only verification (pin cycles, `red_first_violation`), this line is the *only*
auditable proof the test bites — so it must be the assertion line, or an explicit admission
that none was found.

The fix is per-adapter, at capture time: each adapter already produces
`Verdict.target_failure` from runner output it alone understands, so each also produces a
one-line `Verdict.target_evidence`. The sensitivity check stores it on its ledger row
(schema v7), and the friction log renders it — with a `<no assertion line captured>`
sentinel when the adapter found nothing plausible, and a tail-keeping cap (the same
head-vs-tail reasoning as #17's `clip_failure`).

## Design decisions (locked)

- **Extraction happens at capture time in the adapter, stored in the ledger** — not
  recomputed at render time. Decided by codebase evidence: `render.friction_log(ledger, run)`
  has no config or adapter context, the `sensitivity_check` row records no adapter, and the
  module doctrine is "every observable fact comes from recorded events". Adapter knowledge
  stays in adapters (§10: adding an adapter requires no core change).
- **Carrier is a new `Verdict.target_evidence: str = ""` field**, set beside
  `target_failure` on the target-FAILED path of each adapter's `run()`, computed by a pure
  per-adapter helper (`_evidence_line`) so each heuristic is unit-testable on canned output.
  `cmd_sensitivity` reads it from the `verdicts` element `run_projects` already returns
  (currently discarded as `_`) — no `run_projects` signature change, `advance.py` untouched.
- **Storage: `sensitivity_check.evidence_line TEXT`, `SCHEMA_VERSION = 7`,
  `MIGRATIONS[6]` = the `ALTER TABLE`** — following the established v4→v5/v5→v6 pattern
  (idempotent SCHEMA + guarded ALTER; the duplicate-column guard in `Ledger.__init__`
  already covers re-application). The column is written as `""` when extraction found
  nothing, so NULL remains distinguishable as "row predates v7".
- **Render three-way split**: non-empty evidence → show it; computed-empty (`""`) →
  `<no assertion line captured>`; NULL (legacy row) → the old first-line snippet, because
  for pre-v7 rows the raw first line is the only data there is and dropping it loses
  information.
- **Cap keeps the tail** (issue's own instruction, same reasoning as #17): a line longer
  than 160 chars renders as `…` + its last 160 chars, preserving the test identity and
  message tail that the old head-cut destroyed.
- **Per-adapter heuristics** (empirically probed for pytest, canned-output-tested for the
  rest — see Verified repo facts):
  - *pytest*: first `longrepr` line matching `^E\s`, with the `E` prefix and following
    whitespace stripped. Probe-verified to yield `AssertionError: reversed mismatch` /
    `ValueError: boom from deep` for assertion and deep-exception failures, plain and
    under xdist alike (the `[gw0]` header never matches `^E\s`). No E-line → `""`.
  - *xctest*: first line containing `: error:` inside the already-per-test window
    `_failure_for` captures (XCTAssert failures are emitted as
    `/path.swift:42: error: -[Bundle.Class test] : XCTAssertEqual failed: …`; console
    noise like `Socket SO_ERROR …` never contains `: error:`). None → `""`.
  - *gradle*: first non-empty line of the junit `<failure>` message+body (the
    `expected:<…> but was:<…>` line — the runner the issue confirms already correct).
  - *vitest*: first non-empty line of `failureMessages[0]`.
  - *exec*: last non-empty line of the combined output — the issue's "last non-noise
    stderr line" fallback, applied where no structured format exists.

## Verified repo facts

*Anchors are symbol names — grep for them; no line numbers anywhere in this plan.*

- **The defect chain, read from code.** Adapters set `Verdict.target_failure`
  (`adapters/base.py` dataclass); `Engine.run_projects` (`machine.py`) forwards the
  target's `verdict.target_failure` as the returned `failure_text` and also returns the
  `verdicts` list; `cmd_sensitivity` (`cli.py`, the `args.step == "check"` branch) binds
  `outcomes, _, _, failure_text` and stores `observed_failure=failure_text[:4000]` via
  `ledger.update("sensitivity_check", ...)`; `friction_log` (`render.py`) renders
  `sens["observed_failure"].strip().splitlines()` then `snippet[0][:160]` under the
  `- **Sensitivity check:**` block. That `snippet[0][:160]` is both defects.
- **Empirical probe (deleted, tree clean).** A throwaway project ran pytest 8 +
  pytest-json-report with and without `-n 2` (xdist) on an assertion failure and a
  helper-raised exception. Plain `longrepr` begins with the `def test_…` source line and
  carries `E       AssertionError: reversed mismatch`; under xdist the **first line is
  `[gw0] darwin -- Python 3.12.8 …`** — exactly the issue's report — while the `E`-lines
  are unchanged. First-`E`-line extraction returns the right evidence in all four
  combinations; the deep-exception case's first `E`-line is `ValueError: boom from deep`.
- **Adapter test harnesses exist for canned output.** `tests/test_failure_clipping.py`
  (`_pytest_adapter` + monkeypatched `adapters.base.run_command` writing a fake JSON
  report) is the pytest pattern; `tests/test_xctest_adapter.py` (canned xcodebuild stdout
  with `Test Case '-[…]' started./failed` markers), `tests/test_gradle_adapter.py` (canned
  junit XML with `<failure message="expected:&lt;1000&gt; but was:&lt;500&gt;" …>`), and
  `tests/test_vitest_adapter.py` / `tests/test_exec_adapter.py` are the others. Cycle 1–6
  tests follow these shapes in the new `tests/test_evidence_extraction.py`.
- **`Verdict` is a plain dataclass** — the cycle-1 RED reads a field that does not exist,
  so it fails with `AttributeError`, a legitimate in-test failure (not a collection error).
- **Ledger migration pattern.** `ledger.py` holds `SCHEMA_VERSION = 6` and a `MIGRATIONS`
  dict keyed by from-version; entries 4 and 5 are `ALTER TABLE … ADD COLUMN` strings, and
  `Ledger.__init__` swallows `duplicate column name` on re-application.
  `tests/test_release_surface.py` pins version recording, upgrade-from-1, and
  newer-ledger refusal; none of its assertions is broken by v7 (they compare against the
  `SCHEMA_VERSION` constant, not a literal).
- **Sensitivity flow in the test fixture is inherited verbatim from passing tests.**
  `tests/test_end_to_end.py::test_passing_on_arrival_reaches_refactor_once_the_check_is_verified`
  drives exactly the flow cycles 7–11 reuse: working `calc.py` + `TEST_ADD` → `advance`
  (→ `SENSITIVITY_REQUIRED`) → `sensitivity begin` → mutate `add` to `return 0` →
  `sensitivity check` → `sensitivity end`. With that mutation the target's first `E`-line
  is `assert 2 == 0`-shaped, so cycle 7 asserts `evidence_line.startswith("assert")`.
- **Tests open the ledger directly.** `tests/test_progress.py` and
  `tests/test_snapshot_and_identity.py` construct `Ledger(...)` under the conftest
  `ledger_home` fixture; `Ledger.update("sensitivity_check", row_id, …)` with
  `evidence_line=None` writes SQL NULL — how cycles 9–11 stage their variants.
- **No existing test asserts the `observed:` render line** (`grep -rn "observed" tests/`
  → only unrelated prose), and no test asserts `target_evidence` or `evidence_line`
  anywhere. `modifies_tests` is empty for every cycle.
- **Suite is green now**: 406 passed on this branch, 2m05s. Expected `run start` baseline:
  `{"tddcli": 0}` — anything else means a moved branch; stop.
- **Lint is ruff-only, no typecheck** (`tdd.toml`: `lint = ["uv run ruff check"]`), and
  every cycle's RED test references only symbols that exist or dataclass attributes whose
  absence is a runtime failure — **no cycle needs `stub_expected`**.

## Cycle detail

*Single project `tddcli`. Cycles 1–6 are adapter-level unit tests on canned runner output
in `tests/test_evidence_extraction.py`; cycles 7–11 drive the real sensitivity flow on the
conftest `repo` fixture in `tests/test_sensitivity_evidence.py`. Minimum GREEN throughout;
each cycle's implementation is only what its one test demands.*

**Cycle 1 — pytest evidence skips the xdist header.** Test: build the pytest adapter as
`test_failure_clipping.py` does; fake report with one failed test whose `call.longrepr` is
the probe-verified xdist shape — first line `[gw0] darwin -- Python 3.12.8 /tmp/x/bin/python`,
then the source lines, then `E       AssertionError: reversed mismatch` and a diff block.
Assert `verdict.target_evidence == "AssertionError: reversed mismatch"`.
*EXPECTED FAILURE (probed field-absence):* `AttributeError: 'Verdict' object has no
attribute 'target_evidence'`. *GREEN:* add `target_evidence: str = ""` to `Verdict`
(`adapters/base.py`); in `pytest_adapter.run()` where `target_failure` is set from
`call.longrepr`, also set `verdict.target_evidence = self._evidence_line(longrepr)` — a
static helper returning the first line matching `^E\s` with the `E` prefix stripped, `""`
otherwise. Production target: `PytestAdapter.run` / `PytestAdapter._evidence_line`.

**Cycle 2 (pin) — pytest evidence is empty without an assertion line.** Characterises the
`""` fallback cycle 1's minimal helper produces (a `next(..., "")` over `E`-lines): a
longrepr with no `E`-prefixed line (e.g. a bare `<file>:<line>: RecursionError` location tail)
yields `target_evidence == ""`. Expected to **pass on arrival**; the mandatory sensitivity
check proves it bites: mutate `_evidence_line` to return the first raw line
unconditionally, observe the test fail, restore. This pinned `""` is what triggers cycle
9's sentinel.

**Cycle 3 — xctest evidence ignores console noise.** Test: canned xcodebuild output in the
`test_xctest_adapter.py` style — `Test Case '-[AppTests.RecTests testStopsRecording]'
started.`, a noise line `2026-08-27 … Socket SO_ERROR [61: Connection refused]`, the
failure line `/Users/x/RecTests.swift:42: error: -[AppTests.RecTests testStopsRecording] :
XCTAssertEqual failed: ("recording") is not equal to ("stopped")`, then the `failed`
marker. Assert `verdict.target_evidence` contains `XCTAssertEqual failed` and not
`Socket SO_ERROR`. *EXPECTED FAILURE:* `target_evidence` is the dataclass default `""`;
`AssertionError` on the contains-check. *GREEN:* in `XCTestAdapter.run()` where
`_failure_for` sets `target_failure`, also set evidence = first `: error:` line of the same
per-test window (`XCTestAdapter._evidence_line`). Production target: `XCTestAdapter.run` /
`_evidence_line`.

**Cycle 4 — vitest evidence.** Test: canned vitest JSON in the `test_vitest_adapter.py`
style with `failureMessages` = `["AssertionError: expected 2 to be 3 // Object.is
equality\n    at file…"]`. Assert `verdict.target_evidence == "AssertionError: expected 2
to be 3 // Object.is equality"`. *EXPECTED FAILURE:* `""` vs expected — `AssertionError`.
*GREEN:* where `target_failure` is joined from `failureMessages`, set evidence = first
non-empty line of `failureMessages[0]` (empty list → `""`). Production target:
`VitestAdapter.run`.

**Cycle 5 — gradle evidence.** Test: canned junit XML in the `test_gradle_adapter.py`
style (`<failure message="expected:&lt;1000&gt; but was:&lt;500&gt;" …>` with a stack-trace
body). Assert `verdict.target_evidence == "expected:<1000> but was:<500>"`. *EXPECTED
FAILURE:* `""` vs expected — `AssertionError`. *GREEN:* compute evidence beside
`_failure_text` (first non-empty line of message+body) and set it where `target_failure`
is taken from `failures.get(target, …)`. Production target: `GradleAdapter.run` /
`_failure_text` site.

**Cycle 6 — exec evidence.** Test: exec adapter with a fake failing script whose combined
output ends with a distinctive last line (e.g. stdout noise, then
`FAIL: expected exit 0, got 1`). Assert `verdict.target_evidence == "FAIL: expected exit
0, got 1"`. *EXPECTED FAILURE:* `""` vs expected — `AssertionError`. *GREEN:* where
`target_failure = clip_failure(combined)`, set evidence = last non-empty line of
`combined`. Production target: `ExecAdapter.run`.

**Cycle 7 — sensitivity check stores `evidence_line` (schema v7).** Test: on the `repo`
fixture, drive the inherited pass-on-arrival sensitivity flow (working `calc.py`,
`TEST_ADD`, `advance`, `sensitivity begin`, mutate `add` to `return 0`, `sensitivity
check`); then `Ledger(repo)` under the fixture's ledger home,
`one("SELECT evidence_line FROM sensitivity_check ORDER BY id DESC LIMIT 1")`, assert
`row["evidence_line"].startswith("assert")`. *EXPECTED FAILURE:* the column does not
exist — the SELECT raises `sqlite3.OperationalError: no such column: evidence_line` (an
in-test failure; the module imports fine). *GREEN:* `ledger.py` — add `evidence_line TEXT`
to the `sensitivity_check` CREATE TABLE, `SCHEMA_VERSION = 7`, `MIGRATIONS[6] = "ALTER
TABLE sensitivity_check ADD COLUMN evidence_line TEXT;"`; `cli.py` `cmd_sensitivity` —
bind `verdicts` from `run_projects`, `evidence = next((v.target_evidence for v in verdicts
if v.target_evidence), "")`, add `evidence_line=evidence` to the existing
`ledger.update("sensitivity_check", …)`. Production targets: `ledger.py` schema constants,
`cmd_sensitivity`.

**Cycle 8 — render prefers `evidence_line`.** Test: after the cycle-7 flow plus
`sensitivity end`, `Ledger.update` the row to `observed_failure = "[gw0] darwin -- Python
3.12.8 /tmp/x\n\n    def test…\nE       AssertionError: reversed mismatch"` and
`evidence_line = "AssertionError: reversed mismatch"`; `run_cli(repo, "log", "render",
"--out", …)`; assert the file contains ``observed: `AssertionError: reversed mismatch` ``
and not `[gw0]`. *EXPECTED FAILURE:* render shows the raw first line — the `[gw0]`
assertion fails. *GREEN:* in `friction_log`'s sensitivity block, when
`sens["evidence_line"]` is non-empty show it as the snippet, else fall through to the
existing first-line path. Production target: `render.friction_log`.

**Cycle 9 — the sentinel.** Test: same staging with `evidence_line = ""` (and any
non-empty `observed_failure`); assert the rendered log contains
`observed: <no assertion line captured>` and not the raw first line. *EXPECTED FAILURE:*
the empty string falls through to the first-line path — sentinel absent, `AssertionError`.
*GREEN:* distinguish `""` (render the sentinel, unbackticked) from non-empty. Production
target: `render.friction_log`.

**Cycle 10 — legacy NULL keeps the first-line fallback.** Test: same staging with
`evidence_line = None` and `observed_failure` whose first line is `legacy first line`;
assert ``observed: `legacy first line` `` renders. Given cycle 9's minimal GREEN (a falsy
check collapses NULL into the sentinel), *EXPECTED FAILURE:* the sentinel renders instead
of the legacy line — `AssertionError`. If cycle 9's implementation happened to already
distinguish `None`, this test passes on arrival and the tool's sensitivity path handles
it — run the check honestly (mutate the `None` branch), do not relabel the cycle.
*GREEN:* three-way split on `evidence_line`: non-empty → evidence; `== ""` → sentinel;
`None` → the old `snippet[0]` path. Production target: `render.friction_log`.

**Cycle 11 — tail-keeping cap.** Test: same staging with `evidence_line` a ~300-char line
whose last 40 chars are distinctive (e.g. ending
`…is not equal to ("stopped") -[AppTests.RecTests testStopsRecording]`); assert the
rendered `observed:` line contains the distinctive tail and an `…` elision marker, and
does not contain the line's opening characters. *EXPECTED FAILURE:* cycle 8's minimal
GREEN renders the line unbounded (or head-cut) — the tail/`…` assertions fail. *GREEN:*
cap the evidence snippet at 160 chars keeping the tail (`"…" + line[-160:]` when longer).
Production target: `render.friction_log`.

## Deliberate scope cuts (do not build)

- **No "last non-noise stderr line" fallback for pytest/xctest/gradle/vitest.** Premise:
  for structured runners, an un-matched failure text means the output genuinely lacks an
  assertion line, and the observed XCTest noise (`Socket SO_ERROR …`) *was* the last
  stderr line — a generic noise filter would re-introduce the bug the sentinel exists to
  admit. The full `observed_failure` stays in the ledger for auditing. The fallback exists
  only in the exec adapter, where no structured format is available. *Re-evaluation
  trigger:* if during execution a probed runner output shows a plausible assertion line
  the chosen heuristic misses, stop and raise `plan_defect` — do not widen the heuristic
  silently.
- **`NOT_COLLECTED` sensitivity outcomes render the sentinel.** A mutation that breaks the
  build/collection legitimately "bites" (`cmd_sensitivity` accepts it), but a compile
  error has no assertion line; `<no assertion line captured>` is the honest rendering and
  the full build error remains in `observed_failure`. No per-adapter evidence extraction
  on the `not_collected` paths.
- **The sensitivity envelope result is unchanged** (`observed_failure` `[:800]` in the
  `check` response) — the live executor sees the full text, which is strictly richer than
  one line; the defect is only in the rendered log.
- **No `invocation.target_evidence` column.** The issue is about the sensitivity evidence
  line; RED/GREEN verdicts already surface full `target_failure` in envelopes, and
  widening the schema further is speculative.
- **No dedicated migration test.** Precedent: v4→v5 and v5→v6 shipped `ALTER` entries with
  no per-version test; `tests/test_release_surface.py` covers version recording and the
  upgrade walk generically, and cycle 7 proves the column exists on fresh ledgers.
- **Mirrors: none.** The evidence path lives once (`adapters/*` → `machine.py` →
  `cli.py` → `render.py`); no counterpart implementation exists in this repo, and there is
  no `docs/INVARIANTS.md` registry.
- **README/PRD documentation** is a post-run doc follow-up, not a cycle (see
  Done-criteria).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not
ask the user to start the run. `tdd run start` records which model is executing, resolved
from your own session; a run started by anyone else attributes this work to the wrong
agent.

**Referee rule — stricter than usual for this plan:** run the *released* tdd-cli **0.8.0**
at `~/.local/bin/tdd` (the `uv tool` install), never the working tree's editable install.
On this machine plain `tdd` on PATH resolves to an editable venv whose `tddcli` imports
from this working tree — verify before starting:
`~/.local/bin/tdd --version` → `tdd-cli 0.8.0`, and
`python3 -c "import tddcli"` must **not** be how your `tdd` resolves (check
`which tdd`; if it is not `~/.local/bin/tdd`, invoke the referee by its full path in every
command below). This matters doubly here: this plan raises the product's ledger schema to
v7, and any working-tree `tdd` invocation against this repository would upgrade the shared
ledger and permanently lock the 0.8.0 referee out (`LedgerVersionError`). The repo's test
suite exercises v7 only in isolated per-test ledgers.

    git checkout -b feat/68-sensitivity-evidence   # first, before anything else
    ~/.local/bin/tdd doctor                        # must report healthy: true
    ~/.local/bin/tdd run start --plan tasks/issue-68-sensitivity-evidence.md

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
  it will hit: standard cycles (1, 3–11) drive `write_test` → `write_code` → optional
  refactor; **cycle 2 (pin)** passes on arrival and drives `run_sensitivity_check` →
  `~/.local/bin/tdd sensitivity begin|check|end` (mutate `PytestAdapter._evidence_line` to
  return the first raw line, observe the pin fail, restore); cycle 10 may also demand a
  sensitivity check if its test passes on arrival (see its body — run it, do not relabel).
  If blocked, `resolve_blocker` → `tdd blocker --kind --detail` (kinds: `plan_defect`,
  `tooling`, `regression`, `pre_existing_failure`); `confirm_cycle_applicable` on a cycle
  the code has outgrown → `tdd cycle skip --reason`.

## Done-criteria

**Before finishing:** run
`~/.local/bin/tdd log render --out tasks/friction-logs/issue-68-sensitivity-evidence-friction.md`
(the `tasks/friction-logs/` at the **repository root**) and `~/.local/bin/tdd metrics`.
Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity
event. Do not narrate what the ledger already records.

Then the documentation follow-up, committed as ordinary commits after the run is terminal:
in `docs/PRD.md`, extend the `tdd sensitivity check` row of the command table ("record the
mutation diff and the observed failure") to name the per-adapter evidence line, and note
schema v7 wherever the ledger schema version is documented.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-68-sensitivity-evidence-friction.md
    git commit -m "docs: friction log for issue-68-sensitivity-evidence"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes
the branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If
a gate fails, fix it and re-run the skill — a failed gate is work, not a reason to hand
back.
