---
closes: 168
cycles:
  - n: 1
    project: tddcli
    pin_cycle: true
    title: "an empty successful batch leaves its files to the per-file loop"
    test: "tests/test_batch_collection.py::test_an_empty_successful_batch_leaves_its_files_to_the_loop"
    files: ["src/tddcli/adapters/base.py"]
    commit_red: "test: pin the per-file loop after an empty batch"
    commit_refactor: "refactor: tidy empty-batch handling"
  - n: 2
    project: tddcli
    pin_cycle: true
    title: "a failed override batch still attributes its own files"
    test: "tests/test_batch_collection.py::test_a_failed_override_batch_still_attributes_its_own_files"
    files: ["src/tddcli/adapters/base.py"]
    commit_red: "test: pin per-file attribution for a failed override batch"
    commit_refactor: "refactor: tidy override attribution"
  - n: 3
    project: tddcli
    pin_cycle: true
    title: "an adapter whose collect invocations name no suite keeps the per-file loop"
    test: "tests/test_batch_collection.py::test_an_adapter_whose_invocations_name_no_suite_keeps_the_loop"
    files: ["src/tddcli/adapters/base.py"]
    commit_red: "test: pin the loop for adapters that name no suite"
    commit_refactor: "refactor: tidy invocation unpacking"
  - n: 4
    project: tddcli
    title: "a file a successful pytest batch did not list costs no runner start"
    test: "tests/test_batch_collection.py::test_a_file_a_successful_batch_did_not_list_costs_no_runner_start"
    files: ["src/tddcli/adapters/base.py", "src/tddcli/adapters/pytest_adapter.py"]
    modifies_tests:
      - "tests/test_batch_collection.py::test_a_file_the_batch_never_reported_is_collected_individually"
      - "tests/test_suite_overrides.py::test_pytest_collection_routes_override_files_to_the_override_command"
    commit_red: "test: a successful batch settles the files it did not list"
    commit_green: "perf: a successful pytest batch is authoritative for its suite's files"
    commit_refactor: "refactor: tidy authoritative batch collection"
  - n: 5
    project: tddcli
    title: "a file a successful vitest listing did not name costs no runner start"
    test: "tests/test_batch_collection.py::test_vitest_a_file_the_listing_did_not_name_costs_no_runner_start"
    files: ["src/tddcli/adapters/vitest_adapter.py"]
    commit_red: "test: a successful vitest listing settles the files it did not name"
    commit_green: "perf: vitest collect invocations name their suite"
    commit_refactor: "refactor: tidy vitest collect invocations"
  - n: 6
    project: tddcli
    title: "a test file a successful cargo listing did not list costs no runner start"
    test: "tests/test_cargo_adapter.py::test_a_test_file_the_listing_did_not_list_costs_no_runner_start"
    files: ["src/tddcli/adapters/cargo_adapter.py"]
    commit_red: "test: a successful cargo listing settles the files it did not list"
    commit_green: "perf: cargo collect invocations name their suite"
    commit_refactor: "refactor: tidy cargo collect invocations"
  - n: 7
    project: tddcli
    title: "baseline_captured reports how many files fell to the per-file loop"
    test: "tests/test_timing_visibility.py::test_baseline_reports_how_many_files_fell_to_the_per_file_loop"
    files: ["src/tddcli/adapters/base.py", "src/tddcli/cli.py"]
    commit_red: "test: baseline_captured counts per-file collects"
    commit_green: "feat: baseline_captured reports per_file_collects"
    commit_refactor: "refactor: tidy the per-file count"
  - n: 8
    project: tddcli
    title: "parallel baseline probes report the per-file count too"
    test: "tests/test_timing_visibility.py::test_parallel_baselines_report_how_many_files_fell_to_the_loop"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: parallel baseline_captured counts per-file collects"
    commit_green: "feat: parallel baseline_captured reports per_file_collects"
    commit_refactor: "refactor: share the baseline_captured payload"
  - n: 9
    project: tddcli
    refactor_cycle: true
    title: "document the authoritative batch rule"
    files: ["docs/PRD.md", "CHANGELOG.md"]
    commit_refactor: "docs: a successful batch is authoritative for its suite (R10.3)"
---

# Issue 168: a successful batch listing is authoritative for its suite's files

## Context

[#168](https://github.com/geuben/tdd-cli/issues/168): since #27, `collect()`
(`adapters/base.py`, `Adapter.collect`) runs one whole-suite listing per declared suite. It then
runs the per-file loop for **every** `test_paths` file the listing did not report, even when the
listing succeeded. Each loop iteration starts the test runner.

Two ordinary setups produce many such files:

- projects sharing a root, whose `test_paths` must be the union of every project's test files;
- support files (fixtures, helpers, setup files) inside `test_paths`.

On geuben/energy-stats (vitest 4, four projects on `.`), `core` paid 180 runner starts and 135 s
per `collect()`. All 180 returned zero tests and were recorded in `failed_files` as
`no tests parsed from …`.

The issue asks for two things:

1. Treat a successful batch as authoritative for the files it did not mention, while keeping the
   per-file loop for files whose batch failed. That keeps R10.3's guarantee.
2. At minimum, report a per-file fallback count in the `baseline_captured` heartbeat next to
   `collect_s`.

This plan builds both.

## Design decisions (locked)

1. **A successful batch is authoritative for its suite's files** (user, Phase C). This
   deliberately reverses
   `tests/test_batch_collection.py::test_a_file_the_batch_never_reported_is_collected_individually`.
   That test's premise ("a quietly smaller baseline is worse than a slow one") rescued files the
   runner's own config excludes. The suite never runs those files either, so the rescue only
   produced targets no run could observe. Cycle 4 replaces the test with its opposite.
2. **"Successful" means the batch returned a result with at least one test** (planner, from the
   code). `_collect_batch` already returns `None` for:
   - a non-zero exit;
   - pytest's exit 5 on an empty collection;
   - a cargo `could not compile`;
   - a vitest listing that is not a JSON array.

   A result with zero tests still settles nothing, so every file of that suite falls to the loop
   as today. Cycle 1 pins this before the change.

   E-2 evidence that a successful listing does not hide a broken file: real vitest 4.1.11 exits 1
   for a syntax error and for a missing import, and exits 0 listing only the real test file when
   the tree is clean, with no entry for a helper `.ts`. pytest exits 2 on any collection error.
3. **A batch settles only files its own suite owns** (planner). The suite that owns a file is
   `self.project.override_for(rel)`: the override, or `None` for the default suite. After a
   successful batch, every file in `unaccounted` whose owner **is** that batch's owner is
   removed. Compare with `is`, since override objects come from the one config load. A failed
   override batch therefore still loops its own files even when the default batch succeeded.
   Cycle 2 pins this before the change. A vitest override without a `collect_command` has no
   batch at all, so its files still loop and record the missing command.
4. **Owners travel as an optional third element** (planner). Each built-in
   `_collect_invocations` (pytest, vitest, cargo) returns `(command, env, owner)`. `Adapter.collect`
   unpacks it as `command, env, *rest`. With no third element (a third-party plugin adapter's
   2-tuple), the owner is unknown and nothing is settled, so the plugin keeps today's loop
   (cycle 3 pins this). The other built-ins override `collect()` itself and are untouched:
   `exec_adapter.py`, `gradle_adapter.py` and `xctest_adapter.py`. Changing the 2-tuple shape
   instead would break every plugin adapter that implements the hook.
5. **The count is `Collection.per_file_collects`** (planner). It is a new
   `int = 0` field, set by `Adapter.collect` to `len(unaccounted)`, the number of files handed to
   `_collect_per_file`. Both `baseline_captured` heartbeats emit it as `per_file_collects`:
   - the serial path in `_probe_baselines`;
   - the `jobs > 1` path, whose `_worker` returns the `Collection`.

   A reused baseline emits `baseline_reused` with no collect, so it gains nothing. The cache does
   not store the count.

## Deliberate scope cuts (do not build)

- **Narrowing the loop by file-name pattern** (`*.test.ts`, `test_*.py`), the issue's second
  option. Premise: **user-deferred**. The user chose "batch is authoritative" alone over "both" in
  Phase C. Once a batch succeeds the loop no longer runs for its files, so the filter would only
  matter after a batch has already failed.
- **Gradle, xctest and exec collection.** Premise: **named non-goal**. Their `collect()` methods
  do not use the base batch-then-loop path (exec walks files with no subprocess). Gradle and
  xctest run their loop only when their enumeration fails, so they do not have the cost #168
  describes.

## Fake/real divergence

| Seam | Fake | Real | Untested path | Ruling |
|---|---|---|---|---|
| `run_command` monkeypatched in `pytest_adapter` / `vitest_adapter` | scripted exit and output | the runner | a runner exiting 0 while silently skipping a broken file | acceptable: probed on real vitest 4.1.11 and on pytest (decision 2) |
| `CargoAdapter._run_suite` patched | `LIST_OUTPUT` fixture | `cargo test -- --list` | the same | acceptable |

## Cycles

All tests live in existing files and follow the helpers already there:

- `_adapter`, `_write_tests` and the `hide_one` wrapper in `tests/test_batch_collection.py`;
- `project_with` / `OVERRIDE_BLOCK` from `tests/test_suite_overrides.py`;
- `make_adapter` / `LIST_OUTPUT` in `tests/test_cargo_adapter.py`;
- `_lines` / `_start` in `tests/test_timing_visibility.py`.

**Cycle 1 (pin): `test_an_empty_successful_batch_leaves_its_files_to_the_loop`.**
- `repo` fixture. Monkeypatch `adapters.pytest_adapter.run_command`:
  - a command ending in `--collect-only -q` (the batch) returns `(0, "", "")`;
  - everything else goes to the real `run_command`.
- Single assertion: `"backend::tests/test_smoke.py::test_smoke" in _adapter(repo).collect().tests`.
- Probed: it passes today. The commands were `pytest --collect-only -q` then
  `pytest --collect-only -q tests/test_smoke.py`, and the collection held that id.
- Cycle 4's GREEN must keep it green (decision 2).

**Cycle 2 (pin): `test_a_failed_override_batch_still_attributes_its_own_files`.**
- `project_with(tmp_path, OVERRIDE_BLOCK)`, with `backend/tests/test_a.py` and
  `backend/contract/test_api.py`.
- Fake `run_command`:
  - any command starting `pytest contract` returns `(2, "", "ERROR collecting")`;
  - every other command returns `(0, "tests/test_a.py::test_a", "")`.
- Single assertion: `set(collection.failed_files) == {"contract/test_api.py"}`.
- Probed: it passes today. Collection was `{'contract/test_api.py': 'ERROR collecting'}` after
  `pytest contract -p no:cacheprovider --collect-only -q contract/test_api.py`.
- Decision 3 keeps it green, and a "settle everything" GREEN would break it.

**Cycle 3 (pin): `test_an_adapter_whose_invocations_name_no_suite_keeps_the_loop`.**
- A local `PytestAdapter` subclass whose `_collect_invocations` returns
  `[(c, e) for c, e, *_ in super()._collect_invocations()]` (2-tuples), built on `repo` from the
  project config.
- `_write_tests(repo, 3)`, then the `hide_one` wrapper from the test being replaced, which hides
  `test_gen1.py` from the batch.
- Single assertion: exactly one command names `test_gen1.py`.
- Probed: today one rescue command is issued (`pytest --collect-only -q tests/test_gen1.py`).

**Cycle 4: `test_a_file_a_successful_batch_did_not_list_costs_no_runner_start`.**
- `_write_tests(repo, 3)` and the `hide_one` wrapper on the real pytest adapter.
- Single assertion:
  `(rescues, any("test_gen1" in t for t in collected.tests), collected.failed_files) == ([], False, {})`,
  where `rescues` is the commands naming `test_gen1.py`.
- In the same RED, **delete**
  `test_a_file_the_batch_never_reported_is_collected_individually`, since it asserts the reversed
  rule. Also update the module docstring's rule paragraph ("a file the batch does not account
  for gets exactly the old per-file treatment") to state decisions 1–3.
- In the same RED, change
  `tests/test_suite_overrides.py::test_pytest_collection_routes_override_files_to_the_override_command`
  so its fake fails the override's **batch**: return `(2, "", "")` for a command ending in
  `--collect-only -q` that contains `contract`. That keeps it exercising per-file routing through
  the override command, which is its subject. Its assertions stay as they are. The blast-radius
  simulation broke exactly these two tests (664 others passed).
- GREEN:
  - `Adapter.collect` unpacks `(command, env, *rest)`;
  - settles per decisions 2–3;
  - `PytestAdapter._collect_invocations` returns owners: `None` for the default suite, `ov` for
    each override.
  - Rewrite `Adapter.collect`'s docstring to the new rule.
- EXPECTED FAILURE: `AssertionError: (['pytest --collect-only -q tests/test_gen1.py'], True, {}) != ([], False, {})`
  (probed).

**Cycle 5: `test_vitest_a_file_the_listing_did_not_name_costs_no_runner_start`.**
- `repo_multi` with `frontend/a.test.ts` and `frontend/b.test.ts`, both empty files. `b` stands
  for another project's test file on a shared root.
- Fake `adapters.vitest_adapter.run_command`:
  - a command containing `--json` returns `(0, json.dumps([{"name": "alpha", "file": str(<a.test.ts>)}]), "")`;
  - every other command is appended to `per_file` and returns `(0, "", "")`.
- Single assertion: `(per_file, collected.failed_files) == ([], {})`.
- GREEN: `VitestAdapter._collect_invocations` returns owners, and nothing else.
- EXPECTED FAILURE:
  `AssertionError: (['npx vitest list b.test.ts'], {'b.test.ts': 'no tests parsed from `npx vitest list` (exit 0): '}) != ([], {})`
  (probed).

**Cycle 6: `test_a_test_file_the_listing_did_not_list_costs_no_runner_start`.**
- `make_adapter(tmp_path)` plus `kernel/tests/helpers.rs` (`pub fn h() {}`).
- Patch `CargoAdapter._run_suite` with a side effect that records each command:
  - `cargo test --tests -- --list…` returns `(0, LIST_OUTPUT, "")`;
  - anything else returns `(0, "", "")`.
- Single assertion: `calls == ["cargo test --tests -- --list 2>&1"]`.
- GREEN: `CargoAdapter._collect_invocations` returns `(…, …, None)`.
- EXPECTED FAILURE: `AssertionError` with a second call
  `cargo test --test helpers -- --list 2>&1` (probed).

**Cycle 7: `test_baseline_reports_how_many_files_fell_to_the_per_file_loop`.**
- `repo` with two more test files written via `backend/tests/test_genN.py`, for 3 test files in
  total.
- Monkeypatch `adapters.pytest_adapter.run_command` so a command ending exactly in
  `--collect-only -q` (the batch) returns `(2, "", "boom")`; delegate everything else to the real
  one. Then `_start(repo)`.
- Single assertion: the `backend` `baseline_captured` line has `.get("per_file_collects") == 3`.
- GREEN: the `Collection.per_file_collects` field, set in `Adapter.collect`, and the serial
  heartbeat only.
- EXPECTED FAILURE: `AssertionError: None != 3`. Probed: today's line holds only `event`,
  `project`, `test_count`, `elapsed_s`, `run_s` and `collect_s`.

**Cycle 8: `test_parallel_baselines_report_how_many_files_fell_to_the_loop`.**
- The same arrangement, but start with
  `run_cli(repo, "run", "start", "--plan", plan, "--baseline-jobs", "2")` after registering the
  plan as `_start` does.
- Single assertion: the same `== 3` assertion as cycle 7.
- GREEN: the `jobs > 1` heartbeat. Refactor phase: build both heartbeats' payload in one helper,
  so the two paths cannot drift again.
- EXPECTED FAILURE: `AssertionError: None != 3`.

**Cycle 9 (refactor): docs.**
- `docs/PRD.md`: R10.3 and R10.3a state decisions 1–3. The `baseline_captured` description names
  `per_file_collects`.
- `CHANGELOG.md` `## [Unreleased]`:
  - a `### Changed` entry: a successful batch is authoritative for its suite's files, so files it
    did not list are no longer started one by one or recorded in `failed_files`;
  - an `### Added` entry: `per_file_collects`.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-168-authoritative-batch-collection   # first, before anything else
    tdd doctor                                  # must report healthy: true
    tdd run start --plan tasks/issue-168-authoritative-batch-collection.md   # captures baselines, opens cycle 1

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is green at
  the plan commit (verified in a fresh worktree: `666 passed`). Expect `baselines: {tddcli: 0}`.
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`: pins 1–3 will ask for it.
    Mutate the base `collect()` logic each one guards.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|environment> --detail '...'`.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.
  - No cycle declares a stub, and no annotation keys are declared.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- cycle 4 changes `Adapter.collect` and `PytestAdapter._collect_invocations` only.
- cycle 5 adds the owner to `VitestAdapter._collect_invocations`, and nothing else.
- cycle 6 adds the owner to `CargoAdapter._collect_invocations`, and nothing else.
- cycle 7 adds `Collection.per_file_collects` and the serial heartbeat field.
- cycle 8 adds the parallel heartbeat field.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-168-authoritative-batch-collection-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-168-authoritative-batch-collection-friction.md
    git commit -m "docs: friction log for issue-168-authoritative-batch-collection"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #168`. Cycle 9 owns the docs:

- `git diff --stat origin/main -- docs/PRD.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.

Nothing a user sees changes beyond one heartbeat field, so no demo recording is required. Quote a
`baseline_captured` line carrying `per_file_collects` in the PR body.
