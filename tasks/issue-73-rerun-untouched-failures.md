---
closes: 73
cycles:
  - n: 1
    project: tddcli
    title: "GREEN goes through when an untouched failure passes on rerun"
    test: "tests/test_flaky_reruns.py::test_green_passes_when_an_untouched_failure_passes_on_rerun"
    files: ["src/tddcli/machine.py", "src/tddcli/advance.py"]
    commit_red: "test: GREEN must not block on an untouched failure that passes on rerun"
    commit_green: "feat: rerun a failure outside the cycle once before GREEN blocks on it"
    commit_refactor: "refactor: tidy the GREEN rerun"
  - n: 2
    project: tddcli
    title: "a cleared failure is recorded as flaky_pre_existing with both outcomes"
    test: "tests/test_flaky_reruns.py::test_a_cleared_failure_is_recorded_as_flaky_pre_existing_with_both_outcomes"
    files: ["src/tddcli/machine.py", "docs/PRD.md"]
    commit_red: "test: a failure cleared by a rerun must be recorded as flaky_pre_existing"
    commit_green: "feat: record flaky_pre_existing with the suite and rerun outcomes"
    commit_refactor: "refactor: tidy the flaky_pre_existing event"
  - n: 3
    project: tddcli
    title: "a GREEN failure that fails again carries its rerun outcomes"
    test: "tests/test_flaky_reruns.py::test_a_green_failure_that_fails_again_carries_its_rerun_outcomes"
    files: ["src/tddcli/machine.py", "src/tddcli/advance.py"]
    commit_red: "test: a GREEN failure that fails again must carry its rerun outcomes"
    commit_green: "feat: fix_regression at GREEN carries rerun_outcomes"
    commit_refactor: "refactor: tidy rerun_outcomes at GREEN"
  - n: 4
    project: tddcli
    title: "the close sweep closes when an untouched failure passes on rerun"
    test: "tests/test_flaky_reruns.py::test_the_close_sweep_closes_when_an_untouched_failure_passes_on_rerun"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: the close sweep must not block on an untouched failure that passes on rerun"
    commit_green: "feat: rerun the close sweep's failures before it blocks"
    commit_refactor: "refactor: tidy the close-sweep rerun"
  - n: 5
    project: tddcli
    title: "a close-sweep failure that fails again carries its rerun outcomes"
    test: "tests/test_flaky_reruns.py::test_a_close_sweep_failure_that_fails_again_carries_its_rerun_outcomes"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: a close-sweep failure that fails again must carry its rerun outcomes"
    commit_green: "feat: fix_regression at the close sweep carries rerun_outcomes"
    commit_refactor: "refactor: tidy rerun_outcomes at the close sweep"
  - n: 6
    project: tddcli
    refactor_cycle: true
    title: "extract plan_paths.locate, the one id-to-file resolver"
    files: ["src/tddcli/plan_paths.py"]
    commit_refactor: "refactor: extract plan_paths.locate from resolve"
  - n: 7
    project: tddcli
    title: "a failure in any file the plan declares is not rerun"
    test: "tests/test_flaky_reruns.py::test_a_failure_in_any_file_the_plan_declares_is_not_rerun"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: a failure in a file the plan declares must not be rerun"
    commit_green: "feat: never rerun a failure in a file the plan declares"
    commit_refactor: "refactor: tidy the plan's declared paths"
  - n: 8
    project: tddcli
    title: "a failure in a test the run added is not rerun"
    test: "tests/test_flaky_reruns.py::test_a_failure_in_a_test_the_run_added_is_not_rerun"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: a failure in a test the run added must not be rerun"
    commit_green: "feat: rerun only tests collected when the run started"
    commit_refactor: "refactor: tidy the pre-existing check"
  - n: 9
    project: tddcli
    title: "a failure whose file cannot be resolved is not rerun"
    test: "tests/test_flaky_reruns.py::test_a_failure_whose_file_cannot_be_resolved_is_not_rerun"
    files: ["src/tddcli/machine.py", "docs/PRD.md"]
    commit_red: "test: a failure whose file cannot be resolved must not be rerun"
    commit_green: "feat: never rerun a failure whose file cannot be resolved"
    commit_refactor: "refactor: tidy rerun eligibility"
  - n: 10
    project: tddcli
    title: "each rerun emits a heartbeat"
    test: "tests/test_flaky_reruns.py::test_each_rerun_emits_a_heartbeat"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: each rerun must emit a heartbeat"
    commit_green: "feat: a project_completed heartbeat with phase RERUN per rerun"
    commit_refactor: "refactor: tidy the rerun heartbeat"
  - n: 11
    project: tddcli
    title: "flaky_reruns = 2 reruns until the test passes"
    test: "tests/test_flaky_reruns.py::test_flaky_reruns_two_reruns_until_the_test_passes"
    files: ["src/tddcli/config.py", "src/tddcli/machine.py"]
    commit_red: "test: flaky_reruns = 2 must rerun until the test passes"
    commit_green: "feat: per-project flaky_reruns sets how many reruns a failure gets"
    commit_refactor: "refactor: tidy the rerun loop"
  - n: 12
    project: tddcli
    title: "flaky_reruns = 0 replies exactly as before"
    test: "tests/test_flaky_reruns.py::test_flaky_reruns_zero_replies_exactly_as_before"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: flaky_reruns = 0 must reply exactly as before"
    commit_green: "feat: flaky_reruns = 0 turns reruns off"
    commit_refactor: "refactor: tidy the reruns-off path"
  - n: 13
    project: tddcli
    title: "a flaky_reruns that is not a non-negative integer is refused"
    test: "tests/test_config_and_staging.py::test_flaky_reruns_must_be_a_non_negative_integer"
    files: ["src/tddcli/config.py", "README.md", "docs/PRD.md"]
    commit_red: "test: flaky_reruns must be a non-negative integer"
    commit_green: "feat: refuse a flaky_reruns that is not a non-negative integer"
    commit_refactor: "refactor: tidy flaky_reruns validation"
  - n: 14
    project: tddcli
    title: "GREEN on an exec project goes through when an untouched script passes on rerun"
    test: "tests/test_flaky_reruns.py::test_green_on_an_exec_project_passes_when_an_untouched_script_passes_on_rerun"
    files: ["src/tddcli/adapters/exec_adapter.py", "CHANGELOG.md"]
    commit_red: "test: an untouched exec script that passes on rerun must not block GREEN"
    commit_green: "fix: an exec id names its script's path"
    commit_refactor: "refactor: tidy ExecAdapter.target_path"
  - n: 15
    project: tddcli
    pin_cycle: true
    title: "tdd plan paths resolves an exec id to its script"
    test: "tests/test_plan_paths.py::test_an_exec_id_resolves_to_its_script"
    files: ["src/tddcli/adapters/exec_adapter.py"]
    commit_pin: "test: pin plan paths resolving an exec id to its script"
  - n: 16
    project: tddcli
    pin_cycle: true
    title: "a rerun records no invocation row"
    test: "tests/test_flaky_reruns.py::test_a_rerun_records_no_invocation_row"
    files: ["src/tddcli/machine.py"]
    commit_pin: "test: pin that a rerun records no invocation row"
---

# Rerun an untouched pre-existing failure before it blocks

## Context

[#73](https://github.com/geuben/tdd-cli/issues/73): in a real agent-driven run, a JVM test that
contends for a global dispatcher failed once mid-run. The test lived in a file the plan never
touched and passed when rerun. The run stopped anyway, and a person had to step in only to say
"passes on rerun, not caused by this plan". It was the one human intervention in an otherwise
autonomous multi-cycle run.

The issue asks the tool to do what that person did. Before it reports a failure that is
**outside the plan's declared file set** and **absent from the baseline**, it reruns that test
once, alone, through the adapter:

- if the rerun passes, it records a `flaky_pre_existing` event with both outcomes and carries on;
- if the rerun fails, it reports the failure as today, with two consistent failures as evidence.

The issue sets a scope guard: a flaky test the plan touches is the plan's problem and still
blocks. It also asks for a config knob for the rerun count, with a default of 1.

### What "the blocker" is in the code

`tdd advance` reports a failure outside the cycle by replying `fix_regression`. The phase holds,
and the executor files `tdd blocker --kind pre_existing_failure` (the kind PRD §5 defines for
"a flake, or something the baseline missed"), which halts the run. A failure outside the cycle
reaches that reply on two paths in `src/tddcli/advance.py`:

| Path | Where | Reply today |
|---|---|---|
| GREEN's whole-suite run (R9.1b) | `_handle_impl`, after the second `engine.run_projects` | `fix_regression`, `result = {"other_failures": [...]}` |
| The close sweep (R9.2) | `_handle_refactor`, the `if outcome.failures:` branch after `engine.sweep` | `fix_regression`, `result = {"failures": [...], "commit": sha}` |

RED and pin runs are target-only (R9.1a). They record `others_observed = 0` and never report a
failure elsewhere, so they are out of this path. So is the close sweep's un-baselined-project
reply (`no_baseline_for_project`): with no baseline, "absent from the baseline" cannot be
established. R9.3's plan-completion full sweep has no implementation in `advance.py`
(`Config.full_sweep_projects` has no caller), so there is nothing there to change.

### What the planning probes found (E-2, run on `origin/main` in a scratch worktree)

The flake is a pytest test that counts its own executions in a file **outside the repository**
and fails on chosen ones (the `_flaky` helper below). A counter inside the repo would change the
tree hash and dirty the worktree. Execution numbers in the `repo` fixture, probed:

| Step | Executes `test_legacy`? | Execution number |
|---|---|---|
| `run start` (baseline) | yes | 1 |
| RED `advance` (target-only) | no | — |
| GREEN `advance`, target-only first run (R9.1e) | no | — |
| GREEN `advance`, whole-suite run | yes | 2 |
| close-sweep `advance` after a content edit | yes | 3 |
| each rerun (after the change; probed with a throwaway hack) | yes | the next one |

What each cycle's setup returns today, on `origin/main`:

| Setup | Today |
|---|---|
| flake fails on execution 2, GREEN `advance` | `fix_regression`, `result == {"other_failures": [ID]}`, no `flaky_pre_existing` event |
| flake fails on executions ≥ 2, GREEN `advance` | the same |
| flake fails on execution 3, close-sweep `advance` after a content edit | `fix_regression`, `result == {"failures": [ID], "commit": <sha>}` |
| each of cycle 7's seven declaration cases | `fix_regression` |
| a new test file written after RED, failing on its first execution | `fix_regression`, `other_failures == ["backend::tests/test_new.py::test_new"]` |
| `PytestAdapter.target_path` monkeypatched to return `None` | `fix_regression` |
| `flaky_reruns = 0` or `= 2` appended to `tdd.toml` | the key is ignored (no error); `fix_regression` |
| `config_mod.load` on `flaky_reruns` = `-1`, `1.5`, `"1"`, `true` | loads without error, all four |
| GREEN heartbeats | two `project_completed` lines, both `phase: "AWAITING_IMPL"`; none with `RERUN` |
| exec project, untouched script failing on execution 2, GREEN `advance` | `fix_regression`, `other_failures == ["gates::scripts/check-legacy.sh"]` |
| `plan_paths.resolve` on an exec cycle's `test` | `unresolved`, `reason: "no_path_in_id"` |
| ledger collection snapshot | qualified ids: `{"backend": {"backend::tests/test_smoke.py::test_smoke", "backend::tests/test_legacy.py::test_legacy"}}` |

**Test-side blast radius: none.** Per the repo note, the whole change was hacked into a scratch
worktree (rerun with eligibility, `rerun_outcomes`, the event, the heartbeat,
`ExecAdapter.target_path`). The existing suite stayed green there: `722 passed`, the same count
as `origin/main`. No existing reply gains a key, because `rerun_outcomes` is omitted when it is
empty. No cycle declares `modifies_tests`. The hack and all its probes were then deleted.

## Design decisions (locked)

1. **Where reruns happen.** Reruns happen in GREEN's whole-suite run (`_handle_impl`) and in the
   close sweep (`_handle_refactor`), and nowhere else. In the close sweep they happen only when
   `outcome.failures` is non-empty and `outcome.unbaselined` is empty. The un-baselined reply
   comes first and is unchanged. *Decided by evidence (the table above, R9.1a, R9.5d).*
2. **What makes a failure eligible for a rerun.** A failure is eligible only when **all** of
   these hold:
   - (a) its project's `flaky_reruns` is at least 1;
   - (b) it is in the run's collection snapshot (`ledger.collection(run_id)[project]`), so it
     existed when the run started;
   - (c) its file can be resolved;
   - (d) that file is not in the plan's declared set.

   "Absent from the baseline" needs no check of its own: both paths already subtract the
   baseline (R9.6). The reasons for each condition:
   - (b) is what "pre-existing" means in the issue's title, and a test the run wrote is the
     run's own. It also covers a target adopted under R8.9, which is new by definition. A
     late-probed project (R9.5d) records an empty collection snapshot, so its tests are never
     rerun. That is conservative and deliberate.
   - (c) and (d) are the issue's scope guard. A test whose file cannot be placed cannot be shown
     to be outside the plan.

   *Decided by evidence (the issue's title, proposal and scope guard; P5 "plan scope is declared,
   never discovered").*
3. **The plan's declared set is plan-wide, not the current cycle's.** It is the union, over
   **every** declared cycle (`engine.declared`), of:
   - the cycle's `files` and `stub_expected` entries, as written;
   - the repository-relative file of every `test` and `modifies_tests` id, each qualified with
     `Engine._qualify(cycle, id)` and resolved with `plan_paths.locate` (decision 4), skipping
     ids that do not resolve;
   - the plan's `ancillary_files` (`engine.ancillary_files`).

   A failing test whose repository-relative file is `rel` is declared when `rel` is in the set,
   **or** when `project.relative_to_root(rel)` is in the set. Plans write `files` and
   `stub_expected` in either form, and `staging.classify` accepts both for `stub_expected`. One
   consequence: in a multi-project plan, a project-relative entry also covers the same relative
   path in another project. That errs toward not rerunning, which is the safe side.
   *Decided by evidence (the issue says "the plan's declared file set" and "a file the plan never
   touches"; the `staging.classify` precedent).*
4. **One resolver from a test id to its file: `plan_paths.locate`.** Cycle 6, a refactor,
   extracts the per-id resolution in `plan_paths.resolve` into:

   ```python
   def locate(adapter, project, native: str, scan_cache: dict) -> tuple[str | None, str]:
   ```

   It returns `(repository-relative path, "")` when the id resolves, and `(None, reason)`
   otherwise. `reason` is one of `"no_path_in_id"`, `"not_found_in_sources"` or
   `"ambiguous_id"`, exactly as today. It tries `adapter.target_path(native)` first, then falls
   back to `adapter.scan_target_paths()` (cached in `scan_cache` under `project.name`). It joins
   the result with `os.path.normpath(os.path.join(project.root, …))`. `resolve` then calls
   `locate` and keeps its output byte-identical, which the existing `tests/test_plan_paths.py`
   guards. Rerun eligibility calls the same function, so `tdd plan paths` and the reruns cannot
   drift apart.

   **Mechanism footgun:** `plan_paths.py` imports `Engine` from `machine.py` at module level, so
   `machine.py` must import `plan_paths` *inside* the method that uses it (`from . import
   plan_paths`). A module-level import is a circular-import error at CLI start.
   *Decided by convention (`plan_paths.resolve` already lazy-imports `adapters`; R7.14 is the
   resolver's spec).*
5. **How a rerun runs.** Each rerun is
   `adapters.build(engine.config.project(name), engine.worktree).run(test_id, target_only=True)`,
   one test per invocation ("in isolation"), with the failures taken in list order. Its outcome is
   `verdict.target_outcome`. Only `"passed"` clears the test. `failed`, `not_found` and
   `not_collected` all count as not passing. Reruns stop at the first pass, after at most
   `flaky_reruns` attempts.
   - **No invocation row.** Never route a rerun through `Engine.run_projects`, which writes an
     `invocation` row. Such a row would add an AWAITING_IMPL row that R9.1e's "the whole-suite
     run is the attempt's last invocation" does not expect, and it would inflate
     `impl_attempts_total` in `tdd metrics`. Cycle 16 pins this. *Decided by convention: the late
     start-sha probe (`Engine.probe_at_start_sha`) also runs suites without invocation rows.*
   - **One heartbeat per rerun:**
     `heartbeat(event="project_completed", project=name, phase="RERUN", elapsed_s=…)`.
     *Decided by convention: `run_projects`, `sweep` and the late probe ("LATE_PROBE") each emit
     one per suite execution, unconditionally (the comment in `run_projects`).*
   - Spawns go through the adapter and so through `src/tddcli/actor.py`. No new spawn site
     (`tests/test_actor_seams.py`).
6. **The event.** When a rerun passes, the tool writes
   `engine.ledger.event(run_id, cycle_id, "flaky_pre_existing", json.dumps({"test": <qualified
   id>, "phase": <"AWAITING_IMPL" | "CLOSE_SWEEP">, "outcomes": [<suite outcome>, <each rerun's
   outcome>…]}))`. The first outcome is always `"failed"`, from the suite run, and the last is
   `"passed"`. The cleared test leaves `other_failures` / `failures`. When nothing remains, the
   phase proceeds exactly as if the suite had not reported it (GREEN commits; the cycle closes).
   The whole-suite invocation row still lists the test in its `other_failures`, because that row
   records what the run saw. The phase labels are the invocation `phase_at` values of the two
   paths. It is a new integrity-event *kind* in the existing `integrity_event` table, so there is
   no shape change and no `SCHEMA_VERSION` bump. *Decided by evidence (the issue names the event
   and "both outcomes"; the repo note on schema bumps).*
7. **When a rerun also fails.** The reply is today's, with the same verb, the same detail text and
   `other_failures` / `failures` listing every test still failing. The one addition is
   `rerun_outcomes`, a dict from the id of every *eligible* test that never passed to its
   outcomes list (`["failed", "failed"]` under the default). It is passed as
   `**({"rerun_outcomes": reruns} if reruns else {})`, so a reply with no reruns is
   byte-identical to today's. No ledger event is written for this case: the executor files
   `tdd blocker` with this evidence, as today. *Decided by evidence (the issue says "raise the
   blocker as today (now with two consistent failures as evidence)"). The key name follows the
   envelope's snake_case result keys and the event's `outcomes`. That is convention.*
8. **The knob: `flaky_reruns`, per project in `tdd.toml`, default 1.**
   - It is a non-negative integer.
   - `0` turns reruns off for that project. The test is then not eligible (decision 2a), so the
     reply is exactly today's, with no `rerun_outcomes`.
   - Any other value raises `ConfigError(f"project {name!r}: flaky_reruns must be a
     non-negative integer")` when the file is loaded. **Footgun:** `bool` is a subclass of `int`,
     so `isinstance(True, int)` is true. Refuse `bool` explicitly
     (`isinstance(v, bool) or not isinstance(v, int) or v < 0`).
   - The field is `Project.flaky_reruns: int = 1`, parsed in `config.load` beside `timeout` and
     `baseline_max_failure_ratio`.

   *Decided by evidence for the default (the issue: "default 1"), and by convention for the
   place, the per-project scope and the error's shape (the sibling knobs `timeout` and
   `baseline_max_failure_ratio`). The issue's motivating suite is one project's JVM tests, and a
   project whose single-test startup is expensive can turn reruns off alone.*
9. **Exec ids resolve to their script.** `ExecAdapter.target_path(native)` returns `native`: an
   exec id *is* the script's path relative to the project root. R7.14 already says exec ids carry
   their path ("For adapters whose id grammar carries a file component (pytest, cargo integration
   tests, exec), the path is extracted directly"), but the method was never written. The probe
   shows `no_path_in_id`. Without it, decision 2c would never rerun an exec failure. As a side
   effect, `tdd plan paths` now resolves exec ids, which cycle 15 pins. *Decided by evidence
   (R7.14, the probe).*
10. **Known limit, accepted:** a genuine regression that fails only when run with the rest of the
    suite, and passes alone, is cleared and recorded as `flaky_pre_existing`. The issue chose an
    isolated rerun, and the event puts the case in the ledger for an auditor. Each eligible
    failure costs up to `flaky_reruns` single-test runs, and only on a path that would otherwise
    have replied `fix_regression`. *Decided by evidence (the issue's "in isolation" and its
    knob).*
11. **Docs.**
    - PRD §5 *IntegrityEvent*: add `flaky_pre_existing` to the typed list (cycle 2).
    - PRD §6.1 *New failures elsewhere*: add one sentence, and add a new **R9.1f** in §9.1 with
      the text under cycle 9 (cycle 9).
    - PRD §7.1: add a new **R7.15** for the knob (cycle 13).
    - README: a new `### Untouched failures are rerun before they block` subsection after
      `### Environment-dependent suites` (cycle 13).
    - `CHANGELOG.md` under `## [Unreleased]`: an `### Added` entry and a `### Fixed` entry
      (cycle 14).

    *Decided by convention (`RELEASING.md`; every earlier plan's docs placement; `tdd.toml`'s
    project root is the repository, so these are in-project `files`).*

## Deliberate scope cuts (do not build)

None. Two neighbouring things stay unchanged. They are outside the issue, not cuts:

- the close sweep's un-baselined-project reply (decision 1);
- the `fix_regression` detail strings, which keep today's wording (decision 7).

## Fake/real divergence

| Seam | Fake behaviour | Real behaviour | Production path left untested | Ruling |
|---|---|---|---|---|
| The execution-counting test (`_flaky`) | fails on chosen execution numbers, deterministically | a flake fails at random | none: the tool sees a failing then passing test either way | acceptable |
| `PytestAdapter.target_path` monkeypatched to `None` (cycle 9) | a pytest id that carries no path | cargo `lib::` ids, and gradle/xctest ids that the source scan does not place in exactly one file | the scan branch of `locate`, which `tests/test_plan_paths.py` already covers for gradle and xctest | acceptable |

Everything else is real: real pytest through the `repo` fixture, and real bash scripts through
the exec adapter.

## Cycles

All new tests in `tests/test_flaky_reruns.py` share one module header, which **cycle 1's RED
writes in full**. Later cycles add only their test function, plus any import the cycle names.

```python
"""Untouched pre-existing failures are rerun before they block (#73, PRD R9.1f).

The flake is a test that counts its own executions in a file outside the repository
and fails on chosen ones: `run start`'s baseline is execution 1, RED's and GREEN's
target-only runs never execute it, GREEN's whole-suite run is execution 2, a close
sweep after a content edit is execution 3, and each rerun is the next one.
"""

from __future__ import annotations

import json

from conftest import git, run_cli, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger

ID = "backend::tests/test_legacy.py::test_legacy"

PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding"
    test: "tests/test_add.py::test_adding"
    files: ["app/calc.py"{files}]
{extra}    commit_red: "test: adding"
    commit_green: "feat: add"
    commit_refactor: "refactor: add"
{more}---
"""


def _flaky(counter, rule, name="test_legacy"):
    """A test that counts its executions in `counter` and fails while `rule` holds for `n`."""
    return (
        f"def {name}():\n"
        "    import pathlib\n"
        f"    p = pathlib.Path({str(counter)!r})\n"
        "    n = int(p.read_text()) + 1 if p.exists() else 1\n"
        "    p.write_text(str(n))\n"
        f"    assert not ({rule}), n\n"
    )


def _to_green(
    repo, counter, rule, *, files="", extra="", more="", where="tests/test_legacy.py", toml=""
):
    """Commit the flaky test at `where`, start a run, confirm RED on test_adding and write
    the implementation. Returns the run id; the next `tdd advance` is GREEN."""
    (repo / "backend" / where).write_text(_flaky(counter, rule))
    if toml:  # the fixture's [project.backend] table is the file's last
        with open(repo / "tdd.toml", "a") as f:
            f.write(toml)
    calc = repo / "backend" / "app" / "calc.py"
    calc.write_text("def add(a, b):\n    raise NotImplementedError\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "flaky legacy test")
    plan = write_plan(repo, PLAN.format(files=files, extra=extra, more=more))
    run_cli(repo, "plan", "register", plan)
    run_id = run_cli(repo, "run", "start", "--plan", plan)["run"]["id"]
    add = repo / "backend" / "tests" / "test_add.py"
    head = add.read_text() + "\n\n" if add.exists() else ""
    add.write_text(
        head + "from app.calc import add\n\n\ndef test_adding():\n    assert add(2, 3) == 5\n"
    )
    run_cli(repo, "advance")  # RED
    calc.write_text("def add(a, b):\n    return a + b\n")
    return run_id


def _flaky_events(repo, run_id):
    ledger = Ledger(gitutil.repo_identity(repo))
    return [json.loads(d) for d in ledger.event_details(run_id, "flaky_pre_existing")]
```

The lint gate (`uv run ruff check`, which selects `F`) fails on an unused import. So the header
imports only what cycle 1 uses: cycle 7 adds `import shutil`, cycle 9 adds the `PytestAdapter`
import, and cycle 14 adds `import stat`, each in the cycle that first uses it.

**Cycle 1: `tests/test_flaky_reruns.py::test_green_passes_when_an_untouched_failure_passes_on_rerun`.**

- **Setup:** `repo, tmp_path`. `_to_green(repo, tmp_path / "count", "n == 2")`, then
  `out = run_cli(repo, "advance")`.
- **Single assertion:** `out["next_action"]["verb"] == "refactor_or_advance"`.
- **Production:**
  - add `Engine.rerun_untouched(self, cycle_row, phase, failures) -> tuple[list[str],
    dict[str, list[str]]]` to `src/tddcli/machine.py`. It returns the failures still failing
    and the rerun outcomes of those that were rerun.
  - In this cycle it reruns **every** failure once (decision 5's call) and drops each one that
    passes. It returns the remaining list and an empty dict.
  - In `_handle_impl`, call it on `others` after the whole-suite run, when `others` is
    non-empty. Keep the remaining list in `others`.
- **EXPECTED FAILURE:** `AssertionError: assert 'fix_regression' == 'refactor_or_advance'`
  (probed).

**Cycle 2: `tests/test_flaky_reruns.py::test_a_cleared_failure_is_recorded_as_flaky_pre_existing_with_both_outcomes`.**

- **Setup:** `run_id = _to_green(repo, tmp_path / "count", "n == 2")`, then
  `run_cli(repo, "advance")`.
- **Single assertion:** `_flaky_events(repo, run_id) == [{"test": ID, "phase": "AWAITING_IMPL",
  "outcomes": ["failed", "passed"]}]`.
- **Production:** `rerun_untouched` writes decision 6's event for each cleared test, with the
  `phase` its caller passes (`_handle_impl` passes `AWAITING_IMPL`). Add `flaky_pre_existing` to
  PRD §5's *IntegrityEvent* list, with one sentence: an untouched pre-existing failure that
  passed when rerun alone (R9.1f).
- **EXPECTED FAILURE:** `AssertionError: assert [] == [{'outcomes': ['failed', 'passed'], …}]`.
  No such event exists before this cycle (probed).

**Cycle 3: `tests/test_flaky_reruns.py::test_a_green_failure_that_fails_again_carries_its_rerun_outcomes`.**

- **Setup:** `_to_green(repo, tmp_path / "count", "n >= 2")`, then `out = run_cli(repo, "advance")`.
- **Single assertion:** `(out["next_action"]["verb"], out["result"]["other_failures"],
  out["result"].get("rerun_outcomes")) == ("fix_regression", [ID], {ID: ["failed", "failed"]})`.
  The two-entry list also pins the default of one rerun.
- **Production:** `rerun_untouched` returns each rerun test that never passed, with its outcomes
  list. `_handle_impl`'s `fix_regression` reply passes
  `**({"rerun_outcomes": reruns} if reruns else {})` (decision 7).
- **EXPECTED FAILURE:** an `AssertionError`: the third element is `None`, because the reply
  carries only `other_failures` (probed: `{"other_failures": [ID]}`).

**Cycle 4: `tests/test_flaky_reruns.py::test_the_close_sweep_closes_when_an_untouched_failure_passes_on_rerun`.**

- **Setup:** `run_id = _to_green(repo, tmp_path / "count", "n == 3")`. Then
  `run_cli(repo, "advance")` (GREEN, execution 2, passes). Then make a content edit, so the §6.1
  skip does not drop the cycle's own suite (repo note), and advance again:

  ```python
  (repo / "backend" / "app" / "calc.py").write_text(
      "def add(a, b):\n    total = a + b\n    return total\n"
  )
  out = run_cli(repo, "advance")  # the close sweep: execution 3
  ```
- **Single assertion:** `(out["next_action"]["verb"], [e["phase"] for e in _flaky_events(repo,
  run_id)]) == ("complete", ["CLOSE_SWEEP"])`.
- **Production:** in `_handle_refactor`, right after `outcome = engine.sweep(...)`: when
  `outcome.failures` is non-empty and `outcome.unbaselined` is empty, set
  `outcome.failures, sweep_reruns = engine.rerun_untouched(cycle, "CLOSE_SWEEP",
  outcome.failures)`. `SweepOutcome.ok` then reads the remaining list.
- **EXPECTED FAILURE:** an `AssertionError` against `('fix_regression', [])` (probed:
  `fix_regression` with `failures == [ID]`, and no event).

**Cycle 5: `tests/test_flaky_reruns.py::test_a_close_sweep_failure_that_fails_again_carries_its_rerun_outcomes`.**

- **Setup:** as cycle 4, with rule `"n >= 3"`, and `out` from the close-sweep advance.
- **Single assertion:** `(out["next_action"]["verb"], out["result"]["failures"],
  out["result"].get("rerun_outcomes")) == ("fix_regression", [ID], {ID: ["failed", "failed"]})`.
- **Production:** the close sweep's `fix_regression` reply (the `if outcome.failures:` branch)
  passes `**({"rerun_outcomes": sweep_reruns} if sweep_reruns else {})`.
- **EXPECTED FAILURE:** an `AssertionError`: the third element is `None` (probed: the reply is
  `{"failures": [ID], "commit": …}`).

**Cycle 6 (refactor): extract `plan_paths.locate`.**

- **Change:** decision 4. `resolve` keeps its loop over cycles and fields, and its output.
  Only the per-id resolution moves into `locate(adapter, project, native, scan_cache)`.
- **Guard:** the existing `tests/test_plan_paths.py` (gradle and xctest scans, cargo integration
  and `lib::` ids, ambiguous and not-found ids, the root-`.` normalisation, all qualification
  forms). No behaviour change. If any of those tests must change, that is a blocker
  (`plan_defect`), not a refactor commit.

**Cycle 7: `tests/test_flaky_reruns.py::test_a_failure_in_any_file_the_plan_declares_is_not_rerun`.**

- **Setup:** add `import shutil` to the module. Make one fresh copy of the `repo` fixture per case, made with
  `shutil.copytree(repo, tmp_path / name)` before any run starts. The ledger is keyed by the
  repository's path (`gitutil.repo_identity`), so each copy is an independent repository and
  ledger (probed). For each case, `_to_green(case, tmp_path / f"{name}-count", "n == 2", **kw)`,
  then `verbs[name] = run_cli(case, "advance")["next_action"]["verb"]`. The cases:

  ```python
  CASES = {
      "files_project_relative": {"files": ', "tests/test_legacy.py"'},
      "files_repo_relative": {"files": ', "backend/tests/test_legacy.py"'},
      "stub_expected": {"extra": '    stub_expected: ["tests/test_legacy.py"]\n'},
      "modifies_tests": {"extra": '    modifies_tests: ["tests/test_legacy.py::test_legacy"]\n'},
      "target_file": {"where": "tests/test_add.py"},
      "ancillary_files": {"more": 'ancillary_files: ["backend/tests/test_legacy.py"]\n'},
      "later_cycle": {
          "more": (
              "  - n: 2\n    project: backend\n    title: \"later\"\n"
              '    test: "tests/test_later.py::test_later"\n'
              '    files: ["tests/test_legacy.py"]\n'
              '    commit_red: "test: l"\n    commit_green: "feat: l"\n'
          )
      },
  }
  ```

  In `target_file`, `test_legacy` lives in the cycle's own target file (the failing id is
  `backend::tests/test_add.py::test_legacy`). `_to_green` keeps it there and appends
  `test_adding` below it. All seven plans register, and all seven reply `fix_regression` today
  (probed).
- **Single assertion:** `verbs == dict.fromkeys(CASES, "fix_regression")`.
- **Production:** `rerun_untouched` skips (keeps as failing, never reruns) a failure whose file
  `plan_paths.locate` resolves to a path in the plan's declared set (decision 3). That set is
  built inside the method, which imports `plan_paths` there (decision 4's footgun). A failure
  whose file does **not** resolve stays eligible in this cycle.
- **EXPECTED FAILURE:** an `AssertionError`: every case is `refactor_or_advance`. Reasoned from
  probes: cycle 1's after-state, rule `n == 2`, gives `refactor_or_advance` on the rerun at
  execution 3. All seven setups give `fix_regression` on `origin/main`.

**Cycle 8: `tests/test_flaky_reruns.py::test_a_failure_in_a_test_the_run_added_is_not_rerun`.**

- **Setup:** `_to_green(repo, tmp_path / "count", "False")`, so `test_legacy` never fails. Then,
  before GREEN, write a new test file that the start-of-run collection never saw:
  `(repo / "backend" / "tests" / "test_new.py").write_text(_flaky(tmp_path / "new-count",
  "n == 1", "test_new"))`. Then `out = run_cli(repo, "advance")`. GREEN's whole-suite run is
  `test_new`'s first execution (probed: the counter reads `1` afterwards).
- **Single assertion:** `(out["next_action"]["verb"], out["result"]["other_failures"]) ==
  ("fix_regression", ["backend::tests/test_new.py::test_new"])`.
- **Production:** `rerun_untouched` skips a failure that is not in
  `engine.ledger.collection(engine.run["id"]).get(project, set())` (decision 2b).
- **EXPECTED FAILURE:** an `AssertionError`: the verb is `refactor_or_advance`. `tests/test_new.py`
  is undeclared, so cycle 7's check lets it through, and its rerun is execution 2, which passes.
  Reasoned from the probes; on `origin/main` the same setup gives `fix_regression`.

**Cycle 9: `tests/test_flaky_reruns.py::test_a_failure_whose_file_cannot_be_resolved_is_not_rerun`.**

- **Setup:** `repo, tmp_path, monkeypatch`. Add `from tddcli.adapters.pytest_adapter import
  PytestAdapter` to the module imports. `_to_green(repo, tmp_path / "count", "n == 2")`. **Then**
  `monkeypatch.setattr(PytestAdapter, "target_path", lambda self, native: None)`. Patching after
  `run start` keeps `plan register`'s target lint, which calls `target_path`, out of it. Then
  `out = run_cli(repo, "advance")`. The base adapter's `scan_target_paths` returns `None`, so
  `locate` gives `(None, "no_path_in_id")`.
- **Single assertion:** `(out["next_action"]["verb"], out["result"]["other_failures"]) ==
  ("fix_regression", [ID])`.
- **Production:**
  - `rerun_untouched` skips a failure whose file does not resolve (decision 2c).
  - Docs, `docs/PRD.md`: §6.1's *New failures elsewhere* bullet gains: "An untouched pre-existing
    failure is rerun alone first; one that passes does not hold the phase (R9.1f)."
  - Add to §9.1, after R9.1e:

    > **R9.1f** Before `advance` replies `fix_regression` for a failure in GREEN's whole-suite run
    > (R9.1b) or in a close sweep (R9.2), it reruns that test alone (a target-only run of that one
    > id), up to the project's `flaky_reruns` times (R7.15), when the failure is untouched and
    > pre-existing: absent from the baseline (R9.6), collected at `run start`, and in a file the
    > plan does not declare in any cycle (`files`, `stub_expected`, the file of a `test` or
    > `modifies_tests` id as R7.14 resolves it, or `ancillary_files`). A test whose file cannot
    > be resolved is never rerun. A rerun that passes clears the failure: it is recorded as a
    > `flaky_pre_existing` integrity event `{test, phase, outcomes}` and the phase proceeds as if
    > the suite had not reported it. A test that never passes stays in the reply, which carries
    > `rerun_outcomes: {test: outcomes}` as evidence. Reruns write no invocation row; each emits a
    > `project_completed` heartbeat with phase `RERUN`. Decided in #73.
- **EXPECTED FAILURE:** an `AssertionError`: the verb is `refactor_or_advance`. The unresolved
  file is still eligible after cycle 7. Reasoned; on `origin/main` the same setup gives
  `fix_regression`.

**Cycle 10: `tests/test_flaky_reruns.py::test_each_rerun_emits_a_heartbeat`.**

- **Setup:** `repo, tmp_path, capsys`. `_to_green(repo, tmp_path / "count", "n == 2")`, then
  `capsys.readouterr()` to drop the setup's lines, then `run_cli(repo, "advance")`. Then
  `lines = [json.loads(x) for x in capsys.readouterr().err.splitlines() if x.startswith("{")]`.
  `run_cli` redirects stdout only, so the heartbeats on stderr reach `capsys` (probed, as in
  `tests/test_heartbeat.py`).
- **Single assertion:** `[{k: v for k, v in h.items() if k != "elapsed_s"} for h in lines if
  h.get("phase") == "RERUN"] == [{"event": "project_completed", "project": "backend", "phase":
  "RERUN"}]`.
- **Production:** decision 5's heartbeat, one per rerun, timed with `time.monotonic()` like
  `run_projects`.
- **EXPECTED FAILURE:** `AssertionError: assert [] == [{…'phase': 'RERUN'}]` (probed: only the
  two `AWAITING_IMPL` lines).

**Cycle 11: `tests/test_flaky_reruns.py::test_flaky_reruns_two_reruns_until_the_test_passes`.**

- **Setup:** `run_id = _to_green(repo, tmp_path / "count", "n in (2, 3)", toml="flaky_reruns =
  2\n")`, then `run_cli(repo, "advance")`. The suite run is execution 2 and fails. The first rerun
  is execution 3 and fails. The second rerun is execution 4 and passes (probed in the after-state).
- **Single assertion:** `[e["outcomes"] for e in _flaky_events(repo, run_id)] ==
  [["failed", "failed", "passed"]]`.
- **Production:** add `Project.flaky_reruns: int = 1` and parse
  `body.get("flaky_reruns", 1)` in `config.load`. **No validation yet.** `rerun_untouched`
  reruns up to `project.flaky_reruns` times and stops at the first pass.
- **EXPECTED FAILURE:** `AssertionError: assert [] == [['failed', 'failed', 'passed']]`. With
  one rerun the test fails again, so there is no event. Reasoned; on `origin/main` the key is
  ignored and the reply is `fix_regression` (probed).

**Cycle 12: `tests/test_flaky_reruns.py::test_flaky_reruns_zero_replies_exactly_as_before`.**

- **Setup:** `_to_green(repo, tmp_path / "count", "n == 2", toml="flaky_reruns = 0\n")`, then
  `out = run_cli(repo, "advance")`.
- **Single assertion:** `(out["next_action"]["verb"], out["result"]) == ("fix_regression",
  {"other_failures": [ID]})`. This is today's reply exactly (probed on `origin/main`).
- **Production:** `rerun_untouched` treats a project whose `flaky_reruns` is `0` as not eligible
  (decision 2a), so there is no `rerun_outcomes` entry.
- **EXPECTED FAILURE:** an `AssertionError`: after cycle 11, a zero-iteration loop leaves the
  test failing with `rerun_outcomes == {ID: ["failed"]}`, so `result` has an extra key.
  Reasoned.

**Cycle 13: `tests/test_config_and_staging.py::test_flaky_reruns_must_be_a_non_negative_integer`.**

- **Setup:** `tmp_path`. For each `value` in `("-1", "1.5", '"1"', "true")`, write
  `(tmp_path / "tdd.toml").write_text('[project.backend]\nroot = "backend"\nadapter =
  "pytest"\ntest_paths = ["tests/"]\n' + f"flaky_reruns = {value}\n")`. Then call
  `config_mod.load(tmp_path)` and append `str(exc)` on `config_mod.ConfigError`, or `None` when
  it loads. The module already imports `config_mod`.
- **Single assertion:** `messages == ["project 'backend': flaky_reruns must be a non-negative
  integer"] * 4`.
- **Production:**
  - decision 8's check in `config.load`, refusing `bool` explicitly.
  - Docs, `docs/PRD.md` §7.1, after R7.14:

    > **R7.15** A project may declare `flaky_reruns`, a non-negative integer (default 1): how many
    > times R9.1f reruns an untouched pre-existing failure before reporting it. `0` turns reruns
    > off for that project. Any other value is refused when `tdd.toml` is loaded.
  - README: add `### Untouched failures are rerun before they block` after `### Environment-dependent
    suites`. In a few sentences, say:
    - which failures are rerun (R9.1f's conditions);
    - that a pass is recorded as `flaky_pre_existing` (visible in `tdd metrics` under
      `integrity_events`);
    - that a repeat failure's reply carries `rerun_outcomes`.

    Then show the knob:

    ```toml
    [project.android]
    root = "android"
    adapter = "gradle"
    flaky_reruns = 0    # a JVM start per rerun is too slow here; report failures at once
    ```
- **EXPECTED FAILURE:** `AssertionError: assert [None, None, None, None] == [...]` (probed: all
  four load without error).

**Cycle 14: `tests/test_flaky_reruns.py::test_green_on_an_exec_project_passes_when_an_untouched_script_passes_on_rerun`.**

- **Setup:** `repo, tmp_path`. Add `import stat` and a `_sh(path, body)` helper to the module, copied from
  `tests/test_suite_scope.py` (writes `#!/bin/bash\n` + body, sets the executable bits; uses
  `stat`). Then:
  - `counter = tmp_path / "exec-count"`.
  - Overwrite `repo / "tdd.toml"` with `'[project.gates]\nroot = "gates"\nadapter =
    "exec"\ntest_paths = ["scripts/check-*.sh"]\nlint = []\ntypecheck = []\n'`.
  - `(repo / "gates" / "lib").mkdir(parents=True)`.
  - `_sh(repo / "gates" / "scripts" / "check-legacy.sh", f'n=$(( $(cat {counter} 2>/dev/null ||
    echo 0) + 1 )); echo $n > {counter}; test $n -ne 2')`.
  - Commit (`git add -A`, `git commit`).
  - `write_plan` this plan, then `plan register` and `run start`:

    ```
    ---
    cycles:
      - n: 1
        project: gates
        title: t
        test: "scripts/check-answer.sh"
        files: ["lib/answer.txt"]
        commit_red: "test: t"
        commit_green: "feat: t"
    ---
    ```

  - RED: `_sh(repo / "gates" / "scripts" / "check-answer.sh", 'test "$(cat lib/answer.txt)" =
    42')` and `run_cli(repo, "advance")`.
  - Write `(repo / "gates" / "lib" / "answer.txt").write_text("42\n")`, then
    `out = run_cli(repo, "advance")`.

  The baseline is the script's execution 1 and GREEN's whole-suite run is execution 2. Its
  rerun is execution 3 (probed, before and after).
- **Single assertion:** `out["next_action"]["verb"] == "refactor_or_advance"`.
- **Production:**
  - `ExecAdapter.target_path(self, native) -> str | None` returns `native` (decision 9).
  - `CHANGELOG.md`, under `## [Unreleased]`:
    - `### Added`: **An untouched pre-existing failure is rerun before it blocks** (#73). Name
      the conditions; per-project `flaky_reruns` (default 1, `0` off); the `flaky_pre_existing`
      event; `rerun_outcomes` on a repeat failure.
    - `### Fixed`: **`tdd plan paths` resolves exec ids to their script** (#73), as R7.14 already
      stated; before this it reported `no_path_in_id`.
- **EXPECTED FAILURE:** `AssertionError: assert 'fix_regression' == 'refactor_or_advance'`. The
  exec id does not resolve, so cycle 9 keeps it from a rerun. Reasoned; probed `fix_regression`
  with `other_failures == ["gates::scripts/check-legacy.sh"]` on `origin/main`.

**Cycle 15 (pin): `tests/test_plan_paths.py::test_an_exec_id_resolves_to_its_script`.**

- **Setup:** `tmp_path`, the module's `_resolve` helper. `toml = '[project.gates]\nroot =
  "gates"\nadapter = "exec"\ntest_paths = ["scripts/check-*.sh"]\n'`. `plan_text =
  '---\ncycles:\n  - n: 1\n    project: gates\n    title: t\n    test:
  "scripts/check-answer.sh"\n    commit_red: x\n    commit_green: x\n---\n'`.
- **Single assertion:** `_resolve(tmp_path, toml, plan_text)["paths"] == [{"cycle": 1, "field":
  "test", "id": "scripts/check-answer.sh", "project": "gates", "path":
  "gates/scripts/check-answer.sh"}]`. This shape was probed in the after-state.
- **Why a pin:** cycle 14's `ExecAdapter.target_path` already makes it pass. This pins that
  consumer of `locate`, which decision 9 names.
- **Sensitivity mutation:** make `ExecAdapter.target_path` return `None`. The test must fail
  (`[] == [...]`), then restore.

**Cycle 16 (pin): `tests/test_flaky_reruns.py::test_a_rerun_records_no_invocation_row`.**

- **Setup:** `_to_green(repo, tmp_path / "count", "n == 2")`, then `run_cli(repo, "advance")`
  (the cleared GREEN). Then `rows = Ledger(gitutil.repo_identity(repo)).all("SELECT phase_at,
  others_observed FROM invocation ORDER BY id", ())`.
- **Single assertion:** `[tuple(r) for r in rows] == [("AWAITING_TEST", 0), ("AWAITING_IMPL", 0),
  ("AWAITING_IMPL", 1)]`. These are the rows of a GREEN with no rerun. The throwaway after-state
  hack gave exactly these rows for a cleared exec GREEN, and the pytest flow goes through the
  same `_handle_impl`.
- **Why a pin:** decision 5 already forbids the row, so the test passes on arrival.
- **Sensitivity mutation:** in `rerun_untouched`, make the rerun write an invocation row (for
  example `engine.ledger.record_invocation(...)` with `phase_at=phase`, or route the rerun through
  `self.run_projects`). The test must fail with a fourth row, then restore.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-73-rerun-untouched-failures   # first, before anything else
    tdd doctor                                  # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-73-rerun-untouched-failures.md   # captures baselines, opens cycle 1

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
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is green
  at the plan's base, verified in a fresh worktree of `origin/main` (`722 passed`). Expect
  `baselines: {tddcli: 0}`.
- The referee is the released `tdd` on `PATH` (the note at the top of `tdd.toml`), never
  `uv run tdd`. The referee does not run this plan's reruns. Only the suites under test do.
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`. It is mandatory for pin cycles
    15 and 16, using each cycle's named mutation. It also comes up if a standard RED pre-passes;
    then mutate the increment that cycle's GREEN would add.
  - `annotate_cycle` → `tdd annotate --key --value`. This plan declares no keys of its own;
    `plan_defect` and `friction_note` are reserved.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|tooling|regression> --detail '...'`.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.
  - No cycle declares a stub. Every test imports only names that exist today, and the new
    production names are reached through `run_cli` and `config_mod.load`.
  - Cycle 6 is a refactor cycle: it opens in `refactor_or_advance`, and the existing suite is
    its guard.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- cycle 1 adds `Engine.rerun_untouched`, which reruns every failure once and drops each that
  passes, and calls it from `_handle_impl`. No event, no eligibility, no `rerun_outcomes`, no
  heartbeat, no knob.
- cycle 2 adds the `flaky_pre_existing` event only.
- cycle 3 returns the outcomes of tests that failed again and adds `rerun_outcomes` to
  `_handle_impl`'s reply only.
- cycle 4 calls `rerun_untouched` from `_handle_refactor` with `"CLOSE_SWEEP"`. Not
  `rerun_outcomes` in that reply.
- cycle 5 adds `rerun_outcomes` to the close sweep's reply.
- cycle 6 moves code only.
- cycle 7 adds the declared-set check for a **resolved** file. An unresolved file stays eligible,
  and there is no collection check.
- cycle 8 adds the start-of-run collection check only.
- cycle 9 makes an unresolved file ineligible, and adds the R9.1f and §6.1 text.
- cycle 10 adds the heartbeat only.
- cycle 11 adds `Project.flaky_reruns` (parsed, **not validated**) and the up-to-N loop. Nothing
  special for `0`.
- cycle 12 makes `flaky_reruns == 0` ineligible.
- cycle 13 adds validation, R7.15 and the README subsection.
- cycle 14 adds `ExecAdapter.target_path` and the changelog.
- cycles 15 and 16 add tests only.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-73-rerun-untouched-failures-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-73-rerun-untouched-failures-friction.md
    git commit -m "docs: friction log for issue-73-rerun-untouched-failures"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #73`. Cycles 2, 9, 13 and 14 own the docs:

- `git diff --stat origin/main -- docs/PRD.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- README.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.

The visible change is a JSON envelope field and a ledger event, so no demo recording is
required. In the PR body, quote one cleared GREEN's `flaky_pre_existing` event detail and one
repeat failure's `rerun_outcomes`, from cycles 2 and 3's setups.
