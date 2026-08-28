---
closes: 71
cycles:
  - n: 1
    project: tddcli
    title: "register refuses a pytest target without the :: separator"
    test: "tests/test_target_lint.py::test_register_refuses_a_pytest_target_without_separator"
    files: ["src/tddcli/target_lint.py", "src/tddcli/cli.py", "src/tddcli/adapters/base.py", "src/tddcli/adapters/pytest_adapter.py"]
    commit_red: "test: plan register refuses a pytest target with no ::"
    commit_green: "feat: target lint — adapter id-grammar hook, wired into plan register"

  - n: 2
    project: tddcli
    title: "a vitest target without ' > ' is flagged by the grammar hook"
    test: "tests/test_target_lint.py::test_vitest_target_without_describe_separator_is_flagged"
    files: ["src/tddcli/adapters/vitest_adapter.py"]
    commit_red: "test: vitest grammar lint requires the ' > ' separator"
    commit_green: "feat: vitest lint_target_id flags ids missing ' > '"

  - n: 3
    project: tddcli
    title: "a gradle target without the class/method slash is flagged"
    test: "tests/test_target_lint.py::test_gradle_target_without_slash_is_flagged"
    files: ["src/tddcli/adapters/gradle_adapter.py"]
    commit_red: "test: gradle grammar lint requires the classname/method slash"
    commit_green: "feat: gradle lint_target_id flags ids missing the / separator"

  - n: 4
    project: tddcli
    title: "an xctest target without Bundle/Class/method shape is flagged"
    test: "tests/test_target_lint.py::test_xctest_target_without_three_parts_is_flagged"
    files: ["src/tddcli/adapters/xctest_adapter.py"]
    commit_red: "test: xctest grammar lint requires Bundle/Class/testMethod"
    commit_green: "feat: xctest lint_target_id flags ids without three slash-parts"

  - n: 5
    project: tddcli
    title: "register refuses a target that duplicates the project root prefix"
    test: "tests/test_target_lint.py::test_register_refuses_a_root_duplicated_pytest_target"
    files: ["src/tddcli/target_lint.py", "src/tddcli/adapters/base.py", "src/tddcli/adapters/pytest_adapter.py"]
    commit_red: "test: a root-duplicated pytest target fails registration"
    commit_green: "feat: root-prefix duplication lint with suggested spelling"

  - n: 6
    project: tddcli
    title: "a genuinely nested root-named path is not flagged"
    test: "tests/test_target_lint.py::test_register_accepts_a_genuinely_nested_root_path"
    files: ["src/tddcli/target_lint.py"]
    commit_red: "test: an existing root/root path registers cleanly"
    commit_green: "feat: filesystem existence exempts genuine nested root paths"

  - n: 7
    project: tddcli
    title: "register refuses a root-duplicated vitest target"
    test: "tests/test_target_lint.py::test_register_refuses_a_root_duplicated_vitest_target"
    files: ["src/tddcli/adapters/vitest_adapter.py"]
    commit_red: "test: a root-duplicated vitest target fails registration"
    commit_green: "feat: vitest target_path feeds the root-duplication lint"

  - n: 8
    project: tddcli
    title: "run start refuses lint findings introduced by config drift"
    test: "tests/test_target_lint.py::test_run_start_refuses_lint_findings_from_config_drift"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: run start re-lints the stored contract against current config"
    commit_green: "feat: target lint gates run start before the baseline claim"
---

# Issue #71 — lint declared targets against project roots and adapter id conventions

https://github.com/geuben/tdd-cli/issues/71
Task file: `tasks/issue-71-target-lint.md`

## Context

Declared test targets are validated only by failing to match at execution time: a wrong
path convention costs `not_found` first runs, `declared_test_mismatch` events, and extra
advance round-trips — per cycle, mid-run. Two observed shapes: (1) a target whose path
duplicates the project's `root` (`scripts/__tests__/x.test.js` on a project whose root
*is* `scripts/`, collected as `__tests__/x.test.js`), and (2) separator spelling that can
never match the adapter's collected-id grammar (pytest `::`, vitest ` > `, JVM
`classname/method`, XCTest `Bundle/Class/testMethod`). Both are statically detectable
before anything executes. This plan adds a target lint that **hard-fails**
`tdd plan register` and `tdd run start` (before the baseline claim), with per-adapter
grammar knowledge owned by the adapters (§10) and the root-prefix rule verified against
the filesystem so genuine nested paths pass. Complements #57's runtime normalisation:
the lint catches author-side convention errors early; normalisation absorbs benign
formatting drift that remains.

## Design decisions (locked)

- **Hard-fail at registration** (user decision): findings refuse the command, listed in
  the envelope with a suggested corrected spelling where one is derivable. Matches R7.10 —
  a planning defect must surface at planner time, the cheapest possible.
- **No escape-hatch flag** (user decision): the heuristics are therefore conservative —
  grammar rules flag only shapes that can never match a collected id, and the root-prefix
  rule is exempted by filesystem evidence. The documented recovery for the rare
  legitimate `root/root/...` future path is to create the nested directory before
  registering (cycle 6's exemption then applies); the error message says so.
- **Both gates** (user decision): `run start` re-lints the stored contract against the
  *current* config before claiming the worktree or probing, catching contracts registered
  by an older tdd-cli and `tdd.toml` root/adapter drift since registration. Refusal uses
  the established `failure(..., reason="target_lint", findings=[...])` shape, before the
  claim so no half-started state is left behind.
- **Collection-based resolution is scope-cut** (user decision; see scope cuts) — in this
  repo pin cycles routinely name tests written during the run (every pin in
  `tasks/issue-67-baseline-sanity.md` does), so absence from the run-start collection is
  not evidence of error.
- **Grammar knowledge lives on adapters** (codebase evidence, §10 "adding an adapter
  requires no change to core logic"): a new base hook `lint_target_id(native_id) -> str |
  None` (default `None` — no complaint; exec stays grammar-free) plus a
  `target_path(native_id) -> str | None` hook returning the file-path portion for
  path-bearing ids (default `None`; pytest = the part before the first `::`, vitest = the
  part before the first ` > `). The shared rules live in a new `src/tddcli/target_lint.py`
  with `lint_cycles(cycles, cfg, worktree) -> list[dict]`, called from both CLI commands.
- **The lint replicates `Engine._qualify`'s project attribution exactly** (codebase
  evidence): a declared id may be `project::native` or `project/`-prefixed (both accepted
  today, the latter stripped), so lint imports and applies `Engine._qualify` before
  judging the native part — otherwise a `backend/tests/...` target on a project *named*
  `backend` (legal today, stripped by `_qualify`) would false-positive the root rule.
- **Root-duplication rule**: for a path-bearing target, when `project.root != "."` and
  the native path starts with `<root>/`, flag it — *unless* `worktree/<root>/<path>`
  exists or its parent directory exists (the genuine-nesting exemption, cycle 6). The
  finding carries `suggestion` = the path with the duplicated prefix stripped.
- **Grammar rules** (each flags only definitively-unmatchable shapes): pytest — native
  must contain `::`; vitest — native must contain ` > ` (a pytest-spelled
  `a.test.ts::name` therefore fails, which is the issue's shape 2); gradle — native must
  contain `/` (collected ids are always `classname/method`); xctest — native must be
  three `/`-separated parts (`Bundle/Class/testMethod`). exec — no grammar (ids are bare
  file paths).
- **Refactor cycles are skipped** (they declare no tests — enforced by `parse_cycle`);
  undeclared contracts (no cycles) pass trivially at both gates.

## Verified repo facts

*Anchors are symbol names — grep for them; no line numbers in this plan.*

- **No validation exists today — probed empirically.** A throwaway test on the conftest
  `repo` fixture registered (a) a pytest target with no `::` (`tests/test_add.py`) and
  (b) a root-duplicated target (`backend/tests/test_add.py::test_add` on a project named
  `proj` with `root = "backend"`): **both returned `ok: True`** with a normal
  `contract_id`. Probe deleted; tree clean.
- **The qualify path.** `Engine._qualify` (`machine.py`, staticmethod) returns the id
  unchanged when it is `project::`-prefixed for a declared project, strips a leading
  `<project-name>/`, else prefixes `projects[0]::`. It never consults `project.root` —
  which is exactly why shape 1 survives to `not_found`.
- **Adapter id grammars, read from the adapters.** pytest: report `nodeid`s
  (`tests/x.py::test_y`), matched by equality in `PytestAdapter.run`. vitest:
  `<project-root-relative file> > <space-joined fullName>` (`VitestAdapter._id_for`,
  module docstring), matched via `normalise_id` which requires the structural ` > `
  partition. gradle: `classname/method` (`GradleAdapter._parse_results` builds
  `f"{classname}/{method}"`). xctest: `Bundle/Class/testMethod` (`_CASE_RE`,
  `-only-testing:` format). exec: the root-relative file path (`ExecAdapter.collect`
  qualifies `rel`).
- **CLI landmarks.** `cmd_plan_register`: `contract_mod.register(...)` → the
  `parsed.status == "undeclared"` guard → the ledger `existing`/insert block; the lint
  call sits between the undeclared guard and the ledger lookup (worktree and cfg already
  in scope). `cmd_run_start`: `declared_cycles = contract_mod.cycles_from_json(...)` is
  assigned before the baseline-scoping block, which precedes `ledger.claim(...)`; the
  lint call sits immediately after that assignment, so a refusal never touches the claim
  or the probe. Refusal pattern: `failure(error, reason=..., **extras)` (`envelope.py`),
  as in `reason="baseline_in_progress"`.
- **Fixtures.** The conftest `repo` fixture is a git repo with one pytest project
  `backend` (`root = "backend"`, `lint = []`, `typecheck = []`, a passing
  `test_smoke.py`), plus `write_plan` (writes **and commits** — registration reads the
  blob at HEAD) and `run_cli` helpers. Tests may rewrite `tdd.toml` and commit, as
  `test_config_drift.py` does. Adapter-unit construction pattern:
  `tests/test_id_normalisation.py` (`vitest_adapter_for`/`pytest_adapter_for` — a tmp
  `tdd.toml`, `config_mod.load`, direct adapter construction); gradle/xctest adapters
  construct the same way (`tests/test_gradle_adapter.py`, `tests/test_xctest_adapter.py`).
- **Blast radius: empty.** No test registers a plan with a separator-free or
  name/root-prefixed target (`grep -rn 'test: "' tests/*.py | grep -v '::'` → nothing;
  `grep -rn 'test: "backend/' tests/*.py` → nothing). `tests/test_example_plan.py`
  exercises `contract.parse` directly, not the CLI, so register-time lint does not touch
  it; `examples/plan.md`'s targets are all well-formed anyway. No `modifies_tests`
  anywhere in this plan.
- **Suite is green now**: 406 passed on this branch. Expected `run start` baseline:
  `{"tddcli": 0}` — anything else means a moved branch; stop.
- **Lint is ruff-only, no typecheck** (`tdd.toml`), and every RED here fails at runtime
  (envelope assertion or `AttributeError` on a missing adapter method), never at
  collection — **no cycle needs `stub_expected`**. `src/tddcli/target_lint.py` is created
  in cycle 1's GREEN; no RED test imports it.

## Cycle detail

*Single project `tddcli`; all cycles standard; all tests in a new
`tests/test_target_lint.py`. Minimum GREEN throughout.*

**Cycle 1 — register refuses a pytest target without `::` (and builds the plumbing).**
Test: on the `repo` fixture, `write_plan` a one-cycle contract with
`test: "tests/test_add.py"`, `run_cli(repo, "plan", "register", plan)`; assert
`out["ok"] is False`, `out["result"]["reason"] == "target_lint"`, and the single finding
names cycle 1 with a problem mentioning `::`. *EXPECTED FAILURE (probed):* registration
currently returns `ok: True` with a `contract_id` — the `ok is False` assertion fails.
*GREEN:* add `Adapter.lint_target_id(native) -> str | None` (default `None`) and
`Adapter.target_path(native) -> str | None` (default `None`) to `adapters/base.py`;
implement `PytestAdapter.lint_target_id` (complain when `"::" not in native`); create
`src/tddcli/target_lint.py::lint_cycles(cycles, cfg, worktree)` — for each non-refactor
cycle and test, apply `Engine._qualify`, split off the project, build the adapter
(`adapters.build`), collect grammar complaints as
`{"cycle": n, "project": name, "test": declared, "problem": msg}`; call it in
`cmd_plan_register` between the undeclared guard and the ledger lookup, returning
`failure("declared targets failed lint", reason="target_lint", findings=...)` when
non-empty. Production targets: `target_lint.lint_cycles`, `cmd_plan_register`,
`Adapter.lint_target_id`, `PytestAdapter.lint_target_id`.

**Cycle 2 — vitest grammar.** Test: build a `VitestAdapter` via the
`test_id_normalisation.py` pattern; `msg = adapter.lint_target_id("a.test.ts::does a
thing")`; assert `msg` is truthy and mentions `' > '`. *EXPECTED FAILURE:* the base
default returns `None` — `assert msg` fails (`AssertionError`). *GREEN:*
`VitestAdapter.lint_target_id` complains when `" > " not in native`, naming the expected
`<file> > <describe titles> <test title>` shape. Production target:
`VitestAdapter.lint_target_id`.

**Cycle 3 — gradle grammar.** Test: build a `GradleAdapter` (tmp `tdd.toml`,
`adapter = "gradle"`); `msg = adapter.lint_target_id("com.foo.BarTest.testBaz")`; assert
`msg` is truthy and mentions `/`. *EXPECTED FAILURE:* base default `None` —
`AssertionError`. *GREEN:* complain when `"/" not in native` (collected ids are
`classname/method`). Production target: `GradleAdapter.lint_target_id`.

**Cycle 4 — xctest grammar.** Test: build an `XCTestAdapter` (tmp `tdd.toml`,
`adapter = "xctest"`, a `test_command` with `-scheme`); `msg =
adapter.lint_target_id("AppTests.RecTests.testStopsRecording")`; assert `msg` is truthy
and mentions `Bundle/Class`. *EXPECTED FAILURE:* base default `None` — `AssertionError`.
*GREEN:* complain unless the native id is exactly three `/`-separated non-empty parts.
Production target: `XCTestAdapter.lint_target_id`.

**Cycle 5 — root-prefix duplication (pytest, e2e, with suggestion).** Test: on the
`repo` fixture rewrite `tdd.toml` to `[project.proj]` with `root = "backend"` (project
*name* ≠ root, so `_qualify` strips nothing), commit; `write_plan` a contract on project
`proj` with `test: "backend/tests/test_add.py::test_add"`; register; assert
`ok is False`, `reason == "target_lint"`, and the finding's `suggestion ==
"tests/test_add.py::test_add"`. *EXPECTED FAILURE (probed):* registration returns
`ok: True` today (grammar passes — the id has `::`); the `ok is False` assertion fails.
*GREEN:* implement `PytestAdapter.target_path` (portion before the first `::`); in
`lint_cycles`, when `target_path` is non-None, `project.root != "."`, and the path starts
with `root + "/"`, emit a finding with `suggestion` = the target with that prefix
stripped. No filesystem exemption yet — cycle 6 forces it. Production targets:
`target_lint.lint_cycles`, `PytestAdapter.target_path`.

**Cycle 6 — genuine nesting is exempt.** Test: same `proj`/`root = "backend"` setup, but
first create `backend/backend/tests/test_add.py` (any content) and commit; register the
same contract; assert `ok is True`. *EXPECTED FAILURE:* cycle 5's minimal GREEN flags on
the prefix alone, so registration refuses — the `ok is True` assertion fails. (If it
passes on arrival because cycle 5 over-implemented, the tool's sensitivity path handles
it — run the check honestly; do not relabel.) *GREEN:* exempt the finding when
`worktree/<root>/<path>` exists or its parent directory exists; the remaining refusal
message documents "create the nested directory first" as the recovery for legitimate
future nested paths. Production target: `target_lint.lint_cycles`.

**Cycle 7 — root-prefix duplication for vitest.** Test: tmp-repo `tdd.toml` with
`[project.proj]`, `root = "scripts"`, `adapter = "vitest"`; `write_plan` a contract with
`test: "scripts/__tests__/x.test.js > does a thing"`; register; assert `ok is False`
with `reason == "target_lint"`. Registration never runs vitest, so no `npx` is needed.
*EXPECTED FAILURE:* `VitestAdapter.target_path` does not exist (base returns `None`), so
the shared root rule is skipped and registration returns `ok: True` — the assertion
fails. *GREEN:* `VitestAdapter.target_path` returns the portion before the first ` > `.
Production target: `VitestAdapter.target_path`.

**Cycle 8 — run start re-lints against current config.** Test: on the `repo` fixture,
write `tdd.toml` as `[project.proj]` with `root = "."` (commit), `write_plan` a contract
on `proj` with `test: "backend/tests/test_add.py::test_add"` (valid now: root `"."` is
exempt and grammar passes), register — must succeed; then rewrite `tdd.toml` to
`root = "backend"` and commit; `run_cli(repo, "run", "start", "--plan", plan)`; assert
`ok is False` and `result["reason"] == "target_lint"`. *EXPECTED FAILURE:* with no lint
at run start, the command claims, probes the fixture suite, and returns `ok: True` — the
assertion fails. *GREEN:* call `lint_cycles(declared_cycles, cfg, worktree)` in
`cmd_run_start` immediately after `declared_cycles` is assigned (before baseline scoping
and `ledger.claim`), refusing with the same envelope shape. Production target:
`cmd_run_start`.

## Deliberate scope cuts (do not build)

- **No collection-based target resolution at run start** (user decision). Premise: pin
  cycles in this repo's practice routinely name tests written during the run (every pin
  in `tasks/issue-67-baseline-sanity.md`), so absence from the run-start collection
  snapshot is not evidence of error, and the two observed failure shapes are both caught
  statically. *Re-evaluation trigger:* if execution of this plan (or a later run's
  friction log) shows a misspelled *existing* test surviving the static lint into
  mid-run `not_found`, raise a follow-up issue — do not bolt a collection check onto
  these cycles.
- **No escape-hatch flag** (user decision). Recovery paths are: fix the target spelling
  (the finding suggests one), or pre-create a genuinely nested directory (cycle 6's
  exemption). If a false positive with no such recovery appears in practice, that is a
  follow-up issue, not a mid-run patch.
- **No exec-adapter root-duplication lint.** Premise: minimal GREEN — no test demands an
  `ExecAdapter.target_path`, and no exec-project incident has been observed; exec ids
  are bare paths with no grammar to check. The shared rule picks it up the moment a
  `target_path` override is added.
- **`modifies_tests`, `stub_expected`, and `files` lists are not linted** — the issue is
  about *targets*; widening is a separate change (the declined "also check
  modifies_tests" option).
- **No fuzzy/edit-distance suggestions** beyond stripping the duplicated root prefix —
  `tdd target` already owns near-miss suggestion against observed collection mid-run.
- **#57's `normalise_id` is untouched** — runtime normalisation and static lint are
  complementary by design (the issue says so); the lint does not attempt to normalise,
  only to detect unmatchable shapes.
- **Mirrors: none.** The lint lives once; `examples/plan.md` and the forked handoff
  skill document front-matter *keys*, which this plan does not change. No
  `docs/INVARIANTS.md` registry exists in this repo.
- **README/PRD documentation** is a post-run doc follow-up, not a cycle (see
  Done-criteria).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do
not ask the user to start the run. `tdd run start` records which model is executing,
resolved from your own session; a run started by anyone else attributes this work to the
wrong agent.

**Referee rule:** run the *released* tdd-cli **0.8.0** at `~/.local/bin/tdd` (the
`uv tool` install), never a working-tree editable install. On this machine plain `tdd`
on PATH resolves to an editable venv importing from this working tree — check
`which tdd` and use the full path `~/.local/bin/tdd` in every command below if it is not
already first. Verify: `~/.local/bin/tdd --version` → `tdd-cli 0.8.0`. This plan adds no
ledger schema and uses only 0.8.0-supported front-matter keys.

    git checkout -b feat/71-target-lint            # first, before anything else
    ~/.local/bin/tdd doctor                        # must report healthy: true
    ~/.local/bin/tdd run start --plan tasks/issue-71-target-lint.md

If the branch already exists, do not force-checkout and do not pick another name: check
it out only if it carries this plan's commit and no unrelated work, otherwise stop and
ask. If `tdd doctor` fails on *other* uncommitted `tasks/issue-*.md` files (sibling
plans), commit, stash, or gitignore them before `run start`.

Then repeat until done: read `next_action.verb`, do exactly what it says, run
`~/.local/bin/tdd advance`. Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit
it, and raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase; the tool stages and commits from
  the phase — do not `git add`/`git commit` yourself.
- Expected baseline for this repo: `{"tddcli": 0}` — anything else means a moved branch;
  stop.
- This plan declares **no `annotation_keys`**, so `annotate_cycle` will not appear. All
  eight cycles are standard: `write_test` → `write_code` → optional refactor. A cycle
  whose test unexpectedly passes on arrival (cycle 6's note) drives
  `run_sensitivity_check` → `~/.local/bin/tdd sensitivity begin|check|end`. If blocked,
  `resolve_blocker` → `tdd blocker --kind --detail` (kinds: `plan_defect`, `tooling`,
  `regression`, `pre_existing_failure`); `confirm_cycle_applicable` on a cycle the code
  has outgrown → `tdd cycle skip --reason`.

## Done-criteria

**Before finishing:** run
`~/.local/bin/tdd log render --out tasks/friction-logs/issue-71-target-lint-friction.md`
(the `tasks/friction-logs/` at the **repository root**) and `~/.local/bin/tdd metrics`.
Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity
event. Do not narrate what the ledger already records.

Then the documentation follow-up, committed as ordinary commits after the run is
terminal: in `docs/PRD.md`, extend the `tdd plan register` and `tdd run start` rows of
the command table with the target lint (grammar + root-prefix rules, the
`reason: "target_lint"` refusal, and the create-the-nested-directory recovery note).

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-71-target-lint-friction.md
    git commit -m "docs: friction log for issue-71-target-lint"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes
the branch and opens the PR against `main`. Do not push or call the GitHub API by hand.
If a gate fails, fix it and re-run the skill — a failed gate is work, not a reason to
hand back.
