---
closes: 119
cycles:
  - n: 1
    project: tddcli
    title: "plan paths resolves a pytest cycle's test id to a repository-relative path"
    test: "tests/test_plan_paths.py::test_resolves_a_pytest_target_to_a_repository_path"
    files: ["src/tddcli/plan_paths.py", "src/tddcli/cli.py"]
    commit_red: "test: plan paths resolves a pytest target to a repository path"
    commit_green: "feat: tdd plan paths — resolve a plan's test ids to file paths"

  - n: 2
    project: tddcli
    title: "modifies_tests ids are resolved too, labelled with their field"
    test: "tests/test_plan_paths.py::test_resolves_modifies_tests_ids_labelled_with_their_field"
    files: ["src/tddcli/plan_paths.py"]
    commit_red: "test: plan paths resolves modifies_tests ids under their field label"
    commit_green: "feat: resolve modifies_tests alongside each cycle's target"

  - n: 3
    project: tddcli
    pin_cycle: true
    title: "every accepted qualification form resolves to the same path"
    test: "tests/test_plan_paths.py::test_every_qualification_form_resolves_to_the_same_path"
    files: ["src/tddcli/plan_paths.py"]
    commit_pin: "test: pin the three accepted id qualification forms"

  - n: 4
    project: tddcli
    title: "a project root of '.' yields a path with no './' prefix"
    test: "tests/test_plan_paths.py::test_a_root_project_yields_an_unprefixed_path"
    files: ["src/tddcli/plan_paths.py"]
    commit_red: "test: a root-'.' project resolves to an unprefixed path"
    commit_green: "feat: normalise the joined path so a '.' root adds no prefix"

  - n: 5
    project: tddcli
    title: "a cargo lib:: id is reported unresolved with reason no_path_in_id"
    test: "tests/test_plan_paths.py::test_a_cargo_lib_id_is_unresolved_with_no_path_in_id"
    files: ["src/tddcli/plan_paths.py"]
    commit_red: "test: a cargo lib:: id lands in unresolved with no_path_in_id"
    commit_green: "feat: ids whose adapter carries no path land in unresolved"

  - n: 6
    project: tddcli
    pin_cycle: true
    title: "unresolved ids do not fail the command"
    test: "tests/test_plan_paths.py::test_unresolved_ids_do_not_fail_the_command"
    files: ["src/tddcli/plan_paths.py"]
    commit_pin: "test: pin exit 0 when some ids are unresolved"

  - n: 7
    project: tddcli
    pin_cycle: true
    title: "a cargo integration-test id resolves under the project root"
    test: "tests/test_plan_paths.py::test_a_cargo_integration_test_id_resolves_under_the_project_root"
    files: ["src/tddcli/plan_paths.py"]
    commit_pin: "test: pin cargo tests/<stem>.rs resolution under a nested root"

  - n: 8
    project: tddcli
    pin_cycle: true
    title: "a refactor cycle's modifies_tests are resolved although it declares no test"
    test: "tests/test_plan_paths.py::test_a_refactor_cycles_modifies_tests_are_resolved"
    files: ["src/tddcli/plan_paths.py"]
    commit_pin: "test: pin modifies_tests resolution on a testless refactor cycle"

  - n: 9
    project: tddcli
    title: "the gradle adapter resolves an id to its Kotlin source file by scanning sources"
    test: "tests/test_plan_paths.py::test_gradle_scans_sources_to_map_an_id_to_its_file"
    stub_expected: ["src/tddcli/adapters/base.py"]
    files: ["src/tddcli/adapters/base.py", "src/tddcli/adapters/gradle_adapter.py"]
    commit_red: "test: gradle maps a declared id to its Kotlin source file"
    commit_green: "feat: Adapter.scan_target_paths, implemented for gradle"

  - n: 10
    project: tddcli
    title: "the xctest adapter resolves an id to its Swift source file by scanning sources"
    test: "tests/test_plan_paths.py::test_xctest_scans_sources_to_map_an_id_to_its_file"
    files: ["src/tddcli/adapters/xctest_adapter.py"]
    commit_red: "test: xctest maps a declared id to its Swift source file"
    commit_green: "feat: xctest scan_target_paths over the Swift source grep"

  - n: 11
    project: tddcli
    title: "the resolver consults the source scan when the adapter's target_path is None"
    test: "tests/test_plan_paths.py::test_a_gradle_id_resolves_through_the_source_scan"
    files: ["src/tddcli/plan_paths.py"]
    commit_red: "test: a gradle id in a plan resolves through the source scan"
    commit_green: "feat: fall back to the adapter's source scan, cached per project"

  - n: 12
    project: tddcli
    title: "a scan that does not match exactly one file says why"
    test: "tests/test_plan_paths.py::test_a_scan_that_matches_other_than_one_file_says_why"
    files: ["src/tddcli/plan_paths.py"]
    commit_red: "test: not_found_in_sources and ambiguous_id reasons"
    commit_green: "feat: distinguish a missed scan from an ambiguous one"

  - n: 13
    project: tddcli
    title: "a plan that cannot be turned into a contract refuses cleanly"
    test: "tests/test_plan_paths.py::test_a_plan_that_is_not_a_contract_refuses_cleanly"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: plan paths refuses an unknown project and a missing file"
    commit_green: "feat: plan paths refuses malformed and unreadable plans with ok:false"

  - n: 14
    project: tddcli
    title: "the bare command renders a human table"
    test: "tests/test_plan_paths.py::test_the_bare_command_renders_a_human_table"
    files: ["src/tddcli/plan_paths.py", "src/tddcli/cli.py"]
    commit_red: "test: bare plan paths renders a human table"
    commit_green: "feat: human table for plan paths; --json selects the envelope"

  - n: 15
    project: tddcli
    pin_cycle: true
    title: "the bare command emits no JSON envelope alongside the table"
    test: "tests/test_plan_paths.py::test_the_bare_command_emits_no_json_envelope"
    files: ["src/tddcli/plan_paths.py"]
    commit_pin: "test: pin that the rendered table is not followed by an envelope"
ancillary_files:
  - "README.md"
  - "docs/PRD.md"
---

# Issue #119 — `tdd plan paths`: resolve a plan's test ids to repository file paths

https://github.com/geuben/tdd-cli/issues/119
Task file: `tasks/issue-119-plan-paths.md`

## Context

A plan's `test` / `tests` / `modifies_tests` entries name **tests**, not files. Turning one
into the other needs each adapter's id grammar, `Engine._qualify`'s three accepted
qualification forms, and the project roots in `tdd.toml`. Only tdd-cli holds all three.

Tools that read plans therefore cannot. [perturb](https://github.com/geuben/perturb)
subtracts a plan's declared files from what a run touched; because test ids are not paths,
every run's test edits are reported as touching files outside the plan
(geuben/perturb#4). Reproducing the mapping outside tdd-cli means copying every adapter's
`target_path`, the qualification rules and the root joins — a copy that drifts the moment an
adapter changes or a plugin is registered.

This issue adds the missing query:

    tdd plan paths <plan-file> [--json]

Read-only. It needs no run and no prior `tdd plan register`, and writes nothing to the
ledger. Ids that cannot be resolved are reported, not fatal.

## Design decisions (locked)

1. **Output shape — human table by default, `--json` returns the envelope.**
   *User-decided.* This is the established convention for the repo's other query commands
   (`cmd_progress`, `cmd_fleet` in `src/tddcli/cli.py`): bare invocation writes a rendered
   table to stdout and returns `Envelope(..., silent=True)`; `--json` returns the envelope
   whose `result` is the issue's object. The alternative — always JSON, with `--json` inert
   — advertises a flag that does nothing, which is the mechanism footgun that produced
   silently-ignored flags before.

2. **Plan source — the working-tree file, read with `Path.read_text()`.**
   *User-decided.* `contract.register` reads the blob at HEAD because the plan's *commit*
   is the contract (R7.2/R7.11). A read-only query pins no contract, and the issue states
   the command needs no prior registration; requiring a commit would block the planner's
   most useful moment, checking ids before committing the contract. The command therefore
   calls `contract.parse(text, rel, cfg)` directly, never `contract.register`.

3. **Parsing passes `cfg`, so an unknown project refuses.** *Codebase-answered.*
   `contract.parse_cycle` already raises `ContractError` when a cycle names a project
   absent from `tdd.toml` — probe output:
   `ContractError: cycle 1: unknown project 'nosuch'; registered: ['backend']`. The issue
   requires a refusal in exactly that case, so the existing check is the mechanism; the
   command catches `ContractError` and returns `failure(f"malformed plan contract: {exc}")`,
   matching `cmd_plan_register`'s wording.

4. **Qualification reuses `Engine._qualify` verbatim — it is not reimplemented.**
   *Issue-mandated, codebase-verified.* The probe confirmed all three accepted forms
   collapse to one native id (see the multi-form table below). Cycle 1's GREEN must route
   through `Engine._qualify`; cycle 3 pins that it did.

5. **Path derivation: `os.path.normpath(os.path.join(project.root, adapter.target_path(native)))`.**
   *Codebase-answered.* `target_path` is already the per-adapter file-portion hook added by
   issue #71 (`src/tddcli/adapters/base.py`, overridden in pytest, vitest and cargo).
   `normpath` is load-bearing: `os.path.join(".", "tests/x.py")` is `'./tests/x.py'`
   (verified), and a `./`-prefixed path will not match what a caller diffs against git.

6. **Existence on disk is never required.** *Codebase-answered.* A standard cycle's RED test
   file does not exist until that cycle writes it (`stub_expected` exists precisely for
   this), and perturb wants the path regardless. The resolver derives paths syntactically
   and does not stat them. The one exception is the gradle/xctest scan, which is a
   filesystem walk by construction.

7. **gradle and xctest resolve by scanning test sources — a new adapter hook.**
   *Issue-offered, built now (Scope policy).* Their ids name a class, not a file, so
   `target_path` returns `None`. Both adapters already grep their sources during collection.
   The plan adds `Adapter.scan_target_paths(self) -> dict[str, str]` — native id →
   **project-root-relative** path — defaulting to `{}` on the base class, implemented by
   `GradleAdapter` (reusing `_test_files` + `_grep_tests`) and `XCTestAdapter` (reusing
   `_test_files` + `_grep_swift_tests` + `_bundle_from_test_command`). The resolver consults
   it only when `target_path` returns `None`.
   `XCTestAdapter.collect()` must **not** be used: it shells out to
   `xcodebuild test -enumerate-tests` first. The scan uses the grep path directly, so the
   command stays toolchain-free — which is also why `GradleAdapter.collectable()` already
   reports `ok=True` unconditionally.

8. **The scan runs at most once per project per invocation.** *Mechanism footgun.* Calling
   `scan_target_paths()` per id would re-read every test source once per declared id. The
   resolver memoises by project name for the life of one call.

9. **Unresolved reasons are a closed set** (an unresolved row carries `cycle`, `field`,
   `id`, `project`, `reason`):
   - `no_path_in_id` — the adapter's ids never carry a file path and it offers no scan:
     cargo `lib::…` (verified: `target_path('lib::inner::tests::unit_thing')` is `None`),
     and the `exec` adapter, which inherits the base `target_path` returning `None`.
   - `not_found_in_sources` — a scanning adapter scanned and the id was not among the
     ids it found.
   - `ambiguous_id` — the scan matched the id in more than one file. Reachable and verified:
     the gradle grep attributes `pkg.Class/method` from the package declaration and is not
     scope-aware, so two files declaring the same package and class both claim the id.
     Reporting the ambiguity beats picking one arbitrarily, because a caller subtracting
     paths would then subtract the wrong file.

10. **Exit code is 0 whenever the contract parsed**, however many ids are unresolved
    (issue-mandated; pinned by cycle 6). `ok: false` is reserved for a plan that could not
    be turned into a contract at all.

11. **Row order is deterministic**: cycles ascending by ordinal, then `test` ids before
    `modifies_tests` ids, then declaration order within each field. A plan that names the
    same id in two cycles produces two rows — the `cycle` key is what distinguishes them.
    Determinism matters because perturb will diff this output across runs.

12. **Production targets.** A new module `src/tddcli/plan_paths.py` holds both
    `resolve(contract, cfg, worktree) -> dict` and `render(result) -> str`. Module-local
    rendering follows `src/tddcli/fleet.py`, which pairs `summarise` with `render`;
    `src/tddcli/render.py` is the *ledger* projection module and takes a `Ledger`, which
    this command never opens. `src/tddcli/cli.py` gains `cmd_plan_paths` and the
    `plan paths` subparser next to `plan register`.

### Multi-form surface: accepted id spellings (E-12c)

`Engine._qualify` (`src/tddcli/machine.py`) defines the accepted set. Probe output for a
cycle declaring `project: backend`:

| Declared form | Example | Qualifies to | Verdict |
|---|---|---|---|
| bare native id | `tests/test_add.py::test_add` | `backend::tests/test_add.py::test_add` | accepted |
| `<project>/` prefix | `backend/tests/test_add.py::test_add` | `backend::tests/test_add.py::test_add` | accepted, equivalent |
| `<project>::` prefix | `backend::tests/test_add.py::test_add` | `backend::tests/test_add.py::test_add` | accepted, equivalent |

All three are **equivalent** and must produce the same `path` and the same `project`.
Cycle 3 pins all three in one table-driven test.

Two forms are deliberately *not* special-cased, because `_qualify` does not special-case
them either and this command must mirror it exactly rather than improve on it:

- a `<project>::` prefix naming a project **not** in the cycle's own `projects` list falls
  through to the first declared project, and the foreign prefix stays inside the native id;
- a `contract_cycle` declaring `projects: [a, b]` resolves every unprefixed id against `a`.

Both are `_qualify`'s semantics. Reproducing them is the whole point — a caller must get the
same answer tdd-cli itself would act on.

## Deliberate scope cuts (do not build)

1. **Normalising `files`, `stub_expected` and `ancillary_files`.** Premise: **named non-goal**
   — the issue's "Out of scope" section says so, and they are already repository-relative
   paths.
2. **`--at-head` to read the committed blob instead of the working tree.** Premise:
   **user-deferred** — offered in Phase C as a third option and not chosen.
3. **A `tdd plan paths` row in `examples/skills/tdd-handoff/SKILL.md`.** Premise: **named
   non-goal by construction** — the command is a query for external plan readers, not a step
   in the planning or driving loop, and it introduces no verb. The skill's command
   inventory is unchanged.

There are no evidence-dependent cuts: none of the three premises rests on evidence this run
will produce.

## Mirrors

`examples/skills/tdd-handoff/SKILL.md` is a public fork of the private planning skill and
mirrors its prose. This plan changes neither — see scope cut 3 — so no parity cycle is
needed. No production file in this plan's `files` lists has a counterpart implementation
elsewhere in the repository; `src/tddcli/plan_paths.py` is new, and the adapter hook is
declared once on the base class and overridden, not duplicated.

There is **no `docs/INVARIANTS.md`** in this repository, so no registry entry is added or
reconciled.

## Cycles

### Cycle 1 — a pytest cycle's `test` id resolves to a repository-relative path

The command turns one declared id into one path row.

Test: `tests/test_plan_paths.py::test_resolves_a_pytest_target_to_a_repository_path`.
Using the `repo` fixture (project `backend`, root `backend`, pytest) and `write_plan`, a
plan whose cycle 1 declares `test: "tests/test_add.py::test_add"`; the single assertion is
that `run_cli(repo, "plan", "paths", plan, "--json")["result"]["paths"]` equals
`[{"cycle": 1, "field": "test", "id": "tests/test_add.py::test_add", "project": "backend",
"path": "backend/tests/test_add.py"}]`.

Production target: new module `src/tddcli/plan_paths.py`, function `resolve(contract, cfg,
worktree)` returning `{"plan": contract.plan_path, "paths": [...], "unresolved": []}`; and
`cmd_plan_paths` plus the `plan paths` subparser in `src/tddcli/cli.py`. `resolve` walks
`contract.cycles`, qualifies each id with `Engine._qualify`, splits the project off,
builds the adapter with `adapters.build(cfg.project(name), worktree)` and joins
`project.root` with `adapter.target_path(native)`.

**EXPECTED FAILURE** (verified empirically): argparse refuses the unknown subcommand —
stderr carries `tdd plan: error: argument plan_command: invalid choice: 'paths' (choose
from register)`, `main` catches the `SystemExit` and returns `2`, so stdout is empty and
`run_cli`'s `json.loads` fails with
`json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`.

### Cycle 2 — `modifies_tests` ids resolve too, labelled with their field

Test: `tests/test_plan_paths.py::test_resolves_modifies_tests_ids_labelled_with_their_field`.
A plan cycle declaring a `test` and one `modifies_tests` entry; the single assertion is that
the rows whose `field` is `"modifies_tests"` are exactly the one expected row.

Production target: `resolve` in `src/tddcli/plan_paths.py` — iterate
`(("test", cycle.tests), ("modifies_tests", cycle.modifies_tests))` per cycle instead of
`cycle.tests` alone.

**EXPECTED FAILURE**: `AssertionError` — cycle 1's GREEN walks only `cycle.tests`, so the
`modifies_tests` filter is empty (`assert [] == [{...}]`).

### Cycle 3 — every accepted qualification form resolves to the same path *(pin)*

Test: `tests/test_plan_paths.py::test_every_qualification_form_resolves_to_the_same_path`.
Table-driven over the three accepted forms in the multi-form table above; the single
assertion is that every form yields the same `(project, path)` pair.

**This cycle must pass on arrival.** It characterises `Engine._qualify`, which cycle 1's
GREEN is required to use rather than reimplement (decision 4). If it fails on arrival, the
defect is in cycle 1's GREEN — a hand-rolled prefix split — and the fix is to route cycle
1's code through `Engine._qualify`, never to weaken this test.

**EXPECTED FAILURE**: none — it passes on arrival. Probe evidence: `_qualify` mapped all
three spellings to `backend::tests/test_add.py::test_add`.

### Cycle 4 — a project root of `.` yields a path with no `./` prefix

Test: `tests/test_plan_paths.py::test_a_root_project_yields_an_unprefixed_path`.
Resolver-level, against a `tdd.toml` whose only project has `root = "."` (the shape the
`flat_repo` fixture in `tests/test_single_project_repo.py` uses); the single assertion is
that the resolved path is `tests/test_add.py`.

Production target: `resolve` in `src/tddcli/plan_paths.py` — wrap the join in
`os.path.normpath`.

**EXPECTED FAILURE** (verified empirically): `os.path.join(".", "tests/test_add.py")` is
`'./tests/test_add.py'`, so
`AssertionError: assert './tests/test_add.py' == 'tests/test_add.py'`.

### Cycle 5 — a cargo `lib::` id is reported unresolved with `no_path_in_id`

Test: `tests/test_plan_paths.py::test_a_cargo_lib_id_is_unresolved_with_no_path_in_id`.
Resolver-level, against a `tdd.toml` with one cargo project rooted at `crates/dd-bridge`
and a plan declaring `modifies_tests: ["lib::inner::tests::unit_thing"]`; the single
assertion is that `result["unresolved"]` is the one expected row, carrying
`"reason": "no_path_in_id"`.

Production target: `resolve` in `src/tddcli/plan_paths.py` — when `target_path` returns
`None`, append an unresolved row rather than joining.

**EXPECTED FAILURE**: a runtime failure whose exact form depends on cycle 1's GREEN —
either `AssertionError: assert [] == [{...}]` if that GREEN initialised `unresolved` to an
empty list, or `TypeError: join() argument must be str, bytes, or os.PathLike object, not
'NoneType'` if it joined the `None` unconditionally. Both are legitimate REDs: the test
collects and runs. Probe evidence for the input:
`CargoAdapter.target_path('lib::inner::tests::unit_thing')` returns `None`.

### Cycle 6 — unresolved ids do not fail the command *(pin)*

Test: `tests/test_plan_paths.py::test_unresolved_ids_do_not_fail_the_command`. The same
cargo plan as cycle 5 through the CLI; the single assertion is that the envelope's `ok` is
`True` although `unresolved` is non-empty.

**This cycle must pass on arrival** — cycle 5's GREEN records an unresolved row inside an
ordinary success envelope. If it fails on arrival, cycle 5's GREEN turned an unresolved id
into a refusal, which contradicts the issue; fix cycle 5's code, not this test.

**EXPECTED FAILURE**: none — it passes on arrival.

### Cycle 7 — a cargo integration-test id resolves under the project root *(pin)*

Test:
`tests/test_plan_paths.py::test_a_cargo_integration_test_id_resolves_under_the_project_root`.
Resolver-level, same cargo project; the single assertion is that
`adapter_host_catalog::host_catalog_lists_each_running` resolves to
`crates/dd-bridge/tests/adapter_host_catalog.rs`.

**This cycle must pass on arrival** — `CargoAdapter.target_path` already exists and cycle
1's GREEN joins whatever it returns with the project root. It pins that the join is generic
across adapters and nested roots rather than pytest-shaped.

**EXPECTED FAILURE**: none — it passes on arrival. Probe evidence: that id's `target_path`
is `tests/adapter_host_catalog.rs`, joining to
`crates/dd-bridge/tests/adapter_host_catalog.rs`.

### Cycle 8 — a refactor cycle's `modifies_tests` are resolved *(pin)*

Test: `tests/test_plan_paths.py::test_a_refactor_cycles_modifies_tests_are_resolved`.
A plan whose second cycle is `refactor_cycle: true` with no `test` and one `modifies_tests`
entry; the single assertion is that a row for that id is present with `"cycle": 2`.

**This cycle must pass on arrival** — cycle 2's GREEN walks `modifies_tests` for every
cycle regardless of kind. It guards against a later reader restricting the walk to cycles
that declare a target, which would silently drop every refactor cycle's test edits — the
exact class of omission this command exists to prevent.

**EXPECTED FAILURE**: none — it passes on arrival. Probe evidence: a `refactor_cycle`
declaring `modifies_tests: ["other_file::some_test"]` resolved to
`crates/dd-bridge/tests/other_file.rs`.

### Cycle 9 — gradle maps an id to its Kotlin source file by scanning sources

Test: `tests/test_plan_paths.py::test_gradle_scans_sources_to_map_an_id_to_its_file`.
Adapter-level, following the `gradle_adapter_for(tmp_path)` helper style in
`tests/test_target_lint.py`: a `tdd.toml` with a gradle project rooted at `app`,
`test_paths = ["src/test/"]`, and one Kotlin file at
`app/src/test/kotlin/com/example/feature/BarTest.kt` declaring
`package com.example.feature`, `class BarTest` and an `@Test fun rejectsAnEmptyName()`.
The single assertion is that `adapter.scan_target_paths()` equals
`{"com.example.feature.BarTest/rejectsAnEmptyName":
"src/test/kotlin/com/example/feature/BarTest.kt"}`.

Production targets: `Adapter.scan_target_paths(self) -> dict[str, str]` in
`src/tddcli/adapters/base.py`, returning `{}`; and the override in
`src/tddcli/adapters/gradle_adapter.py`, which walks `self._test_files()`, calls
`self._grep_tests(path)` per file, strips the `<project>::` prefix with `self.strip`, and
maps each native id to `str(path.relative_to(self.root))`. `OSError` on one file is
skipped, matching `collect()`'s per-file tolerance (R10.3).

`stub_expected` declares `src/tddcli/adapters/base.py`: the RED test calls a method that
exists nowhere today, and without the base-class signature stub the failure is
`AttributeError`, not an assertion. The stub is the hook and its `{}` body — no scanning
logic, and nothing in `gradle_adapter.py`.

**EXPECTED FAILURE** (verified empirically): with the declared stub in place,
`AssertionError: assert {} == {'com.example.feature.BarTest/rejectsAnEmptyName':
'src/test/kotlin/com/example/feature/BarTest.kt'}`.

### Cycle 10 — xctest maps an id to its Swift source file by scanning sources

Test: `tests/test_plan_paths.py::test_xctest_scans_sources_to_map_an_id_to_its_file`.
Adapter-level, following `xctest_adapter_for(tmp_path)` in `tests/test_target_lint.py`: a
project rooted at `ios` with `test_paths = ["AppTests/"]` and
`test_command = "xcodebuild test -scheme AppTests"`, plus `ios/AppTests/RecTests.swift`
declaring `class RecTests: XCTestCase` and `func testStopsRecording()`. The single
assertion is that `adapter.scan_target_paths()` equals
`{"AppTests/RecTests/testStopsRecording": "AppTests/RecTests.swift"}`.

Production target: the override in `src/tddcli/adapters/xctest_adapter.py`, walking
`self._test_files()` and calling `self._grep_swift_tests(path, self._bundle_from_test_command())`.
It must **not** call `collect()`, which shells out to `xcodebuild test -enumerate-tests`
first (decision 7).

**EXPECTED FAILURE** (verified empirically): `XCTestAdapter` inherits the base `{}`, so
`AssertionError: assert {} == {'AppTests/RecTests/testStopsRecording':
'AppTests/RecTests.swift'}`. Probe evidence: the bundle resolved from `-scheme AppTests`
and the grep produced `ios::AppTests/RecTests/testStopsRecording`.

### Cycle 11 — the resolver consults the scan when `target_path` is `None`

Test: `tests/test_plan_paths.py::test_a_gradle_id_resolves_through_the_source_scan`.
Resolver-level, the cycle-9 gradle tree plus a plan declaring
`test: "com.example.feature.BarTest/rejectsAnEmptyName"` on that project; the single
assertion is that the resolved path is
`app/src/test/kotlin/com/example/feature/BarTest.kt`.

Production target: `resolve` in `src/tddcli/plan_paths.py` — when `target_path` returns
`None`, consult `adapter.scan_target_paths()`, memoised by project name for the life of the
call (decision 8), and join the hit with the project root.

**EXPECTED FAILURE**: `AssertionError` — the id is still in `unresolved` with
`no_path_in_id`, so `result["paths"]` is empty (`assert [] == [{...}]`).

### Cycle 12 — a scan that does not match exactly one file says why

One behaviour: a scan-backed id that does not resolve to exactly one file reports which
kind of failure it was.

Test: `tests/test_plan_paths.py::test_a_scan_that_matches_other_than_one_file_says_why`.
Table-driven over two gradle trees — one where the declared id is absent from every source
file, and one where two files (`app/src/test/kotlin/com/example/feature/BarTest.kt` and
`app/src/test/kotlin/dup/BarTest.kt`) both declare `package com.example.feature` and
`class BarTest`. The single assertion is that the reasons are
`["not_found_in_sources", "ambiguous_id"]` respectively.

Production target: `resolve` in `src/tddcli/plan_paths.py` — map each native id to the
**set** of files claiming it; exactly one is a path row, zero is `not_found_in_sources`,
more than one is `ambiguous_id`.

**EXPECTED FAILURE**: `AssertionError: assert ['no_path_in_id', ...] ==
['not_found_in_sources', 'ambiguous_id']` — cycle 11's GREEN reports only the found case
and falls back to `no_path_in_id` otherwise. Probe evidence that the ambiguous branch is
reachable: two files each yielded `app::com.example.feature.BarTest/rejectsAnEmptyName`.

### Cycle 13 — a plan that cannot be turned into a contract refuses cleanly

Test: `tests/test_plan_paths.py::test_a_plan_that_is_not_a_contract_refuses_cleanly`.
Table-driven over the two ways the command has no contract to report on: a plan whose cycle
names a project absent from `tdd.toml`, and a path that does not exist. The single
assertion is that both envelopes have `ok` `False`.

Production target: `cmd_plan_paths` in `src/tddcli/cli.py` — read the working-tree file
inside `try/except OSError`, parse inside `try/except contract_mod.ContractError`, and
return `failure(...)` for each, mirroring `cmd_plan_register`'s
`f"malformed plan contract: {exc}"` wording for the parse case.

**EXPECTED FAILURE**: the first table row raises out of `cmd_plan_paths` —
`tddcli.contract.ContractError: cycle 1: unknown project 'nosuch'; registered: ['backend']`
(verified empirically; `main` catches only `ConfigError`, `GitError`, `LedgerVersionError`
and `SystemExit`, so it propagates into the test). The second row would raise
`FileNotFoundError`. Both are runtime failures of a collected test, not collection errors.

### Cycle 14 — the bare command renders a human table

Test: `tests/test_plan_paths.py::test_the_bare_command_renders_a_human_table`. The cycle-1
plan invoked without `--json` via `run_cli_text`; the single assertion is that the
`cycle  field  project  path` header line and the row containing
`backend/tests/test_add.py` are both present in stdout — one table, asserted as one
rendered block.

Production targets: `render(result) -> str` in `src/tddcli/plan_paths.py` (module-local,
following `src/tddcli/fleet.py`), and `cmd_plan_paths` in `src/tddcli/cli.py` branching on
`args.json` exactly as `cmd_fleet` does: `--json` returns the envelope, bare writes
`render(...)` to stdout and returns the envelope with `silent=True`.

The header line, the summary line (`<n> ids · <n> resolved · <n> unresolved`) and the
unresolved rows (`— unresolved (<reason>): <id>`) are all part of this one renderer.

**EXPECTED FAILURE**: `AssertionError` — stdout today is the JSON envelope, so the string
`cycle  field` does not appear in it.

### Cycle 15 — the bare command emits no JSON envelope alongside the table *(pin)*

Test: `tests/test_plan_paths.py::test_the_bare_command_emits_no_json_envelope`. The same
bare invocation; the single assertion is that `"envelope_version"` does not appear in
stdout.

**This cycle must pass on arrival** — cycle 14's GREEN returns the envelope with
`silent=True`, which is what suppresses the second write. If it fails on arrival, cycle
14's GREEN omitted `silent=True` and stdout carries a table followed by JSON, breaking
every consumer that does `json.loads(stdout)`; fix cycle 14's code, not this test.

**EXPECTED FAILURE**: none — it passes on arrival.

## Detection claims

No test in this plan derives its expected value by calling the code under test. Every
expected path is a literal written into the test (`backend/tests/test_add.py`,
`crates/dd-bridge/tests/adapter_host_catalog.rs`,
`src/test/kotlin/com/example/feature/BarTest.kt`, `AppTests/RecTests.swift`), taken from
the probe output rather than recomputed. Cycle 3 is the one comparison between two
computed values, and that is deliberate: it asserts three *inputs* agree, which is the
behaviour under test.

## Fakes and ports

This plan introduces no test double over a port or repository. Every test runs against real
`Config`, real `Adapter` instances and real files on disk in `tmp_path`; the gradle and
xctest scans read genuine Kotlin and Swift source files. There is therefore no fake/real
divergence table to rule on, and no production path left untested by substitution.

## Test seams

Two seams, both already established in this repository:

- **CLI-level** (cycles 1, 2, 3, 6, 13, 14, 15): `run_cli` / `run_cli_text` / `write_plan`
  from `tests/conftest.py`, over the `repo` fixture. These need a git worktree because
  `_worktree()` resolves one.
- **Resolver-level** (cycles 4, 5, 7, 8, 11, 12): call `plan_paths.resolve(contract, cfg,
  worktree)` directly against a `tdd.toml` written into `tmp_path`, with the contract from
  `contract.parse(PLAN_TEXT, "tasks/p.md", cfg)`. No git repository is needed, which is
  what makes cargo, gradle and xctest projects cheap to express. This is the same seam
  `tests/test_target_lint.py` uses for its per-adapter cases.
- **Adapter-level** (cycles 9, 10): construct `GradleAdapter` / `XCTestAdapter` directly,
  mirroring `gradle_adapter_for` / `xctest_adapter_for` in `tests/test_target_lint.py`.

`resolve` taking `(contract, cfg, worktree)` rather than reading the plan itself is what
makes the resolver-level seam possible; file reading and refusal live in `cmd_plan_paths`.

## Guards and negative space

Illegal or degenerate inputs, and where each is pinned:

| Input | Behaviour | Pinned by |
|---|---|---|
| id whose adapter carries no path (`lib::`, `exec`) | unresolved, `no_path_in_id` | cycle 5 |
| id a scanning adapter cannot find | unresolved, `not_found_in_sources` | cycle 12 |
| id a scan finds in several files | unresolved, `ambiguous_id` | cycle 12 |
| any number of unresolved ids | still `ok: true` | cycle 6 |
| cycle naming a project absent from `tdd.toml` | `ok: false`, refusal | cycle 13 |
| plan path that does not exist | `ok: false`, refusal | cycle 13 |
| refactor cycle (no `test` declared) | its `modifies_tests` still resolve | cycle 8 |
| project root `.` | path carries no `./` prefix | cycle 4 |

Two further degenerate inputs need no guard cycle, because the contract layer already
refuses them before `resolve` is reached and cycle 13 pins that refusal path: front-matter
that is not valid YAML, and front-matter declaring no `cycles`. A plan with **no**
front-matter at all parses to `status: "undeclared"` with `cycles: []`, which resolves to
empty `paths` and `unresolved` lists — the honest answer to "which files does this plan's
contract name", and `ok: true` per decision 10.

## Sweeps

This plan performs no migration or sweep: nothing is renamed, no call sites move, and no
exception type, signature, return shape or status code changes. `Adapter.scan_target_paths`
is purely additive, with a base-class default, so no existing adapter or caller needs
updating.

Consequently no existing test asserts a form this plan breaks, and every cycle's
`modifies_tests` is empty. Verified — the whole suite is green today and no declared
production file is touched by a behaviour-changing edit:

    $ uv run pytest -q
    517 passed in 29.45s

## Docs (ancillary — post-terminal, see Done-criteria)

`README.md` and `docs/PRD.md` are declared in `ancillary_files` so a mid-run edit cannot
raise `undeclared_file_touched`, but the intended shape is documentation committed after
the run is terminal, matching how `tasks/issue-71-target-lint.md` handled the same need:

- `README.md` — add a row to the **Commands** table:
  `` | `tdd plan paths <path> [--json]` | resolve a plan's test ids to repository file paths; read-only | ``
- `docs/PRD.md` §8.2 — add a `tdd plan paths <path>` row to the command table, stating that
  it reads the **working-tree** plan, needs no run or prior registration, writes nothing to
  the ledger, exits 0 with an `unresolved` list, and refuses only a malformed contract or an
  unknown project.
- `docs/PRD.md` §7 — add **R7.14** after R7.11, stating that a plan's declared test ids are
  resolvable to repository paths by `tdd plan paths` using the same qualification rules the
  engine applies, and that ids whose adapter grammar carries no path are reported as
  unresolved rather than omitted.
- `docs/PRD.md` §10 — add **R10.9** (the next free number; R10.8 is `normalise_id`),
  documenting `Adapter.scan_target_paths() -> dict[str, str]` as the source-scan hook:
  native id → project-root-relative path, base default `{}`, implemented by `gradle` and
  `xctest` whose ids name a class rather than a file, and never invoking the runner.

`docs/harness-integration.md` needs no change: this command adds no verb and does not enter
the drive loop.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout main && git pull                        # branch off main, never off another feature branch
    git checkout -b issue-119-plan-paths                 # first, before anything else
    uv venv ~/.cache/tdd-referee                         # the frozen referee — see below
    uv pip install --python ~/.cache/tdd-referee /Volumes/SSD/repos/tdd-cli
    ~/.cache/tdd-referee/bin/tdd doctor                  # must report healthy: true
    ~/.cache/tdd-referee/bin/tdd run start --plan tasks/issue-119-plan-paths.md

**The referee is a frozen snapshot — build it first, before `doctor`.** `tdd.toml`'s header
states the rule: the controller being edited mid-cycle cannot also be the controller
enforcing the cycle. This plan edits `src/tddcli/cli.py` and `src/tddcli/adapters/base.py`,
which the `tdd` on PATH (the venv's **editable** install of this tree) would pick up live.

The usual answer — the last release — does not work here, verified at plan time:

    $ uvx --from tdd-cli==0.10.1 tdd doctor
    "ledger … has schema version 10, but this tdd-cli understands up to 8"

The ledger has already been migrated past the released tool by earlier runs, so 0.10.1
(both the `~/.local/bin/tdd` install and the `uvx` form) refuses every command. Until a
release ships that understands schema 10, the referee is a **non-editable snapshot of this branch's
HEAD**, which is frozen at the moment you build it and therefore does not move as you edit:

    uv venv ~/.cache/tdd-referee
    uv pip install --python ~/.cache/tdd-referee /Volumes/SSD/repos/tdd-cli
    ~/.cache/tdd-referee/bin/tdd --version      # tdd-cli 0.10.1 — verified healthy at plan time

Build it **after** `git checkout -b`, so the snapshot carries this plan's commit and nothing
else, and use `~/.cache/tdd-referee/bin/tdd` for every `tdd` command below. Do **not**
rebuild it mid-run, and do **not** fall back to the `tdd` on PATH: an editable referee
executing cycle 13's half-written `cmd_plan_paths` is exactly the failure the rule exists to
prevent. If the snapshot itself cannot run, that is `tdd blocker --kind tooling`, not a
reason to switch binaries.

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

`main` must be the base — never another feature branch, whose unmerged commits would be
dragged into this PR. If `git log --oneline main..HEAD` shows anything other than this
plan's commit before you start, you are on the wrong base — stop and ask.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `~/.cache/tdd-referee/bin/tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `~/.cache/tdd-referee/bin/tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The expected
  baseline summary line is `tddcli: 0` — the suite is green on `main` at **517 passed**. A different
  number means the branch moved; stop and raise a blocker rather than absorbing it.
- Verb map for this plan: `run_sensitivity_check` → `~/.cache/tdd-referee/bin/tdd sensitivity begin|check|end`;
  `resolve_blocker` → `~/.cache/tdd-referee/bin/tdd blocker --kind --detail` (kinds: `plan_defect`, `tooling`,
  `regression`, `pre_existing_failure`); `confirm_cycle_applicable` on a cycle the code has
  outgrown → `~/.cache/tdd-referee/bin/tdd cycle skip --reason`. This plan declares **no `annotation_keys`**, so
  `annotate_cycle` will not fire; if it does, something is wrong — do not invent a key.

**Minimal GREEN, per cycle.** Ten of these fifteen cycles touch `src/tddcli/plan_paths.py`.
Write each cycle's test only when its verb says to, and add exactly the increment below —
**and nothing earlier**:

- cycle 1 — the subparser, `resolve`'s walk over `cycle.tests`, `Engine._qualify`, the
  root join, and the `{plan, paths, unresolved}` shape.
- cycle 2 — walking `modifies_tests` as a second labelled field. **Nothing else.**
- cycle 4 — `os.path.normpath` around the join. **Nothing else.**
- cycle 5 — the unresolved row for a `None` `target_path`. **Nothing else.**
- cycle 9 — the base-class hook and gradle's override. Not xctest's.
- cycle 10 — xctest's override. Nothing in `plan_paths.py`.
- cycle 11 — the scan fallback for the *found* case, memoised per project. Not the
  not-found or ambiguous cases.
- cycle 12 — the zero-match and many-match branches. **Nothing else.**
- cycle 13 — the two refusals in `cmd_plan_paths`. Nothing in `resolve`.
- cycle 14 — `render` and the `args.json` branch, with `silent=True` on the bare path.

Cycles 3, 6, 7, 8 and 15 are **pin cycles**: their tests must pass the moment they are
written. Do not add production code for them. A pin that fails on arrival means an earlier
cycle's GREEN is wrong — read that cycle's note above, fix the earlier code, and never
weaken the pin.

## Done-criteria

**Before finishing:** run `~/.cache/tdd-referee/bin/tdd log render --out tasks/friction-logs/issue-119-plan-paths-friction.md` and `~/.cache/tdd-referee/bin/tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then the documentation, committed as ordinary commits after the run is terminal, exactly as
the **Docs** section above specifies:

    git add README.md docs/PRD.md && git commit -m "docs: tdd plan paths in the README and PRD"

Both are deliverables, not hopes. Before raising the PR, confirm each of these is non-empty,
or say in the PR body which one was dropped and why:

    git diff --stat origin/main -- README.md
    git diff --stat origin/main -- docs/PRD.md

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-119-plan-paths-friction.md
    git commit -m "docs: friction log for issue-119-plan-paths"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

This PR changes nothing a user sees in a GUI — `tdd plan paths` is a terminal command — so
the repository's demo-video requirement is satisfied by pasting the bare and `--json`
output of `tdd plan paths tasks/issue-119-plan-paths.md` into the PR body.
