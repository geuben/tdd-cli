---
closes: 184
cycles:
  - n: 1
    project: tddcli
    title: "doctor's pytest collection probe names its command, exit and stderr when stdout is empty"
    test: "tests/test_doctor_blockers.py::test_a_collection_probe_with_nothing_on_stdout_names_its_command_exit_and_stderr"
    files: ["src/tddcli/adapters/base.py", "src/tddcli/adapters/pytest_adapter.py", "docs/PRD.md"]
    commit_red: "test: a silent pytest collection probe must name its command, exit and stderr"
    commit_green: "fix: doctor's pytest collection probe reports command, exit and stderr when stdout is empty"
    commit_refactor: "refactor: tidy the command-failure description"
  - n: 2
    project: tddcli
    title: "vitest's collection gate names each silent listing's command and exit"
    test: "tests/test_vitest_adapter.py::test_a_listing_that_prints_nothing_names_its_command_and_exit"
    files: ["src/tddcli/adapters/vitest_adapter.py"]
    commit_red: "test: a silent vitest listing must name its command and exit"
    commit_green: "fix: vitest's collection gate never fails with an empty detail"
    commit_refactor: "refactor: tidy the vitest collection gate"
  - n: 3
    project: tddcli
    title: "cargo's collection gate names a silent no-run build's command and exit"
    test: "tests/test_cargo_adapter.py::test_a_no_run_build_that_prints_nothing_names_its_command_and_exit"
    files: ["src/tddcli/adapters/cargo_adapter.py"]
    commit_red: "test: a silent cargo no-run build must name its command and exit"
    commit_green: "fix: cargo's collection gate never fails with an empty detail"
    commit_refactor: "refactor: tidy the cargo collection gate"
  - n: 4
    project: tddcli
    title: "a pytest file that fails to collect records its command, exit and stderr"
    test: "tests/test_batch_collection.py::test_a_file_that_fails_to_collect_records_its_command_exit_and_stderr"
    files: ["src/tddcli/adapters/pytest_adapter.py"]
    commit_red: "test: a pytest per-file collection failure must record its command and exit"
    commit_green: "fix: pytest per-file collection failures record command, exit and output"
    commit_refactor: "refactor: tidy pytest per-file failure reasons"
  - n: 5
    project: tddcli
    title: "a cargo test target that fails to list records its command and exit"
    test: "tests/test_cargo_adapter.py::test_a_target_that_fails_to_list_records_its_command_and_exit"
    files: ["src/tddcli/adapters/cargo_adapter.py"]
    commit_red: "test: a cargo per-file listing failure must record its command and exit"
    commit_green: "fix: cargo per-file collection failures record command, exit and output"
    commit_refactor: "refactor: tidy cargo per-file failure reasons"
  - n: 6
    project: tddcli
    title: "run start's nothing-collected refusal quotes the first file's failure"
    test: "tests/test_baseline_integrity.py::test_a_nothing_collected_refusal_quotes_the_first_failure"
    files: ["src/tddcli/cli.py", "docs/PRD.md"]
    commit_red: "test: run start's collection refusal must quote the first failure"
    commit_green: "fix: run start's collection refusal quotes the first file's failure"
    commit_refactor: "refactor: tidy the collection refusal"
  - n: 7
    project: tddcli
    title: "in split mode, doctor's failed collection check says it ran through the runner as the agent"
    test: "tests/test_split_doctor.py::test_split_doctor_says_a_failed_collection_ran_through_the_runner_as_the_agent"
    files: ["src/tddcli/actor.py", "src/tddcli/cli.py"]
    commit_red: "test: split doctor must say a failed collection ran through the runner"
    commit_green: "fix: split doctor says a failed collection ran through the runner, as the agent"
    commit_refactor: "refactor: tidy actor provenance"
  - n: 8
    project: tddcli
    title: "in split mode, run start's collection refusal says it ran through the runner as the agent"
    test: "tests/test_split_runner.py::test_a_collection_refusal_says_it_ran_through_the_runner_as_the_agent"
    files: ["src/tddcli/cli.py", "CHANGELOG.md"]
    commit_red: "test: split run start must say a collection refusal ran through the runner"
    commit_green: "fix: split run start says a collection refusal ran through the runner, as the agent"
    commit_refactor: "refactor: tidy the split collection refusal"
---

# A collection probe that fails with nothing on stdout crashes doctor and hides the error

## Context

[#184](https://github.com/geuben/tdd-cli/issues/184): in split mode, sudo's `secure_path`
replaced the agent's PATH, so every suite command the runner ran as the agent exited 127. The
error went to stderr only. The host-side cause is fixed in geuben/machine#368. tdd-cli reported
that one error in two unhelpful ways:

1. **`tdd doctor` crashed.** `PytestAdapter.collectable` (`src/tddcli/adapters/pytest_adapter.py`)
   keeps **stdout only** from a failing `--collect-only -q` probe, so it returned
   `GateResult(ok=False, output='')`. `cmd_doctor` passes that to the recorder from
   `_doctor_checklist` (`src/tddcli/cli.py`), which raises
   `AssertionError: doctor check 'collectable' would fail silently` by design.
2. **`tdd run start` refused with no reason.** The refusal in `cmd_run_start` (grep
   `no test could be collected`) names the first failed file but never the reason that
   `collect()` already recorded for it in `Collection.failed_files`.

The issue expects three things:

- a failed `collectable` probe is a failed doctor check, never an `AssertionError`, and with
  stdout empty its detail carries the command, the exit status and the tail of stderr;
- `run start`'s refusal carries the same for at least the first failure;
- in split mode, both messages say the command ran through the runner, as the agent.

### What the planning probes found (E-2, run on `origin/main` in a scratch worktree)

The probes used a `collect_command` of `tdd-184-no-such-tool pytest`, which exits 127 with
`/bin/sh: 1: tdd-184-no-such-tool: not found` on stderr and nothing on stdout.

| Path | Today |
|---|---|
| `tdd doctor`, single mode and `split_runner` | raises the `AssertionError` above out of `run_cli` |
| `tdd doctor` with a pytest override whose `collect_command` also fails | the same `AssertionError` |
| `tdd run start`, single mode and `split_runner` | `backend: no test could be collected — 1 file(s) failed to collect, starting with tests/test_smoke.py. The baseline would …` with no command, exit or stderr |
| `VitestAdapter.collectable`, `collect_command = "sh -c 'exit 3'"` | `GateResult(ok=False, output='')`, so the same doctor crash |
| the same, plus an override with `collect_command = "sh -c 'exit 4'"` | `GateResult(ok=False, output='\n\n')`, which the recorder strips to empty, so the same crash |
| `CargoAdapter.collectable`, `test_command = "sh -c 'exit 3'"` | `GateResult(ok=False, output='')`, so the same doctor crash |
| `PytestAdapter.collect()` per-file reason | `'/bin/sh: 1: tdd-184-no-such-tool: not found'`: stderr, but no command or exit |
| `CargoAdapter.collect()` per-file reason | `''` |
| `VitestAdapter.collect()` per-file reason | ``no tests parsed from `tdd-184-no-such-tool vitest list` (exit 127): /bin/sh: 1: …: not found``: already complete |

The commands cargo ran in the probe were `sh -c 'exit 3' --no-run 2>&1` (the gate),
`sh -c 'exit 3' -- --list 2>&1` (the batch) and `sh -c 'exit 3' --test roundtrip -- --list 2>&1`
(the per-file loop). All exited 3 with empty output.

## Design decisions (locked)

1. **The fix is in the probes. The recorder's guard stays.** Every adapter's `collectable()`
   must never return `ok=False` with blank output. The `AssertionError` in `_doctor_checklist`'s
   `check` is deliberate: PRD §8.1 says "Every failing check carries a `detail` naming what to
   fix, enforced by the recorder", and
   `tests/test_doctor_blockers.py::test_a_check_cannot_fail_without_a_detail` pins it. Do not
   weaken it, and do not catch it in `cmd_doctor`. *Decided by evidence (PRD §8.1, that test).*
2. **One shared helper describes a failed command.** It is `command_failure(command, code,
   text="")` in `src/tddcli/adapters/base.py`, next to `clip_failure`. It returns:
   - ``f"`{command}` exited {code}: {clip_failure(text.strip(), 800)}"`` when `text` is not blank;
   - ``f"`{command}` exited {code} with no output"`` when it is.

   `clip_failure` keeps both ends and weights the tail, so the tail of stderr survives (the
   issue's "tail of stderr"). `command` is the exact string handed to the shell, including any
   `2>&1` or file argument, so that a person can paste it to reproduce. The format follows the
   issue's own example: `` `uv run --frozen pytest --collect-only -q tests/` exited 127: sh: 1:
   uv: not found ``. *Decided by evidence (the issue's example); the helper's place follows the
   convention of `clip_failure` and `_overlap_error` in the same module.*
3. **pytest's gate keeps stdout when there is any** (PRD R10.7: uv's stderr warnings hide
   pytest's real error). Only a probe with **blank stdout** falls back to
   `command_failure(probe_command, code, err)`. This applies to the default probe and to every
   override probe, because the fallback goes in the loop body that handles both. Cycle 1's test
   covers both. *Decided by evidence (the issue's "when stdout is empty", PRD R10.7).*
4. **vitest's and cargo's gates are fixed too.** The issue's first expectation ("a failed
   `collectable` probe is a failed doctor check, never an `AssertionError`") is general, and the
   probes show both adapters crash doctor the same way. Each chunk that would be blank becomes
   `command_failure(command, code)`, and the existing text is kept when it is not blank:
   - vitest: `(err or out).strip()`, for the default listing and for each override's;
   - cargo: `clip_failure(self._errors(out + err))`.

   Exec, gradle and xctest need no change. Their failing gates return literal, non-empty
   messages, or they always pass. *Decided by evidence (probes; the repo note "one cycle per
   adapter that feeds a path").*
5. **Per-file collection reasons carry the command and the exit status, always.** `run start`
   can only quote what `collect()` recorded:
   - pytest's `_collect_per_file` records
     `command_failure(f"{base} --collect-only -q {shlex.quote(rel)}", code, err or out)`.
     That keeps today's choice of text (`err or out`) and replaces today's head-only `[:800]`
     cut with `clip_failure`'s.
   - cargo's `_collect_per_file` records `command_failure(cmd, code, self._errors(out))`, where
     `cmd` is the full per-file command including `2>&1`.
   - vitest's per-file reason already names the command and the exit (probe), so it is unchanged.

   Gradle, xctest and exec override `collect()`, and their reasons are exception text or literal
   messages, so they are out of this path. *Decided by evidence (probes, `Collection.failed_files`
   consumers).*
6. **`run start`'s refusal keeps its first line and gains one.** The error becomes today's text,
   unchanged, then `"\n"`, then `f"{sample}: {collection.failed_files[sample]}"`, where `sample`
   is the same `sorted(collection.failed_files)[0]` the message already names. The envelope's
   `failed_files` list (keys only) and `project` stay as they are. No new result field is added:
   the issue asks for the message to carry it, and `tests/test_baseline_integrity.py` already
   asserts on `error`. *Decided by evidence (the issue).*
7. **Split-mode provenance comes from the actor.** `LocalActor` gains `provenance(self) -> str`,
   which returns `""`. `SudoActor` overrides it to return exactly:

   ```
   f"This ran through the split-mode runner, as {self.agent} (`{self.sudo} -u {self.agent}`):"
   f" its PATH and environment are the ones sudo gives {self.agent}, which can differ from"
   f" {self.agent}'s own shell."
   ```

   Only the runner holds a `SudoActor`, so the actor is the one object that knows the command
   crossed a sudo hop. `cli.py` asks `actor.current().provenance()` and checks no mode flags.
   `src/tddcli/actor.py` is the module that owns "who acts in the agent's territory", and
   provenance does not spawn anything, so `tests/test_actor_seams.py` is unaffected.
   *Decided by convention (the actor seam from issue 142; `_actor_for` in `cli.py` installs it).*
8. **Where provenance is appended.** It goes only on the two messages the issue names, and only
   when `provenance()` is not empty:
   - **doctor:** the `collectable` check's detail becomes `gate.output + "\n" + provenance`
     when `gate.ok` is false;
   - **run start:** the nothing-collected refusal's error gains `"\n" + provenance` after
     decision 6's line.

   Single-mode messages must not change, and cycles 1 and 6 pin that by matching their message
   to its end. *Decided by evidence (the issue's third expectation).*
9. **No ledger change.** `failed_files` reasons are stored as JSON text in existing columns
   (`baseline_cache.failed_files`, the collection rows). Only the text inside them changes, so
   there is no shape change and no `SCHEMA_VERSION` bump. A reused baseline skips the refusal
   (`if name in reused: continue`), so a cached reason in the old format is never quoted.
   *Decided by evidence (`ledger.py`, `cmd_run_start`) and the repo note on schema bumps.*
10. **Docs.** Two PRD additions and one changelog entry:
    - PRD R10.7 gains a sentence: when stdout is blank, the gate's detail is the command, its
      exit status and the tail of stderr (cycle 1).
    - PRD R9.5a gains a sentence: the refusal quotes the first failed file's recorded reason,
      and in split mode says the command ran through the runner, as the agent (cycle 6).
    - `CHANGELOG.md` gets a `### Fixed` entry under `## [Unreleased]` (cycle 8).

    *Decided by convention (`RELEASING.md`, and every earlier plan's docs cycle).*

## Deliberate scope cuts (do not build)

None. The issue names two messages, and this plan changes both for every adapter whose path can
produce a blank one. Two neighbouring paths are left alone because the issue does not ask for
them. They are not cuts:

- the late start-sha probe's `R9.5a: N file(s) failed to collect` reason (`machine.py`);
- the `pytest-json-report installed` check (its detail is stderr, which is not blank in any
  observed failure).

## Fake/real divergence

There are no fakes. Every test runs a real shell command: `tdd-184-no-such-tool …` (exit 127,
stderr only) or `sh -c 'exit N'` (no output at all). Split mode runs through `conftest.sudo_shim`,
which execs the command as the same uid. The one thing the shim does not reproduce is sudo's
`secure_path` rewriting PATH, which is the host's cause and is fixed in geuben/machine#368. This
plan tests what tdd-cli reports, not what sudo does: *acceptable*.

## Cycles

The shell's "not found" wording differs between dash (`/bin/sh: 1: X: not found`) and bash in sh
mode on macOS (`sh: X: command not found`). Both are one line ending in `not found`, so the
regexes below match `[^\n]*not found` and nothing more specific. Every test imports `re` where it
uses one.

Two tests edit a `repo` fixture's `tdd.toml`. They append to it, because the `[project.backend]`
table is the file's last, and then commit (`git(repo, "add", "-A")`,
`git(repo, "commit", "-q", "-m", "...")`) so that the worktree-clean checks stay out of the way.

**Cycle 1: `tests/test_doctor_blockers.py::test_a_collection_probe_with_nothing_on_stdout_names_its_command_exit_and_stderr`.**

- **Setup:** the `repo` fixture. Append the following to `tdd.toml`, then commit:

  ```
  collect_command = "tdd-184-no-such-tool pytest"

  [[project.backend.override]]
  pattern         = "contract/"
  test_command    = "pytest contract"
  collect_command = "tdd-184-other-tool pytest"
  ```

  Then `detail = _check(run_cli(repo, "doctor"), "collectable")["detail"]`, using the module's
  existing `_check` helper.
- **Single assertion:**

  ```python
  re.fullmatch(
      r"`tdd-184-no-such-tool pytest --collect-only -q` exited 127: [^\n]*not found"
      r"\n\n"
      r"`tdd-184-other-tool pytest --collect-only -q` exited 127: [^\n]*not found",
      detail,
  )
  ```

  The match is to the end, so it also pins that single mode appends no provenance.
- **Production:** add `command_failure` to `src/tddcli/adapters/base.py` (decision 2) and import
  it in `pytest_adapter.py`. In `PytestAdapter.collectable`, give the probe string a name, run
  it, and on a non-zero exit append `out.strip() or command_failure(probe, code, err)`.
  Add the R10.7 sentence to `docs/PRD.md`.
- **EXPECTED FAILURE:** `AssertionError: doctor check 'collectable' would fail silently: a failing
  check must name what to fix`, raised out of `run_cli` by `_doctor_checklist`'s `check`
  (probed).

**Cycle 2: `tests/test_vitest_adapter.py::test_a_listing_that_prints_nothing_names_its_command_and_exit`.**

- **Setup:** `(tmp_path / "frontend").mkdir()`. Write this `tdd.toml`:

  ```
  [project.frontend]
  root            = "frontend"
  adapter         = "vitest"
  test_paths      = ["**/*.test.ts"]
  collect_command = "sh -c 'exit 3'"

  [[project.frontend.override]]
  pattern         = "contract/"
  test_command    = "npx vitest run"
  collect_command = "sh -c 'exit 4'"
  ```

  Then build the adapter with `VitestAdapter(config_mod.load(tmp_path).project("frontend"),
  tmp_path)`. The module already imports both names.
- **Single assertion:** `adapter.collectable() == GateResult(ok=False, output="`sh -c 'exit 3'`
  exited 3 with no output\n\n`sh -c 'exit 4'` exited 4 with no output")`. Import `GateResult`
  from `tddcli.adapters.base`.
- **Production:** `VitestAdapter.collectable`. Both the default branch and the override branch
  append `(err or out).strip() or command_failure(<that branch's command>, code)`.
- **EXPECTED FAILURE:** an `AssertionError` comparing against `GateResult(ok=False,
  output='\n\n')` (probed).

**Cycle 3: `tests/test_cargo_adapter.py::test_a_no_run_build_that_prints_nothing_names_its_command_and_exit`.**

- **Setup:** `a = make_adapter(tmp_path, TOML + "test_command = \"sh -c 'exit 3'\"\n")`, using the
  module's own `make_adapter` and `TOML`. There is no patching: the real shell runs.
- **Single assertion:** `a.collectable() == GateResult(ok=False, output="`sh -c 'exit 3'
  --no-run 2>&1` exited 3 with no output")`. Import `GateResult` from `tddcli.adapters.base`.
- **Production:** in `CargoAdapter.collectable`, give the command string a name and return
  `clip_failure(self._errors(out + err)) or command_failure(cmd, code)`.
  `test_collectable_is_a_no_run_build` keeps passing, since its output is not blank.
- **EXPECTED FAILURE:** an `AssertionError` comparing against `GateResult(ok=False, output='')`
  (probed).

**Cycle 4: `tests/test_batch_collection.py::test_a_file_that_fails_to_collect_records_its_command_exit_and_stderr`.**

- **Setup:** the `repo` fixture. Append `collect_command = "tdd-184-no-such-tool pytest"\n` to
  `tdd.toml`; no commit is needed. Then `collected = _adapter(repo).collect()`, using the module's
  `_adapter` helper.
- **Single assertion:**

  ```python
  re.fullmatch(
      r"`tdd-184-no-such-tool pytest --collect-only -q tests/test_smoke\.py`"
      r" exited 127: [^\n]*not found",
      collected.failed_files["tests/test_smoke.py"],
  )
  ```

  The batch fails first, so the file goes through the per-file loop.
- **Production:** `PytestAdapter._collect_per_file` records
  `command_failure(<the per-file command>, code, err or out)` (decision 5).
- **EXPECTED FAILURE:** the fullmatch is `None` against `'/bin/sh: 1: tdd-184-no-such-tool: not
  found'` (probed).

**Cycle 5: `tests/test_cargo_adapter.py::test_a_target_that_fails_to_list_records_its_command_and_exit`.**

- **Setup:** the same as cycle 3. `make_adapter` writes `kernel/tests/roundtrip.rs`, then
  `c = a.collect()`.
- **Single assertion:** `c.failed_files == {"tests/roundtrip.rs": "`sh -c 'exit 3' --test
  roundtrip -- --list 2>&1` exited 3 with no output"}`.
- **Production:** `CargoAdapter._collect_per_file` records
  `command_failure(cmd, code, self._errors(out))`.
  `test_per_file_collection_records_compile_failure_against_its_file` (it asserts `"could not compile" in`
  the reason) keeps passing.
- **EXPECTED FAILURE:** `AssertionError` against `{'tests/roundtrip.rs': ''}` (probed).

**Cycle 6: `tests/test_baseline_integrity.py::test_a_nothing_collected_refusal_quotes_the_first_failure`.**

- **Setup:** the `repo` fixture. Append `collect_command = "tdd-184-no-such-tool pytest"\n` to
  `tdd.toml` and commit. Then `plan = write_plan(repo, PLAN)`, `run_cli(repo, "plan", "register",
  plan)` and `out = run_cli(repo, "run", "start", "--plan", plan)`. `PLAN` is the module's own.
- **Single assertion:**

  ```python
  re.search(
      r"\ntests/test_smoke\.py: `tdd-184-no-such-tool pytest --collect-only -q"
      r" tests/test_smoke\.py` exited 127: [^\n]*not found\Z",
      out["error"],
  )
  ```

  The `\Z` pins that single mode appends no provenance.
- **Production:** in `cmd_run_start`'s nothing-collected refusal, append
  `f"\n{sample}: {collection.failed_files[sample]}"` to the existing message (decision 6). Add
  the R9.5a sentence to `docs/PRD.md`.
  `test_run_start_refuses_when_nothing_could_be_collected` keeps passing.
- **EXPECTED FAILURE:** `re.search` returns `None`. Today's error ends `… Fix the environment
  (dependencies installed?) and retry.` (probed).

**Cycle 7: `tests/test_split_doctor.py::test_split_doctor_says_a_failed_collection_ran_through_the_runner_as_the_agent`.**

- **Setup:** fixtures `repo, split_runner`. Append `collect_command =
  "tdd-184-no-such-tool pytest"\n` to `tdd.toml` and commit (import `git` and `current_user` from
  `conftest`). Then `detail = _check(run_cli(repo, "doctor"), "collectable")["detail"]`.
- **Single assertion:** `f"ran through the split-mode runner, as {current_user()}" in detail`.
- **Production:**
  - add `LocalActor.provenance` and `SudoActor.provenance` to `src/tddcli/actor.py`
    (decision 7);
  - in `cmd_doctor`, when `gate.ok` is false and `actor.current().provenance()` is not empty,
    record the `collectable` check's detail as `gate.output + "\n" + provenance`.
- **EXPECTED FAILURE:** an `AssertionError` on the `in`. After cycle 1 the detail is only the
  `` `…` exited 127: … `` line. (Before cycle 1, the same setup raises the doctor `AssertionError`;
  that was probed under `split_runner`.)

**Cycle 8: `tests/test_split_runner.py::test_a_collection_refusal_says_it_ran_through_the_runner_as_the_agent`.**

- **Setup:** fixtures `repo, split_runner`. Append `collect_command =
  "tdd-184-no-such-tool pytest"\n` to `tdd.toml` and commit (import `git` from `conftest`). Then
  `plan = write_plan(repo, MINIMAL_PLAN)`, `run_cli(repo, "plan", "register", plan)` and
  `out = run_cli(repo, "run", "start", "--plan", plan)`.
- **Single assertion:** `f"ran through the split-mode runner, as {current_user()}" in
  out["error"]`.
- **Production:** in `cmd_run_start`'s nothing-collected refusal, append `"\n" + provenance` when
  `actor.current().provenance()` is not empty. Add the `CHANGELOG.md` entry under `## [Unreleased]`
  → `### Fixed`, naming #184: doctor no longer crashes on a silent collection probe, and both
  messages carry the command, the exit status and the output, plus the split-mode provenance.
- **EXPECTED FAILURE:** an `AssertionError` on the `in`. Under `split_runner`, today's refusal is
  the plain nothing-collected message (probed), and after cycle 6 it ends with the quoted failure.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-184-silent-collection-failures   # first, before anything else
    tdd doctor                                  # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-184-silent-collection-failures.md   # captures baselines, opens cycle 1

`tdd doctor` checks every project; `tdd run start` probes only the ones the plan declares and
those downstream of them through an `[artifact]`. A failing check on a project outside that set
does not stop the run: note it and go on. Any other failing check stops it.

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is green at
  the plan's base (verified in a fresh worktree of `origin/main`: `722 passed`). Expect
  `baselines: {tddcli: 0}`.
- The referee is the released `tdd` on `PATH` (the note at the top of `tdd.toml`), never
  `uv run tdd`.
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`, if a RED pre-passes. Mutate the
    increment that cycle added.
  - `annotate_cycle` → `tdd annotate --key --value`. This plan declares no keys of its own;
    `plan_defect` and `friction_note` are reserved.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|environment> --detail '...'`.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.
  - No cycle declares a stub: every test imports only names that exist today.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- cycle 1 adds `command_failure` and changes `PytestAdapter.collectable`. Nothing else.
- cycle 2 changes `VitestAdapter.collectable`, and nothing else.
- cycle 3 changes `CargoAdapter.collectable`, and not `_collect_per_file`.
- cycle 4 changes `PytestAdapter._collect_per_file`, and nothing else.
- cycle 5 changes `CargoAdapter._collect_per_file`, and nothing else.
- cycle 6 adds the quoted-failure line to the run-start refusal, and no provenance.
- cycle 7 adds `provenance()` to both actors and uses it in `cmd_doctor` only.
- cycle 8 uses `provenance()` in the run-start refusal.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-184-silent-collection-failures-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-184-silent-collection-failures-friction.md
    git commit -m "docs: friction log for issue-184-silent-collection-failures"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #184`. Cycles 1, 6 and 8 own the docs:

- `git diff --stat origin/main -- docs/PRD.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.

The visible change is error text in a JSON envelope, so no demo recording is required. In the PR
body, quote one doctor `collectable` detail and one `run start` refusal produced with a
`collect_command` that exits 127.
