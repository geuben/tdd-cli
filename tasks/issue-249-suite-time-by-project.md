---
closes: 249
cycles:
  - n: 1
    project: tddcli
    title: "tdd metrics reports suite time per project, a close sweep credited to the project it ran"
    test: "tests/test_time_report.py::test_metrics_reports_suite_time_by_project"
    files: ["src/tddcli/ledger.py", "src/tddcli/render.py"]
    modifies_tests: ["tests/test_time_report.py::test_metrics_reports_suite_time_by_phase_and_the_wall_clock"]
    commit_red: "test: tdd metrics must report suite time per project"
    commit_green: "feat: tdd metrics reports time.by_project"
    commit_refactor: "refactor: tidy the per-project time summary"
  - n: 2
    project: tddcli
    pin_cycle: true
    title: "a run with no invocations has an empty time.by_project"
    test: "tests/test_time_report.py::test_metrics_by_project_is_empty_for_a_run_with_no_invocations"
    files: []
    commit_pin: "test: pin that a run with no suite runs has an empty time.by_project"
  - n: 3
    project: tddcli
    pin_cycle: true
    title: "time.by_project sums to the suite total, in seconds and in runs"
    test: "tests/test_time_report.py::test_metrics_by_project_sums_to_the_suite_total"
    files: []
    commit_pin: "test: pin that the projects' suite time and runs sum to the run's"
  - n: 4
    project: tddcli
    title: "the friction log's Time section tables suite time per project"
    test: "tests/test_time_report.py::test_the_friction_log_tables_suite_time_by_project"
    files: ["src/tddcli/render.py", "docs/PRD.md", "docs/split-runner.md", "README.md", "CHANGELOG.md"]
    modifies_tests: ["tests/test_time_report.py::test_the_friction_log_carries_a_time_section"]
    commit_red: "test: the friction log must table suite time per project"
    commit_green: "feat: the friction log tables suite time per project"
    commit_refactor: "docs: suite time per project in the PRD, README, split-runner guide and changelog"
---

# Issue 249: suite time per project in `tdd metrics` (`time.by_project`)

## Context

Issue #249. `tdd metrics --json` says how much of a run's time went to suites, by phase
(`time.by_phase`) and by cycle (`time.cycles`), but not **which project** it went to.
geuben/machine needs per-project suite time to compare toolchains (Xcode, Gradle, a compose
stack, cargo) and decide whether builds move to shared builders (geuben/machine#418,
geuben/machine#419).

The ledger already holds what is needed. Every `invocation` row has `project` (`NOT NULL`),
`phase_at` and `duration_ms`. A cycle's `suite_s` cannot stand in for its project's time,
because the close sweep (`Engine.sweep` in `src/tddcli/machine.py`, using
`Config.close_sweep_projects`) runs the cycle's projects plus every project downstream of an
artifact the cycle touched. It records each swept project's invocation **under that project's
name** (`record_invocation(..., phase_at="CLOSE_SWEEP", project=name, ...)`) and **under the
cycle that triggered it** (verified in the planning checkout).

**Done when** (from the issue):
- `tdd metrics --json` has `time.by_project` for every run, and it is `{}` for a run with no
  invocations (cycles 1 and 2).
- A test with invocations in two projects and a close sweep shows the sweep's time under the
  swept project, and both invariants hold (cycles 1 and 3).
- It is in a release (scope cut below: releasing is a separate maintainer step).

Nothing new is recorded. Everything here is a projection in `src/tddcli/render.py`
(`_time_summary` → `_time_json` for `tdd metrics`, `_time_section` for the friction log) plus
one new ledger read beside `Ledger.suite_time_by_phase`.

## Design decisions (locked)

1. **The JSON shape.** *Decided by the issue's proposal.* Each run's `time` object gains
   `by_project`, keyed by project name. Each value is
   `{"runs": <int>, "suite_s": <float>, "by_phase": {<phase_at>: {"runs": <int>, "suite_s": <float>}}}`.
   Every other `time` key is unchanged: `wall_clock_s`, `suite_s`, `suite_share`, `by_phase`
   and `cycles`.

2. **Every invocation of the run counts, close sweeps included, credited to the project that
   ran.** *Decided by the issue, verified in the code.* The grouping is by `invocation.project`
   over `WHERE run_id = ?`, exactly the rows `suite_time_by_phase` sums. It is never by cycle,
   and never by a cycle's declared `projects`. Every invocation the tool records has a
   `cycle_id` today (both `record_invocation` calls in `machine.py` pass `cycle_row["id"]`),
   but the query does not depend on that.

3. **One new ledger read, `Ledger.suite_time_by_project(run_id)`.** *Decided by the issue
   ("a ledger query beside `suite_time_by_phase`, grouping by `project` and `phase_at`") and by
   convention.* It sits directly after `suite_time_by_phase` in `src/tddcli/ledger.py`:

   ```python
   def suite_time_by_project(self, run_id: int) -> list[sqlite3.Row]:
       """(project, phase_at, n, ms) over every invocation of the run."""
       return self.all(
           "SELECT project, phase_at, COUNT(*) n, SUM(duration_ms) ms FROM invocation"
           " WHERE run_id = ? GROUP BY project, phase_at",
           (run_id,),
       )
   ```

   It goes in `GUEST_READS`, in alphabetical order after `suite_time_by_phase`. The convention
   is that a read keyed by `run_id` that the renderers call is a guest read, like
   `suite_time_by_phase` and `cycle_times`. Two tests force this:
   - `tests/test_ledger_surface.py::test_every_ledger_method_is_classified_and_scoped` fails
     on an unclassified public method.
   - `tests/test_ledger_service.py::test_a_guest_renders_its_own_friction_log` renders the
     friction log through a guest. `_time_summary` makes this read, so the service refuses it
     with `method_not_allowed` unless it is a guest read.

   It needs no `service._foreign` change, because it takes `run_id`.

4. **No schema change.** *Decided by evidence.* The read uses existing `invocation` columns.
   `SCHEMA_VERSION` does not change, so the referee needs no freezing.

5. **One source.** *Decided by the issue and by convention (#147's decision 3).*
   - `_time_summary` computes `by_project`. It holds unrounded seconds (`ms / 1000`), like
     `by_phase`.
   - `_time_json` rounds each project's `suite_s` and each project-phase's `suite_s` to one
     decimal, as it already does for `by_phase`. `runs` are integers.
   - `tdd metrics`, `tdd progress --json`, `tdd ledger metrics` and the report socket's
     `metrics` method all return `render.metrics`, so they gain the key with no wiring change.

6. **Order.** *Settled by convention.*
   - In `_time_summary`, projects are in name order (`sorted`).
   - Each project's `by_phase` uses the same `order` key as `time.by_phase` (`PHASE_ORDER`,
     then any other `phase_at`, sorted).
   - JSON object key order is not part of the contract (the tests compare dicts).
   - The friction log's row order is part of the contract, and cycle 4 pins it: its fixture
     records `server` first, but `client` is the first row.

7. **`{}` for a run with no invocations.** *Decided by the issue.* No rows means an empty
   dict, never a missing key or `None`.

8. **The invariants.** *Decided by the issue.* In `time.by_project`:
   - the `suite_s` values sum to `time.suite_s`;
   - the `runs` values sum to the runs in `time.by_phase`.

   Cycle 3 pins both on the two-project fixture. Its durations are whole seconds, so the
   float sums are exact. The two sides come from different queries (`suite_time_by_phase`
   versus `suite_time_by_project`), so the check is not circular.

9. **The friction log gains a per-project table; `tdd metrics` has no text output to change.**
   *Settled by evidence and convention.*
   - The issue says "the text output and the friction log may gain a per-project table".
   - `cmd_metrics` (`src/tddcli/cli.py`) only ever returns the JSON envelope, so the
     friction log is the one text view.
   - `_time_section` already renders every breakdown `_time_summary` makes (the phase table,
     #145's cycle table), so the new breakdown gets a table too.
   - The table goes between the Phase table and the Cycle table:
     `| Project | Suite runs | Suite (min) | Average (s) |`. It has one row per project, in
     name order, with the Phase table's formats (`:.1f` minutes, `:.1f` average seconds).
   - It shows project totals only. The per-project phase split stays JSON-only, since the
     issue says "the JSON is what geuben/machine reads".

10. **Docs and changelog.** *Settled by convention* (#147 put its docs in its last cycle's
    refactor phase; `CHANGELOG.md` is hand-edited under `## [Unreleased]`, per `RELEASING.md`).
    The ledger-service upgrade note follows 0.17.0's `delivered_run` and 0.18.0's
    `reference_paths` entries: a 0.18.0 host refuses the new read with `method_not_allowed`.
    The exact text is in cycle 4.

11. **External readers of `tdd metrics` are only gaining a key.** *Settled by evidence*
    (`.claude/plan-issue/render-friction-log-consumers.md`). geuben/dispatch reads `tdd metrics`
    keys, and `implement-issue`/`raise-pr` read the friction log's header and intervention list.
    Nothing is renamed or removed, and the friction-log change is inside `## Time`, which
    neither skill parses. The PR body still names geuben/dispatch and geuben/machine as readers.

## Deliberate scope cuts (do not build)

- **Cutting a release** (the issue's third done-when). Premise: *the run cannot reach it*.
  - Per `RELEASING.md`, a release is its own PR: bump `__version__`, move `Unreleased`
    under a version, merge, tag, then create a GitHub Release, which publishes to PyPI. 0.18.0
    was #245.
  - An implementation run delivers the change and its `## [Unreleased]` line. The next
    release carries it, after which geuben/machine bumps `tdd_cli_version`.
- **A per-project phase table in the friction log.** Premise: *named non-goal*. The issue
  asks only for "a per-project table" in text and says the JSON is what is read. The JSON
  carries the per-project phase split.

## Cycles

### Shared fixture changes (cycle 1's RED)

`tests/test_time_report.py` already has `_at`, `RUNS` and `_ledger(tmp_path)`. In cycle 1's
RED:

- Generalise `_ledger` with two keyword parameters whose defaults keep today's ledger
  byte-for-byte:

  ```python
  def _ledger(tmp_path, runs=None, cycle_projects=("p", "p")):
      """A run that started at 10:00 and was blocked at 10:10. Cycle 1 ran 10:00-10:04;
      cycle 2 opened at 10:04 and never closed. `runs` are (cycle ordinal, phase, project,
      duration_ms); the default is RUNS, all in project `p`."""
      if runs is None:
          runs = [(ordinal, phase, "p", ms) for ordinal, phase, ms in RUNS]
      ...
  ```

  - Each cycle row's `projects` becomes `json.dumps([cycle_projects[ordinal - 1]])`, which is
    `'["p"]'` by default, as today.
  - The invocation loop becomes `for ordinal, phase, project, ms in runs:` with
    `project=project`.
- Add, after `CYCLES`:

  ```python
  # (cycle ordinal, phase, project, duration_ms): cycle 1 is `server`'s, and its close sweep
  # also ran `client`, downstream of an artifact cycle 1 touched. Cycle 2 is `client`'s.
  SPLIT_RUNS = [
      (1, "AWAITING_TEST", "server", 30000),
      (1, "AWAITING_IMPL", "server", 30000),
      (1, "CLOSE_SWEEP", "server", 30000),
      (1, "CLOSE_SWEEP", "client", 60000),
      (2, "AWAITING_TEST", "client", 12000),
      (2, "AWAITING_IMPL", "client", 18000),
      (2, "CLOSE_SWEEP", "client", 18000),
  ]


  def _split_ledger(tmp_path):
      return _ledger(tmp_path, SPLIT_RUNS, ("server", "client"))
  ```

Hand-worked from `SPLIT_RUNS`, all whole seconds and exact at one decimal:
- **Suite:** 198 s (3.3 min), 7 runs. Wall clock 600 s, so the share is 0.33 (33%).
- **By phase:**
  - `AWAITING_TEST`: 2 runs, 42 s (0.7 min), averaging 21.0 s.
  - `AWAITING_IMPL`: 2 runs, 48 s (0.8 min), averaging 24.0 s.
  - `CLOSE_SWEEP`: 3 runs, 108 s (1.8 min), averaging 36.0 s.
- **By project:**
  - `server`: 3 runs, 90 s (1.5 min), averaging 30.0 s. Each of `AWAITING_TEST`,
    `AWAITING_IMPL` and `CLOSE_SWEEP` has 1 run of 30 s.
  - `client`: 4 runs, 108 s (1.8 min), averaging 27.0 s. `AWAITING_TEST` has 1 run of 12 s,
    `AWAITING_IMPL` 1 run of 18 s, and `CLOSE_SWEEP` 2 runs of 78 s. That 78 s is 60 s swept
    under cycle 1 plus 18 s under cycle 2.
- **By cycle:**
  - Cycle 1: wall 4.0 min, suite 150 s (2.5 min), 4 runs. It includes `client`'s 60 s sweep,
    which is why a cycle cannot stand in for a project.
  - Cycle 2: wall `—`, suite 48 s (0.8 min), 3 runs.

**Probed** in a fresh worktree of `origin/main` (deleted afterwards), with this exact fixture:
- `render.metrics(ledger, "/wt")["runs"][0]["time"]` gave `suite_s` 198.0, `suite_share`
  0.33, the `by_phase` and `cycles` values above, and **no `by_project` key**.
- `SELECT project, phase_at, COUNT(*), SUM(duration_ms) … GROUP BY project, phase_at`
  returned exactly the per-project rows above.
- The friction log's `## Time` section was the phase and cycle tables below, with no
  Project table.
- After `DELETE FROM invocation WHERE run_id = ?`, `time` had `by_phase: {}` and still no
  `by_project`.

### Cycle 1: `tdd metrics` reports suite time per project

- **Test** `test_metrics_reports_suite_time_by_project(tmp_path, ledger_home)`:
  - `ledger, _ = _split_ledger(tmp_path)`, then `m = render.metrics(ledger, "/wt")["runs"][0]`.
  - Single assertion:

    ```python
    assert m["time"].get("by_project") == {
        "client": {
            "runs": 4,
            "suite_s": 108.0,
            "by_phase": {
                "AWAITING_TEST": {"runs": 1, "suite_s": 12.0},
                "AWAITING_IMPL": {"runs": 1, "suite_s": 18.0},
                "CLOSE_SWEEP": {"runs": 2, "suite_s": 78.0},
            },
        },
        "server": {
            "runs": 3,
            "suite_s": 90.0,
            "by_phase": {
                "AWAITING_TEST": {"runs": 1, "suite_s": 30.0},
                "AWAITING_IMPL": {"runs": 1, "suite_s": 30.0},
                "CLOSE_SWEEP": {"runs": 1, "suite_s": 30.0},
            },
        },
    }
    ```

    `client`'s `CLOSE_SWEEP` of 2 runs and 78 s is the sweep cycle 1 triggered, credited to
    the project that ran (decision 2).
- **Modifies** `test_metrics_reports_suite_time_by_phase_and_the_wall_clock`. Its whole-`time`
  dict gains, between `"by_phase"` and `"cycles"`:

  ```python
  "by_project": {
      "p": {
          "runs": 7,
          "suite_s": 222.0,
          "by_phase": {
              "AWAITING_TEST": {"runs": 2, "suite_s": 60.0},
              "AWAITING_IMPL": {"runs": 3, "suite_s": 102.0},
              "CLOSE_SWEEP": {"runs": 2, "suite_s": 60.0},
          },
      },
  },
  ```

  Nothing else in it changes. It fails in RED too, until GREEN.
- **Production targets:**
  - `src/tddcli/ledger.py`: `Ledger.suite_time_by_project`, plus its `GUEST_READS` entry
    (decision 3).
  - `src/tddcli/render.py`: `_time_summary` builds `by_project` from it (decisions 5 and 6),
    and `_time_json` rounds it (decision 5).
- **EXPECTED FAILURE** (probed: there is no `by_project` key today):
  `AssertionError: assert None == {'client': {'by_phase': {...}, 'runs': 4, 'suite_s': 108.0}, 'server': {...}}`.

### Cycle 2: pin. A run with no invocations has `by_project == {}`

- **Test** `test_metrics_by_project_is_empty_for_a_run_with_no_invocations(tmp_path, ledger_home)`:
  - `ledger, run_id = _ledger(tmp_path)`, then
    `ledger._write("DELETE FROM invocation WHERE run_id = ?", (run_id,))`.
  - `m = render.metrics(ledger, "/wt")["runs"][0]`.
  - Single assertion: `assert m["time"].get("by_project") == {}`.
- **Kind: pin.** It passes on arrival once cycle 1 builds `by_project` from the grouped rows
  (decision 7). If it fails on arrival, cycle 1 left the empty case out: stop and raise
  `tdd blocker --kind plan_defect`. Do not add the case here as implementation.
- **Sensitivity mutation:** in `_time_summary`, set `by_project` to `None` when the read
  returns no rows. The test fails with `assert None == {}`.

### Cycle 3: pin. The projects sum to the suite total, in seconds and in runs

- **Test** `test_metrics_by_project_sums_to_the_suite_total(tmp_path, ledger_home)`:
  - `ledger, _ = _split_ledger(tmp_path)`, then `t = render.metrics(ledger, "/wt")["runs"][0]["time"]`.
  - Single assertion:

    ```python
    assert (
        sum(p["suite_s"] for p in t["by_project"].values()),
        sum(p["runs"] for p in t["by_project"].values()),
    ) == (t["suite_s"], sum(p["runs"] for p in t["by_phase"].values()))
    ```

    Both sides are `(198.0, 7)`. The right side comes from `suite_time_by_phase` and the
    left from `suite_time_by_project`, so they are derived independently (decision 8).
- **Kind: pin.** It passes on arrival after cycle 1. If it fails on arrival, cycle 1's query
  drops or double-counts rows: stop and raise `tdd blocker --kind plan_defect`.
- **Sensitivity mutation:** add `AND phase_at != 'CLOSE_SWEEP'` to
  `suite_time_by_project`'s `WHERE`. The left side becomes `(90.0, 4)` and the test fails.

### Cycle 4: the friction log tables suite time per project

- **Test** `test_the_friction_log_tables_suite_time_by_project(tmp_path, ledger_home)`:
  - `ledger, run_id = _split_ledger(tmp_path)`.
  - `text = render.friction_log(ledger, ledger.one("SELECT * FROM run WHERE id = ?", (run_id,)))`.
  - `section = text.split("\n## Time\n", 1)[1].split("\n## ", 1)[0] if "\n## Time\n" in text else ""`.
  - Single assertion: `assert section.strip() == SPLIT_TIME_SECTION.strip()`, where
    (at module level, without the indentation shown here):

    ```python
    SPLIT_TIME_SECTION = """
    - Wall clock: 10.0 min. Suite: 3.3 min (33%).

    | Phase | Suite runs | Suite (min) | Average (s) |
    |---|---|---|---|
    | AWAITING_TEST | 2 | 0.7 | 21.0 |
    | AWAITING_IMPL | 2 | 0.8 | 24.0 |
    | CLOSE_SWEEP | 3 | 1.8 | 36.0 |

    | Project | Suite runs | Suite (min) | Average (s) |
    |---|---|---|---|
    | client | 4 | 1.8 | 27.0 |
    | server | 3 | 1.5 | 30.0 |

    | Cycle | Wall (min) | Suite (min) | Suite runs |
    |---|---|---|---|
    | 1 | 4.0 | 2.5 | 4 |
    | 2 | — | 0.8 | 3 |
    """
    ```

    `server`'s rows were inserted first, and `client` comes first: name order (decision 6).
- **Modifies** `test_the_friction_log_carries_a_time_section`. Its `TIME_SECTION` gains,
  between the Phase table and the Cycle table, a blank line and:

  ```
  | Project | Suite runs | Suite (min) | Average (s) |
  |---|---|---|---|
  | p | 7 | 3.7 | 31.7 |
  ```

  This is 222 s = 3.7 min, and 222 / 7 = 31.71 s.
- **Production target:** `src/tddcli/render.py`, `_time_section`. After the Phase rows,
  append a blank line, the Project header and separator, and one row per
  `summary["by_project"]` entry:
  `f"| {project} | {p['runs']} | {p['suite_s'] / 60:.1f} | {p['suite_s'] / p['runs']:.1f} |"`.
- **EXPECTED FAILURE** (probed: the section today is the Phase and Cycle tables with no Project
  table): `AssertionError: assert '- Wall clock: 10.0 min. Suite: 3.3 min (33%).\n\n| Phase | …\n\n| Cycle | …' == '- Wall clock: 10.0 min. Suite: 3.3 min (33%).\n\n| Phase | …\n\n| Project | …'`.
- **Refactor phase: the docs** (decision 10). No production code changes here.
  - `docs/PRD.md` §11.1, the "Suite duration and wall clock" row: change "summed per phase and
    per cycle" to "summed per phase, per project (a close sweep under the project it ran) and
    per cycle".
  - `docs/split-runner.md`: the paragraph ending "with `closed_at` and `wall_clock_s` null
    while the cycle is open." gains a sentence: "It also carries `time.by_project`: each
    project's suite `runs`, `suite_s` and `by_phase`, over every invocation of the run, so a
    close sweep counts under the project it ran and the projects sum to `time.suite_s`."
  - `README.md`:
    - "The friction log" paragraph's "per phase and per cycle." becomes "per phase, per
      project and per cycle."
    - The `tdd metrics` paragraph's "suite time per phase against the run's wall clock"
      becomes "suite time per phase and per project against the run's wall clock".
  - `CHANGELOG.md`, under `## [Unreleased]`, a new `### Added` heading with:

    ```markdown
    - **Suite time per project** (#249). Each run in `tdd metrics` (and `tdd ledger metrics`
      and the report socket's `metrics`) carries `time.by_project`: each project's suite
      `runs`, `suite_s` and `by_phase`, over every invocation of the run. A close sweep's
      time counts under the project it ran, not the cycle that triggered it, and the
      projects sum to `time.suite_s`. A run with no suite runs has `{}`. The friction log's
      `## Time` section gains a per-project table. With a ledger service, upgrade the host
      with or before its guests: a 0.18.0 host refuses the new `suite_time_by_project` read,
      made by `tdd metrics` and `tdd log render`, with `method_not_allowed`.
    ```

### Behaviour census

| Promise | Test |
|---|---|
| `time.by_project` per project: runs, seconds, per-phase split | cycle 1 |
| a close sweep's time is credited to the swept project | cycle 1 (`client`'s `CLOSE_SWEEP`: 2 runs, 78.0 s) |
| a single-project run's `by_project` mirrors `by_phase` | cycle 1's modification of `test_metrics_reports_suite_time_by_phase_and_the_wall_clock` |
| `{}` for a run with no invocations | cycle 2 |
| projects' `suite_s` sum to `time.suite_s`; projects' `runs` sum to the run's | cycle 3 |
| the friction log's Project table, in name order | cycle 4 |
| a guest's `tdd metrics` / `tdd log render` can make the new read | existing `tests/test_ledger_service.py::test_a_guest_renders_its_own_friction_log` (fails if the read is not in `GUEST_READS`) and `tests/test_ledger_surface.py::test_every_ledger_method_is_classified_and_scoped` |
| `tdd progress --json`, `tdd ledger metrics`, the report socket carry it | all return `render.metrics`, unchanged wiring (decision 5) |

**Test-side blast radius.** Found by grepping `tests/` for `"time"`, `wall_clock_s`,
`suite_share`, `## Time` and `Suite runs`. Exactly two tests assert the whole `time` object or
the whole `## Time` section, and both are declared in `modifies_tests`:
- `test_metrics_reports_suite_time_by_phase_and_the_wall_clock`, in cycle 1;
- `test_the_friction_log_carries_a_time_section`, in cycle 4.

`test_metrics_reports_each_cycles_time` and `test_metrics_measures_a_live_runs_wall_clock_to_now`
read single keys and are unaffected.

There are no fakes (the ledger is real SQLite), no mirrors (`_time_summary` is the one
source), no generated artifacts, no schema change, no `docs/INVARIANTS.md` and no `perturb/`
ledger. The numbers are fixture arithmetic, not performance targets.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-249-suite-time-by-project   # first, before anything else
    tdd doctor                                  # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-249-suite-time-by-project.md   # captures baselines, opens cycle 1

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
  at the plan's base (verified in a fresh worktree of `origin/main` on 2026-11-08: `898 passed`).
  Expect `baselines: {tddcli: 0}`.
- The referee is the released `tdd` on `PATH` (the note at the top of `tdd.toml`), never
  `uv run tdd`. It is 0.18.0 and has none of this plan's behaviour, so this run's own
  `tdd metrics` has no `time.by_project` and its friction log has no Project table.
  `SCHEMA_VERSION` does not change.
- Every RED, GREEN and REFACTOR edit must pass `uv run ruff check` and `uv run mypy` (the
  close sweep's gates). `Ledger.suite_time_by_project` is annotated like
  `suite_time_by_phase` (`-> list[sqlite3.Row]`).
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`. Cycles 2 and 3 are pins and
    will ask for it. Use the mutation each cycle names, then restore it. Any standard RED
    that pre-passes also asks: mutate the increment that cycle added.
  - `annotate_cycle` → `tdd annotate --key --value`. This plan declares no keys of its own;
    `plan_defect` and `friction_note` are reserved.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|regression|tooling> --detail '...'`.
    A pin that fails on arrival (cycles 2 and 3) is `plan_defect`.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- **Cycle 1:**
  - `Ledger.suite_time_by_project` and its `GUEST_READS` entry;
  - `by_project` in `_time_summary` (name order, phases in `PHASE_ORDER`);
  - its rounding in `_time_json`.

  Not `_time_section`.
- **Cycle 2:** a pin. Only its test.
- **Cycle 3:** a pin. Only its test.
- **Cycle 4:** the Project table in `_time_section`. Its refactor phase carries the docs and
  the CHANGELOG entry, and no production code.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-249-suite-time-by-project-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-249-suite-time-by-project-friction.md
    git commit -m "docs: friction log for issue-249-suite-time-by-project"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #249`. Cycle 4's refactor phase owns the docs:

- `git diff --stat origin/main -- docs/PRD.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- docs/split-runner.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- README.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.
- `git diff origin/main -- src/tddcli/ledger.py | grep -c SCHEMA_VERSION` must print `0`
  (decision 4).

The visible change is JSON and friction-log content, so no demo recording is required. In the
PR body:

- paste cycle 1's `by_project` value and cycle 4's Project table;
- name the readers of `tdd metrics`: geuben/machine (this issue's consumer) and
  geuben/dispatch, for whom the change only adds a key (decision 11);
- repeat the ledger-service upgrade note from the CHANGELOG;
- say that a release is a separate step (scope cut), after which geuben/machine can bump
  `tdd_cli_version`.
