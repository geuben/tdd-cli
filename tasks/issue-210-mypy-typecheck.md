---
closes: 210
cycles:
  # -- Phase 1: the tool is installed and configured, nothing enforces it yet ---------------
  - n: 1
    project: tddcli
    refactor_cycle: true
    title: "mypy is a dev dependency, configured to check src and tests"
    files: ["pyproject.toml", "uv.lock", ".gitignore"]
    commit_refactor: "build: add mypy and its configuration as dev tooling"
  # -- Phase 2: the one error that is a behaviour defect -----------------------------------
  - n: 2
    project: tddcli
    title: "a late baseline probe records its collection's failed files as a map"
    test: "tests/test_late_baseline.py::test_a_late_probe_records_its_failed_files_as_an_empty_map"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: a late probe records its failed files as an empty map"
    commit_green: "fix: a late baseline probe records failed_files as a map, not a list"
    commit_refactor: "refactor: tidy the late-probe collection row"
  # -- Phase 3: the remaining errors, behaviour preserved ----------------------------------
  - n: 3
    project: tddcli
    refactor_cycle: true
    title: "the ledger, the ledger service and leases type-check"
    files: ["src/tddcli/ledger.py", "src/tddcli/service.py", "src/tddcli/leases.py"]
    commit_refactor: "refactor: make the ledger, its service and leases type-check"
  - n: 4
    project: tddcli
    refactor_cycle: true
    title: "the engine, advance and render type-check"
    files: ["src/tddcli/machine.py", "src/tddcli/advance.py", "src/tddcli/render.py"]
    commit_refactor: "refactor: make the engine, advance and render type-check"
  - n: 5
    project: tddcli
    refactor_cycle: true
    title: "the CLI, the adapters and the tests type-check"
    files:
      - "src/tddcli/cli.py"
      - "src/tddcli/adapters/base.py"
      - "src/tddcli/adapters/xctest_adapter.py"
      - "tests/test_unblocks_count.py"
      - "tests/test_split_identity.py"
      - "tests/test_ledger_service.py"
      - "tests/test_init_skill.py"
    commit_refactor: "refactor: make the CLI, the adapters and the tests type-check"
  # -- Phase 4: enforce it -----------------------------------------------------------------
  - n: 6
    project: tddcli
    refactor_cycle: true
    title: "mypy is the close sweep's typecheck gate and a CI step"
    files: ["tdd.toml", ".github/workflows/ci.yml", "CONTRIBUTING.md", "CHANGELOG.md"]
    commit_refactor: "build: type-check with mypy in the close sweep and in CI"
---

# Issue 210: type-check the source and tests with mypy

## Context

[Issue #210](https://github.com/geuben/tdd-cli/issues/210) says "add mypy typechecking". Its one
comment, from the automated classifier, names what a plan must settle: the configuration, its
strictness, fixing the errors that exist today, and wiring it into CI.

The repo has no type checker today. `pyproject.toml`'s dev group is pytest, pytest-json-report,
pytest-xdist, ruff and zizmor. `tdd.toml` declares a `lint` gate (`uv run ruff check`) and no
`typecheck` gate. CI's `lint` job runs `ruff check` and `ruff format --check` over `src tests`.
The code is already mostly annotated, because the repo's own docs show mypy as the example
`typecheck` gate (README's `tdd.toml` example, `docs/PRD.md` §7.1).

Measured at `origin/main` 660bf35 with mypy 2.4.1 and `types-PyYAML`, in mypy's default mode with
`--python-version 3.11`, over `src tests`: **53 errors in 13 files** (`src` alone: 49 in 9). Without
`types-PyYAML` there are 3 more (`import-untyped` on `yaml` in `contract.py`, `harness.py` and
`tests/test_init_skill.py`). `--strict` reports 324, nearly all `no-untyped-def`. A cold run takes
about 1 s and a warm one 0.2 s. mypy writes `.mypy_cache/` with its own `.gitignore` (`*`), so
the cache never dirties the tree hash.

Of the 53 errors, one is a behaviour defect and the rest are annotation or narrowing gaps (each
was read, see "Cycles"). The defect: `Engine.sweep`'s late baseline probe writes the
`collection_snapshot` row with `failed_files` `[]`. The column is a JSON map of path to error (its
comment in `ledger.SCHEMA`), `Ledger.record_collection` takes `failed_files: dict`, and the only
other writer (`cmd_run_start`) passes the adapter's `Collection.failed_files` dict. A late-probed
project's row is the only one holding a list.

## Design decisions (locked)

1. **Default mode, with no extra strictness flags.** Decided by *evidence*. The issue asks for
   mypy and nothing more. The repo's own example gate is a bare `mypy .` (README, `docs/PRD.md`
   §7.1). Adding `--strict` (324 errors, almost all missing annotations on CLI handlers and test
   functions) would be the "no future-proofing" extra that `/plan-issue` rule 4 forbids.
   Tightening it later is additive: a reviewer who wants `check_untyped_defs` or `strict` can ask
   for it on its own issue. Default mode prints `annotation-unchecked` *notes* for bodies of
   untyped functions. Notes do not change the exit status. Leave them; do not silence them.
2. **mypy checks `src` and `tests`, not `examples/`.** Decided by *convention*. Ruff checks
   exactly `src tests` in CI and CONTRIBUTING, and `[tool.ruff] src = ["src", "tests"]`.
3. **Configuration lives in `pyproject.toml` as `[tool.mypy]`, beside `[tool.ruff]`:**

   ```toml
   [tool.mypy]
   python_version = "3.11"
   files = ["src", "tests"]
   ```

   Nothing else. `python_version` comes from `requires-python = ">=3.11"` (*evidence*), so a CI
   job on a newer interpreter still checks against the oldest supported one. `files` makes a
   bare `uv run mypy` check the right paths, so CI, `tdd.toml` and CONTRIBUTING all run the same
   command (*convention*: one spelling per tool, as with ruff).
4. **mypy and `types-PyYAML` join `[dependency-groups] dev` with lower bounds,
   `"mypy>=2.4"` and `"types-PyYAML>=6.0"`, and `uv.lock` is regenerated with `uv lock`.**
   Decided by *convention* (ruff and zizmor are dev-group lower bounds; the lock pins). The stubs
   are needed (*evidence*: without them `import yaml` fails in two `src` modules).
5. **`.mypy_cache/` is added to `.gitignore`, beside `.ruff_cache/` and `.pytest_cache/`.**
   *Convention*: those tools also write a self-ignoring cache, and the repo lists them anyway.
6. **The late probe's row gets `{}`, through a standard RED/GREEN cycle (cycle 2).** Decided by
   *evidence* (Context). A refactor cycle cannot carry it, because it changes what the ledger
   stores. Nothing reads `collection_snapshot.failed_files` today (`Ledger.collection` reads only
   `tests`), so no other test or reader changes. The late probe's `tests` stays `[]`. That is
   existing behaviour (`Engine.rerun_untouched` reads it through `Ledger.collection`), and it is
   not a type error.
7. **Fix rules for every other error. They bind cycles 3–5:**
   - Fix the annotation, not the logic. Widen or add an annotation to the type the code already
     handles (`dict[str, object]` / `dict[str, Any]` for a heterogeneous result dict,
     `str | None` for a value that can be missing, `tuple[str, ...]` for a tuple that changes
     length). Rename a variable that is reused for a value of another type.
   - Narrow with `assert x is not None` only where `None` cannot occur on that path. That is
     also where today's code would already raise on `None` (indexing a `Row | None`, calling a
     method on `Ledger | None`). Narrow an adapter with `assert isinstance(adapter, PytestAdapter)`
     where the code has just checked `project.adapter == "pytest"`.
   - Use `# type: ignore[<code>]` only where mypy's model is wrong, and always with the error
     code. The repo's two existing ignores (`actor.py`'s `_env` and `service.py`'s
     `_Handler.handle`) are the precedent. Never use a bare `# type: ignore`, and never use
     `cast` to hide a `None` that is reachable.
   - A missing method that every concrete subclass already defines (`Adapter._test_files`) is
     declared on the base with the subclasses' signature and a `raise NotImplementedError` body.
   - **If an error cannot be fixed without changing behaviour, it is not a refactor.** Stop with
     `tdd blocker --kind plan_defect`, and do not commit a semantic change under a refactor
     phase.
   *Convention*: refactor cycles preserve behaviour, and the existing suite (852 tests) guards it.
8. **Enforcement copies ruff's two places, with no pytest test that runs mypy.**
   `tdd.toml` gains `typecheck = ["uv run mypy"]` beside `lint`, and CI's `lint` job gains a
   step after "Ruff format":

   ```yaml
         - name: Mypy
           run: uv run mypy
   ```

   *Convention*: ruff runs as `tdd.toml`'s `lint` gate and as a CI `lint`-job step, and no test
   runs ruff. The step runs once, on ubuntu, like ruff. `python_version` (decision 3) fixes the
   semantics whatever interpreter the job resolves. `uv run zizmor --offline .` reports no
   findings with this step added (probed).
9. **The gate is wired last (cycle 6), after every error is fixed.** Decided by *evidence*. The
   referee loads `tdd.toml` on every command, so a `typecheck` gate added earlier fails every
   close sweep until the last fix lands. Editing `tdd.toml` mid-run records one
   `config_changed` integrity event (`advance._check_config_drift`, deduplicated per hash). It
   is expected here and is not a defect. Wiring it last also means cycle 6's own close sweep
   runs `uv run mypy` through the referee, which proves the whole tree is clean.
10. **Docs:** CONTRIBUTING's ground rules gain "Type-check with `uv run mypy`." after the ruff
    line, and its "CI must pass" list names the type check. `CHANGELOG.md` gets two lines under
    `## [Unreleased]`: one under `### Changed`, that the source and tests are type-checked with
    mypy in CI and in the repo's own close sweep (#210), and one under `### Fixed`, for
    decision 6. *Convention*: a CI change got a line before ("CI now tests on Python 3.11 and
    3.14 only (#87)"), and `RELEASING.md` says the changelog is hand-edited under Unreleased.
    README and `docs/PRD.md` do not change, because nothing a user of `tdd` sees changes.
11. **The implementation PR edits `.github/workflows/ci.yml`, so #210 must carry the `ci`
    label before the run pushes.** Decided by *evidence*. `.dispatch.toml` has no `[ci]` table,
    so the label is `ci`, and GitHub rejects a push that changes a workflow without it.

## Deliberate scope cuts (do not build)

None. Stricter modes and `examples/` are not cuts: the issue does not ask for them
(decisions 1 and 2).

## Fake and real divergence

None. No test double is introduced. Cycle 2 runs the real CLI in-process against the
`repo_schema_other` fixture, and reads the real ledger.

## Cycles

### Cycle 1 (refactor): mypy is a dev dependency, configured to check src and tests

Behaviour is unchanged, and the existing suite guards it.

- `pyproject.toml`: add `"mypy>=2.4"` and `"types-PyYAML>=6.0"` to `[dependency-groups] dev`.
  Add the `[tool.mypy]` table of decision 3 after `[tool.ruff.lint]`.
- `uv.lock`: regenerate with `uv lock`. Do not hand-edit it.
- `.gitignore`: add `.mypy_cache/` after `.ruff_cache/`.
- Before `tdd advance`, run `uv run mypy` and record its summary line. Expect
  `Found 53 errors in 13 files (checked 117 source files)` at this plan's base. If the count
  differs, code landed after planning. Re-derive the list (see "The error sweep") and report the
  delta in the cycle's `friction_note`. Do not fix anything in this cycle.
- Do **not** touch `tdd.toml` here (decision 9).

### Cycle 2: a late baseline probe records its collection's failed files as a map

- **Test:** `tests/test_late_baseline.py::test_a_late_probe_records_its_failed_files_as_an_empty_map(repo_schema_other)`,
  at file scope like the file's other tests, after
  `test_close_sweep_late_probes_an_unbaselined_project_at_the_start_sha`. The file already
  imports `json`, `Ledger`, `gitutil`, `run_cli` and the helpers `_drive_to_close` and
  `_pull_svc_into_the_sweep`. Body:
  1. `_drive_to_close(repo)`.
  2. Read the run id: `Ledger(gitutil.repo_identity(repo)).one("SELECT id FROM run WHERE
     worktree_path = ? ORDER BY id DESC LIMIT 1", (str(repo),))["id"]`.
  3. `_pull_svc_into_the_sweep(repo)`, then `run_cli(repo, "advance")`. The close sweep reaches
     `svc`, which has no baseline, so `Engine.sweep` late-probes it.
  4. Read `SELECT failed_files FROM collection_snapshot WHERE run_id = ? AND project = 'svc'`.
  5. Single assertion: `(json.loads(row["failed_files"]) if row else None) == {}`.
- **Target:** `src/tddcli/machine.py::Engine.sweep`, in the late-probe branch
  (`if name not in baselines:` → `if probe.observed:`). Its `self.ledger.record_collection(...)`
  call passes `{}` as `failed_files` instead of `[]`.
- **EXPECTED FAILURE:** `assert [] == {}` (probed at `origin/main` in a fresh worktree: the
  advance replies `complete`, and the run's `collection_snapshot` rows are `backend` with
  `failed_files` `'{}'` and `svc` with `failed_files` `'[]'`).
- No stub: the test imports nothing new. No existing test reads the column (`grep -rn
  failed_files tests/` hits only `Collection.failed_files` on adapter results), so
  `modifies_tests` is empty.
- After GREEN, `uv run mypy` no longer reports `machine.py`'s `record_collection` `arg-type`
  error. The count drops by one.

### The error sweep (cycles 3–5)

**Discovery command**, run at the start of each of cycles 3–5:

    uv run mypy | grep ': error:'

Each error belongs to the cycle whose `files` holds its file. The cycle is done when the
command reports no error in any of its files. Errors in later cycles' files stay for those
cycles. An error in a file that **no** cycle declares (code merged after planning) belongs to
cycle 5. Fix it there, and name the file and the error in that cycle's `friction_note`. Its
commit records an `undeclared_file_touched` event, which is expected.

The list below is the discovery output at `origin/main` 660bf35, by file and enclosing function,
after cycle 2. If the run finds more or fewer, report the delta in the cycle's `friction_note`.

### Cycle 3 (refactor): the ledger, the ledger service and leases type-check

Behaviour is unchanged, and the existing suite guards it. Fix rules: decision 7. 22 errors:

- `src/tddcli/ledger.py` (5):
  - `Ledger.insert`: `return-value`, because `lastrowid` is `int | None`. Narrow it: after an
    `INSERT`, `lastrowid` is set.
  - `Ledger.max_suite_duration_ms`: `assignment` to `extra`, which is inferred as `tuple[()]`.
    Annotate it `tuple[str, ...]`.
  - `Ledger.abandon_run` (×2): `index` on `run = self.run(run_id)`. Narrow it; the run exists.
  - `open_readonly`: `assignment` of `None` to `reader.repo_path`. Annotate `Ledger.repo_path`
    as `Path | None` in `Ledger.__init__`, and fix whatever that widening newly reports.
- `src/tddcli/service.py` (15):
  - `_Session.answer` (×5): `method` and `repo` are `Any | None`, and `self.source` is
    `str | None` (passed to `report`, `admin`, `executors.get`, `Path` and `ledger_mod.slug`).
    Widen `Service.report` and `Service.admin`'s `method` parameter to `str | None`. Both
    already refuse or fall through on a name they do not know, so `None` takes that path
    today. Widen `Service.executors` to `dict[str | None, str | None]`, because `answer`'s
    `ping` branch already calls `.get(self.source)` with `source` `None`. Narrow `repo` with
    `assert isinstance(repo, str)` after `_well_formed_repo(repo)` has accepted it.
  - `_Session._foreign`, `_closed`, `_cycle_source`, `_invocation_source`, `_contract_source`
    (×9): `union-attr` on `self.ledger`. These run only after `answer` has returned early when
    `self.ledger is None`. Narrow there.
  - `_Session._stamp_executor` (×1): `executors.get(self.source)`. This is covered by the key
    type widened above.
  - `_Listener.__init__` (×1): `shutil.chown(path, group=group)` with `group: str | None`.
    `load_config` refuses `bind_socket` without `bind_group`, so `group` is set when
    `bind_only` is. Narrow it.
- `src/tddcli/leases.py` (2): `snapshot` and `worker_lease` pass `guest.ledger_socket`
  (`Path | None`) on. `_guest()` returns a config only when `ledger_socket` is set, so narrow
  with `assert guest.ledger_socket is not None` at each call. `_guest`'s return type stays
  `RunnerConfig | None`.

### Cycle 4 (refactor): the engine, advance and render type-check

Behaviour is unchanged, and the existing suite guards it. Fix rules: decision 7. 16 errors:

- `src/tddcli/machine.py` (4): `Engine.__init__` (×3) and `Engine.run_state` (×1) index
  `ledger.contract(...)`, which is `Row | None`. A run's contract always exists (it is a foreign
  key). Narrow in `__init__` once, and annotate `self.contract_row: sqlite3.Row`. Leave
  `Ledger.contract`'s `Optional` return alone, because `service._Session._contract_source`
  relies on it returning `None`.
- `src/tddcli/advance.py` (3):
  - `_handle_test_phase`: `classification.implementation` on `object`. Annotate
    `_stage_and_commit`'s third return element as `staging.Classification`.
  - `_handle_refactor` (×2): index `engine.contract_row`. This is covered by machine's
    annotation above.
- `src/tddcli/render.py` (10):
  - `friction_log` (×4) and `progress` (×2): index `ledger.contract(...)`. Narrow.
  - `metrics`: `by_project = defaultdict(int)` (`var-annotated`), so annotate it
    `defaultdict[str, int]`. `out` is inferred too narrowly, which gives `attr-defined` on
    `out["runs"].append` and `index` on `out["runs"][-1]["abandoned"]`. Annotate `out` as
    `dict[str, Any]`. Narrow the inline `ledger.contract(...)["declared_cycles"]`.

### Cycle 5 (refactor): the CLI, the adapters and the tests type-check

Behaviour is unchanged, and the existing suite guards it. Fix rules: decision 7. 14 errors:

- `src/tddcli/cli.py` (7):
  - `cmd_doctor`: `plugin_probe_cmd` on `Adapter`. Bind `adapters.build(project, worktree)`
    to a name and `assert isinstance(it, PytestAdapter)` under the existing
    `project.adapter == "pytest"` check.
  - `cmd_run_start` (×2): `unreachable` is inferred `list[dict[str, object]]`, so its
    `", ".join(u["project"] ...)` is `misc`. Annotate it `list[dict[str, Any]]`. The
    `implausible` loop reassigns `project` to `probe_projects.get(name)` (`Project | None`)
    after an earlier `project: Project`. Rename the loop's variable.
  - `cmd_resume` (×2): `result = {"resumed": True}` is inferred `dict[str, bool]`. Annotate it
    `dict[str, object]`.
  - `build_parser` (×2): `inv = inv.add_subparsers(...)` rebinds a parser to a subparsers
    action. Chain it as the other verb groups in `build_parser` do (`plan`, `run_p`, `cyc`,
    `log`): `inv = sub.add_parser("invocation", help=...).add_subparsers(dest=..., required=True)`,
    with the same help text and dest.
- `src/tddcli/adapters/base.py` (1): `Adapter.collect` calls `self._test_files()`, which every
  subclass defines (exec, cargo, pytest, gradle, vitest, xctest) and the base does not. Declare
  `def _test_files(self) -> list[Path]: raise NotImplementedError` on `Adapter`.
- `src/tddcli/adapters/xctest_adapter.py` (1): `_failure_for`'s `captured` (`var-annotated`).
  Annotate it `list[str]`.
- Tests (4). These are helpers and module constants, not test bodies or assertions, so no test
  id goes in `modifies_tests`:
  - `tests/test_unblocks_count.py::fixture_ledger` returns `ledger.one(...)` as `sqlite3.Row`.
    Narrow it.
  - `tests/test_split_identity.py::_recorded` indexes `ledger.one(...)`. Narrow it.
  - `tests/test_ledger_service.py::host_run` calls `.run` on `open_readonly(...)`
    (`Ledger | None`). Narrow it.
  - `tests/test_init_skill.py`: the `@pytest.mark.parametrize` list of
    `test_wired_means_every_stanza_command_is_present` unpacks
    `*EXPECTED_SETTINGS["hooks"]["Stop"]` (`misc`). Annotate the module constant
    `EXPECTED_SETTINGS: dict[str, Any]`.
- Before `tdd advance`, `uv run mypy` must print `Success: no issues found in 117 source files`
  (or the current file count). This is the last fix cycle.

### Cycle 6 (refactor): mypy is the close sweep's typecheck gate and a CI step

Behaviour of `tdd` is unchanged. This cycle adds enforcement and docs only.

- `tdd.toml`: add `typecheck  = ["uv run mypy"]` under `lint` in `[project.tddcli]`, aligned
  like its siblings.
- `.github/workflows/ci.yml`: in the `lint` job, after the "Ruff format" step, add the "Mypy"
  step of decision 8. Then run `uv run zizmor --offline .`, which must report no findings
  (CONTRIBUTING requires it for any `.github/` change).
- `CONTRIBUTING.md`: in "Ground rules", after "Lint with `uv run ruff check src tests`.", add
  "Type-check with `uv run mypy` (it reads its paths and settings from `pyproject.toml`)." In
  "Pull requests", the CI list becomes "(tests on Python 3.11–3.14, lint, type check, workflow
  audit, build + wheel smoke test)".
- `CHANGELOG.md`, under `## [Unreleased]`:
  - `### Changed`: "The source and tests are type-checked with mypy (default mode, Python 3.11
    semantics), in CI and as this repo's own `typecheck` gate (#210)."
  - `### Fixed`: "A late baseline probe records its collection's `failed_files` as an empty map,
    like every other `collection_snapshot` row, instead of an empty list (#210)."
- The close sweep of this cycle runs the new `typecheck` gate through the referee. A failing gate
  means an error cycles 3–5 left behind: fix it here under decision 7. If it cannot be fixed
  without a behaviour change, raise `plan_defect`.
- Expect exactly one `config_changed` integrity event, on the first `tdd advance` after the
  `tdd.toml` edit (decision 9).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-210-mypy-typecheck    # first, before anything else
    tdd doctor                                  # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-210-mypy-typecheck.md   # captures baselines, opens cycle 1

`tdd doctor` checks every project; `tdd run start` probes only the ones the plan declares and
those downstream of them through an `[artifact]`. A failing check on a project outside that set
does not stop the run: note it and go on. Any other failing check stops it.

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

**Referee.** Use the released `tdd` on `PATH`, never `uv run tdd` from this tree (the note at
the top of `tdd.toml`). This plan changes no ledger table, so `SCHEMA_VERSION` does not move
and no frozen referee is needed.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is
  green at the plan's base (verified in a fresh worktree of `origin/main` 660bf35:
  `852 passed`). Expect `baselines: {tddcli: 0}` and no standing failures.
- Verbs this plan will hit:
  - `refactor_or_advance`: cycles 1 and 3–6 open in `AWAITING_REFACTOR`. Make the cycle's
    edits, check them with `uv run mypy` as the cycle says, then `tdd advance`.
  - `write_test`, `write_implementation`: cycle 2.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`, only if cycle 2's test passes
    on arrival (it should not: `assert [] == {}`).
  - `create_stub`: no cycle declares a stub (cycle 2 imports only existing symbols), so any
    request means an undeclared import.
  - `fix_regression`: in cycle 6, a failing `typecheck` gate is an error cycles 3–5 missed. Fix
    it under decision 7.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|environment> --detail '...'`.
    `plan_defect` when an error cannot be fixed without a behaviour change (decision 7).
    `environment` when `uv lock` / `uv run` cannot reach the package index.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.
  - This plan declares no annotation keys, so `annotate_cycle` asks only for the reserved
    `friction_note` / `plan_defect` if at all. Put the per-cycle mypy deltas in `friction_note`.
- Integrity events this plan expects: one `config_changed` in cycle 6 (decision 9). An
  `undeclared_file_touched` is expected only for a file the error sweep found that no cycle
  declares. Anything else is a real finding: report it.
- Refactor cycles never change behaviour. If a fix turns out to need one, raise `plan_defect`.
  Never commit a semantic change under a refactor phase.

**Minimal GREEN, per cycle: add this and nothing earlier.**

- cycle 1 adds the dependencies, the `[tool.mypy]` table and the `.gitignore` line. It fixes no
  error and does not touch `tdd.toml`.
- cycle 2 changes the late probe's `record_collection` argument from `[]` to `{}`, and nothing
  else in `machine.py`. `Engine.__init__`'s errors wait for cycle 4.
- cycles 3, 4 and 5 fix exactly the errors in their own `files`.
- cycle 6 adds the gate, the CI step and the docs, and no code.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-210-mypy-typecheck-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-210-mypy-typecheck-friction.md
    git commit -m "docs: friction log for issue-210-mypy-typecheck"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #210`.

Before raising the PR, these must hold:

- `uv run mypy` prints `Success: no issues found` and exits 0.
- `uv run ruff check src tests` and `uv run ruff format --check src tests` are clean.
- `uv run zizmor --offline .` reports no findings.

The PR changes `.github/workflows/ci.yml`. GitHub refuses the push unless #210 carries the `ci`
label (decision 11). If it does not, push everything except that file's change, and put the
change in the PR body as a patch with a note that a person must apply it.

Docs and config are deliverables, not hopes. Cycles 1 and 6 own them:

- `git diff --stat origin/main -- pyproject.toml uv.lock .gitignore` must be non-empty for each
  path, or the PR body says why.
- `git diff --stat origin/main -- tdd.toml` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- .github/workflows/ci.yml` must be non-empty, or the PR body
  carries it as a patch (above).
- `git diff --stat origin/main -- CONTRIBUTING.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.

Nothing a user of `tdd` sees changes, so no demo recording is required.
