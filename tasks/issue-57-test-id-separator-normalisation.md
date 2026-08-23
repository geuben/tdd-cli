---
closes: 57
cycles:
  - n: 1
    project: tddcli
    title: "Adapter.normalise_id is an identity hook by default"
    test: "tests/test_id_normalisation.py::test_base_adapter_normalise_id_is_identity"
    files: ["src/tddcli/adapters/base.py"]
    commit_red: "test: adapters expose a normalise_id target-matching hook"
    commit_green: "feat: Adapter.normalise_id identity hook for target matching"

  - n: 2
    project: tddcli
    title: "VitestAdapter.normalise_id canonicalises the describe/test separator"
    test: "tests/test_id_normalisation.py::test_vitest_normalise_id_collapses_describe_separator"
    files: ["src/tddcli/adapters/vitest_adapter.py"]
    commit_red: "test: vitest normalise_id folds ' > ' between nesting levels to a space"
    commit_green: "feat: VitestAdapter.normalise_id canonicalises describe/test separator"

  - n: 3
    project: tddcli
    title: "vitest run() matches a declared target that differs only by the separator"
    test: "tests/test_id_normalisation.py::test_vitest_run_matches_separator_only_target"
    files: ["src/tddcli/adapters/vitest_adapter.py"]
    commit_red: "test: vitest run matches a target differing only by describe separator"
    commit_green: "fix: match declared vitest target against collected ids via normalise_id"
---

# Issue #57 — normalise the describe/test id separator so a formatting-only difference is not a `declared_test_mismatch`

https://github.com/geuben/tdd-cli/issues/57
Task file: `tasks/issue-57-test-id-separator-normalisation.md`

## Context

A declared target test id that differs from the collected id **only** by the
describe/test separator is today treated as `not_found`. For vitest the collected
id joins the ancestor describe titles and the test title with a single **space**
(vitest's `fullName`), while a human or planner writing the target naturally puts
` > ` between the describe block and the test name. Example:

- declared: `services/__tests__/x.test.ts > someHelper > formats a future timestamp as a relative string`
- collected: `services/__tests__/x.test.ts > someHelper formats a future timestamp as a relative string`

Only the ` > ` versus a space between the describe block and the test name differs —
it is the same test. Yet the exact-string match in the adapter misses, the adapter
returns `NOT_FOUND`, and `advance._handle_test_phase` then treats the target as
missing: it runs `_adopt_target`, emits a `declared_test_mismatch` integrity event,
rewrites `target_tests`, and forces an extra `tdd advance` round trip before the
cycle can proceed. That round trip and the noise event are pure overhead for what is
a formatting-only difference.

The fix belongs **in the adapter**, at the point where a declared target is matched
against collected ids — not in `advance.py`. The `declared_test_mismatch` machinery
in `_handle_test_phase` must stay exactly as it is: it is the correct response to a
*genuinely* different target. The change is to make the adapter's target match
separator-insensitive so `NOT_FOUND` is never produced for a same-test formatting
difference in the first place. With the match succeeding, `_handle_test_phase`'s
`missing` list is empty for this case, so no event and no round trip occur — the id
is adopted silently, exactly as the issue asks.

Normalisation is **per adapter** because the separator convention is per runner:
pytest node ids use `::` between file, class and test and carry no describe/test
ambiguity, so the pytest adapter keeps the identity hook; vitest joins nesting
levels with a space in `fullName` but is declared with ` > `, so the vitest adapter
overrides the hook to treat ` > ` and a single space between nesting levels as
equivalent. The hook lives on the base `Adapter` (cycle 1) and vitest overrides it
(cycles 2–3); no core logic in `advance.py` or `machine.py` changes.

Ordering: cycle 1 introduces the base identity hook and proves pytest ids are
untouched; cycle 2 gives vitest its canonicalisation rule as a pure, directly
testable method; cycle 3 wires that method into `VitestAdapter.run()`'s target
matching so the end-to-end `NOT_FOUND` bug is fixed.

## Verified repo facts

*Every fact below was read from the codebase during hardening — none are asserted
from memory. Locators are function names and line numbers at hardening time; grep
for the names at execution time.*

- **The `NOT_FOUND` outcome is decided inside each adapter's `run()`, not in
  `advance.py`.** `advance._handle_test_phase` (`src/tddcli/advance.py`, lines
  120–155) reads `missing = [t for t, o in outcomes.items() if o == NOT_FOUND]` and
  only *then* runs `_adopt_target` and emits `declared_test_mismatch`. `outcomes` is
  built in `Engine.run_projects` (`src/tddcli/machine.py` line 141:
  `outcomes[target] = verdict.target_outcome`) and is keyed by the **declared**
  target string. So making the adapter return `PASSED`/`FAILED` for a
  separator-only-different target is sufficient — `missing` is then empty and the
  entire mismatch path is never entered. No change to `advance.py` is required or
  wanted.
- **vitest builds collected ids by joining the describe path and test name with a
  space.** `VitestAdapter._id_for` (`src/tddcli/adapters/vitest_adapter.py` lines
  50–56) returns `self.qualify(f"{rel} > {full_name}")`, where `full_name` is
  vitest's `fullName` — the ancestor titles and title space-joined. The module
  docstring (lines 1–9) and `_parse_list_output` (lines 144–166) both state
  explicitly that `list` emits ` > ` between nesting levels while `run` joins with a
  space, and that the two must be reconciled by splitting on ` > ` and rejoining the
  name parts with a space. The id shape is therefore
  `<project>::<file> > <space-joined full name>`; the **only** ` > ` that is
  structural is the one after the file.
- **vitest target matching is an exact `in` / `==` string comparison.**
  `VitestAdapter.run()` (lines 107–132) does `if target in verdict.passed` (line
  111) and `if target in verdict.failed` (line 115), then on the FAILED branch
  re-scans suites with `if self._id_for(...) == target` (lines 116–123) to attach
  `target_failure`, and finally falls through to `NOT_COLLECTED`/`NOT_FOUND` (lines
  125–131). A declared ` > `-separated target never equals a space-joined collected
  id, so it lands on `NOT_FOUND` (line 131) — this is the bug. All three comparison
  sites (passed, failed, failure-message lookup) must go through the normalised
  form.
- **pytest target matching is also exact but needs no change.**
  `PytestAdapter.run()` (`src/tddcli/adapters/pytest_adapter.py` lines 138–153)
  does `native = self.strip(target)` then `next((t for t in tests if t["nodeid"] ==
  native), None)`. pytest node ids use `::` and carry no describe/test separator
  ambiguity, so the base identity hook leaves pytest matching byte-for-byte
  unchanged. Cycle 1 pins this.
- **`Adapter` (base) has no `normalise_id` today** — confirmed by
  `grep -rn "normalise\|normalize" src/` returning nothing. `Adapter` (lines
  126–283 of `src/tddcli/adapters/base.py`) already carries `qualify` (line 134)
  and `strip` (line 138), which the vitest override reuses to split off and re-add
  the `<project>::` prefix.
- **Adapters are constructed cheaply from a loaded config in unit tests.**
  `tests/test_vitest_adapter.py` (lines 31–35) builds a real `VitestAdapter` via
  `adapter_for(tmp_path)`: write a `tdd.toml`, `mkdir` the project root,
  `config_mod.load(tmp_path)`, `VitestAdapter(cfg.project("frontend"), tmp_path)`.
  The new test module mirrors this recipe for both a vitest project and a pytest
  project (`adapter = "pytest"`, `root = "backend"`, then
  `PytestAdapter(cfg.project("backend"), tmp_path)`).
- **`VitestAdapter.run()` is unit-testable without node** by monkeypatching
  `adapter._run_suite`. `run()` calls `self._run_suite(f"{base} --reporter=json",
  extra_env)` (line 72) and passes the stdout to `_extract_json` (line 34). With no
  overrides, `_suite_invocations()` (base line 195) yields exactly one invocation,
  so a `lambda cmd, env=None, timeout=None: (0, <canned json>, "")` fully drives
  `run()`. The canned report shape is
  `{"duration": 0, "testResults": [{"name": <abs suite path>, "status": "passed",
  "assertionResults": [{"fullName": "<space-joined>", "status": "passed",
  "failureMessages": []}]}]}`; `_id_for` relpaths `name` against `self.root`, so set
  `name = str(tmp_path / "frontend" / "x.test.ts")`.
- **The vitest test suite already pins the space-vs-arrow reconciliation** in
  `tests/test_vitest_adapter.py::test_parsed_ids_match_the_form_run_produces` (lines
  45–56) and `::test_arrows_are_not_left_in_the_name` (lines 94–99). The new
  normalisation is the same rule applied to the *declared* side at match time; write
  the new tests in that module's style but in the new dedicated module
  `tests/test_id_normalisation.py` (there is no existing base-adapter or pytest-adapter
  test module — `ls tests/ | grep pytest` is empty — so a new module is the correct
  home, and it imports both `VitestAdapter` and `PytestAdapter`).
- **`tdd target` (`cmd_target`, `src/tddcli/cli.py` lines 1030–1058) is a separate
  exact-match surface** (`if args.test not in known`, line 1044, with a `difflib`
  near-miss hint). It is *not* the emit site in this issue and is a deliberate scope
  cut (below).
- **Baseline for this repo is `{"tddcli": 0}`** (single project `tddcli` in
  `tdd.toml`); the released controller at hardening time is `0.7.0` (git:
  `480e082 chore: release v0.7.0`).

## Cycle detail

*Expected failure per cycle; minimum GREEN; resist future cycles' behaviour.*

### Cycle 1 — base identity hook

**Expected RED:** `AttributeError: 'PytestAdapter' object has no attribute
'normalise_id'`.

Test (`tests/test_id_normalisation.py`): build a `PytestAdapter` for a `backend`
pytest project (mirror `adapter_for` from `test_vitest_adapter.py`); assert
`adapter.normalise_id("backend::tests/test_x.py::test_y")` returns the string
unchanged. This proves the hook exists **and** that pytest ids are not rewritten.

GREEN: add `def normalise_id(self, test_id: str) -> str: return test_id` to the base
`Adapter` in `src/tddcli/adapters/base.py`. No vitest logic yet.

### Cycle 2 — vitest canonicalisation

**Expected RED:** assertion — the base identity hook returns the id with its ` > `
between describe and test still present, so it does not equal the space-joined
canonical form the test expects.

Test: build a `VitestAdapter`; assert
`adapter.normalise_id("frontend::a.test.ts > someHelper > formats a value")`
== `"frontend::a.test.ts > someHelper formats a value"`, and that the method is
idempotent on an already-space-joined id
(`normalise_id("frontend::a.test.ts > someHelper formats a value")` is unchanged).
Also assert a multi-level id (`... > a > b > c`) collapses to `... > a b c`, and an
id with no ` > ` (unusual, file-only) is returned unchanged.

GREEN: override `normalise_id` on `VitestAdapter`. Reuse `strip`/`qualify` and the
exact rule already in `_parse_list_output`: strip the `<project>::` prefix,
`partition(" > ")` to isolate the file (the one structural arrow), then
`" ".join(part.strip() for part in remainder.split(" > "))` and re-`qualify`. If the
stripped id has no ` > `, return the original unchanged.

### Cycle 3 — run() matches a separator-only target

**Expected RED (probe-verified):** `run()` returns `verdict.target_outcome ==
NOT_FOUND` where the test expects `PASSED` — the declared ` > `-separated target never
equals the space-joined collected id, so the `in verdict.passed` check misses and
control falls through to `NOT_FOUND`. Confirmed empirically during hardening: with
`_run_suite` monkeypatched to return a canned report whose one passing test has
`fullName == "someHelper formats a value"` in suite `a.test.ts`, the collected id is
`frontend::a.test.ts > someHelper formats a value`; `run("frontend::a.test.ts >
someHelper formats a value")` → `passed`, while `run("frontend::a.test.ts > someHelper
> formats a value")` → `not_found` — the exact bug.

Test: build a `VitestAdapter`; monkeypatch `adapter._run_suite` to return
`(0, <canned JSON with one passing test whose fullName is "someHelper formats a
value" in suite tmp_path/frontend/a.test.ts>, "")`. Call
`adapter.run("frontend::a.test.ts > someHelper > formats a value")` and assert
`verdict.target_outcome == PASSED`. Add a second assertion that a genuinely
different declared target
(`"frontend::a.test.ts > someHelper > a different test"`) still returns
`NOT_FOUND` — normalisation must not over-match and swallow real mismatches
(this keeps `declared_test_mismatch` meaningful; it holds both before and after
GREEN and guards the fix).

GREEN: in `VitestAdapter.run()`, match through the normalised form at all three
comparison sites. Build `ntarget = self.normalise_id(target)` and normalised
lookups of `verdict.passed` / `verdict.failed`
(`{self.normalise_id(t): t for t in ...}`), decide `PASSED`/`FAILED` against those,
and in the FAILED branch compare `self.normalise_id(self._id_for(...)) == ntarget`
when locating `target_failure`. The `NOT_COLLECTED`/`NOT_FOUND` fall-through is
unchanged. Collected ids are already in canonical (space) form, so `normalise_id`
is idempotent on them and the map keys collide with `ntarget` exactly when it is the
same test.

## Deliberate scope cuts (do not build)

- **No change to `advance.py`.** The `declared_test_mismatch` event, `_adopt_target`,
  and the `missing`/round-trip logic in `_handle_test_phase` stay exactly as they
  are — they remain correct for genuinely different targets. This fix removes the
  *false* mismatch at its source (the adapter), not the mismatch machinery.
- **`tdd target` normalisation.** `cmd_target` (`cli.py` line 1044) also matches a
  supplied id exactly against collected ids, and could in principle accept a
  separator-only variant too. It is a different command with its own `difflib`
  near-miss suggestion and is not the emit site named in #57. Leave it unchanged;
  if wanted it is a separate issue.
- **pytest / other adapters' normalisation.** pytest, exec, gradle and xctest
  adapters inherit the base identity hook. Only vitest has a describe/test separator
  ambiguity, so only vitest overrides. Do not invent normalisation rules for runners
  that do not need one.
- **End-to-end (`tdd advance`) test of the no-event / no-round-trip outcome.** The
  fix is proven at adapter altitude (cycle 3: `run()` returns `PASSED` instead of
  `NOT_FOUND`), which is exactly what `_handle_test_phase` keys off. A vitest
  end-to-end run would need node in CI, and this repo's run-level tests use the
  pytest `repo` fixture — where `::` ids have no ambiguity to exercise. Do not add a
  node-dependent e2e; the adapter test and the run_projects keying fact together
  establish the behaviour.
- **PRD/README documentation** of the per-adapter normalisation hook: same PR, after
  the run is terminal, as an ordinary commit — not a cycle (see Done-criteria).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** —
do not ask the user to start the run. `tdd run start` records which model is
executing, resolved from your own session; a run started by anyone else attributes
this work to the wrong agent.

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

The branch `feat/57-id-normalisation` already exists — it was created at hardening and
carries this plan's commit. Check it out; if it has grown unrelated work, stop and ask.

    git checkout feat/57-id-normalisation          # exists: created at hardening, carries this plan
    tdd doctor                                     # must report healthy: true
    tdd run start --plan tasks/issue-57-test-id-separator-normalisation.md

`tdd doctor` must be green first: if it reports "worktree clean" failing on *other*
uncommitted `tasks/issue-*.md` files (sibling plans not part of this work), commit, stash,
or gitignore them before `run start`.

Then repeat until done: read `next_action.verb`, do exactly what it says, run
`tdd advance`. Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log,
commit it, and raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or
  `git commit` cycle code — the tool stages and commits, deriving the file set from
  the phase. (The plan file is already committed on this branch from hardening.)
- The baseline is captured at `run start` and subtracted from later verdicts.
  Expected baseline for this repo: `{"tddcli": 0}` — anything else means a moved
  branch; stop.
- Verbs this plan can hit: `run_sensitivity_check` → `tdd sensitivity
  begin|check|end` (only if a RED passes on arrival — none is expected to;
  cycle 3's second assertion holds before GREEN but the *primary* RED does not);
  `resolve_blocker` → `tdd blocker --kind --detail` (kinds: `plan_defect`,
  `tooling`, `regression`, `pre_existing_failure`); `confirm_cycle_applicable` on a
  cycle the codebase has outgrown → `tdd cycle skip --reason`. This plan declares no
  `annotation_keys` and no refactor cycles.

## Done-criteria

**Before finishing:** run
`tdd log render --out tasks/friction-logs/issue-57-id-normalisation-friction.md` and
`tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped —
and every integrity event. Do not narrate what the ledger already records.

Then the documentation follow-up, committed as ordinary commits on the branch after
the run is terminal: a short note in the PRD/README adapter section (§10) that
`Adapter.normalise_id` is the per-adapter target-matching hook and that vitest
canonicalises the describe/test separator, so a formatting-only difference is no
longer a `declared_test_mismatch`.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-57-id-normalisation-friction.md
    git commit -m "docs: friction log for issue-57-id-normalisation"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates,
pushes the branch and opens the PR against `main`. Do not push or call the GitHub API
by hand. If a gate fails, fix it and re-run the skill — a failed gate is work, not a
reason to hand back.
