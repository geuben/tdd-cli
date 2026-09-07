---
closes: 108
cycles:
  - n: 1
    project: tddcli
    title: "run start records the start sha on the run row"
    test: "tests/test_late_baseline.py::test_run_start_records_the_start_sha_on_the_run_row"
    files: ["src/tddcli/cli.py", "src/tddcli/ledger.py"]
    commit_red: "test: run start records run.start_sha"
    commit_green: "feat: run.start_sha — HEAD at run start, recorded on the run row"

  - n: 2
    project: tddcli
    title: "a v9 ledger is migrated in place to v10 and gains run.start_sha"
    test: "tests/test_release_surface.py::test_run_gains_start_sha_column"
    files: ["src/tddcli/ledger.py"]
    commit_red: "test: v9 ledger gains run.start_sha on open"
    commit_green: "feat: ledger schema v10 — run.start_sha migration"

  - n: 3
    project: tddcli
    title: "gitutil.temporary_worktree checks out a sha in a throwaway worktree and removes it on exit"
    test: "tests/test_late_baseline.py::test_temporary_worktree_checks_out_the_sha_and_is_removed_on_exit"
    stub_expected: ["src/tddcli/gitutil.py"]
    files: ["src/tddcli/gitutil.py"]
    commit_red: "test: temporary_worktree checks out a sha and cleans up"
    commit_green: "feat: gitutil.temporary_worktree — detached worktree at a sha, removed on exit"

  - n: 4
    project: tddcli
    title: "temporary_worktree links the ignored directories directly under a project root"
    test: "tests/test_late_baseline.py::test_temporary_worktree_links_ignored_directories_under_the_project_root"
    files: ["src/tddcli/gitutil.py"]
    commit_red: "test: temporary_worktree links a project root's ignored directories"
    commit_green: "feat: temporary_worktree symlinks ignored top-level dirs (node_modules, .venv) from the live root"

  - n: 5
    project: tddcli
    title: "a close sweep that reaches an un-baselined project probes it at the start sha and records a late_probe baseline"
    test: "tests/test_late_baseline.py::test_close_sweep_late_probes_an_unbaselined_project_at_the_start_sha"
    files: ["src/tddcli/machine.py"]
    modifies_tests:
      - "tests/test_baseline_integrity.py::test_close_sweep_with_unbaselined_failures_directs_resolve_blocker"
      - "tests/test_baseline_integrity.py::test_accept_failures_inserts_baseline_row_for_unbaselined_project"
      - "tests/test_baseline_integrity.py::test_sweep_reports_unbaselined_failures_separately"
    commit_red: "test: an un-baselined project is late-probed at the start sha"
    commit_green: "feat: late baseline — probe an un-baselined project at run.start_sha, source late_probe"

  - n: 6
    project: tddcli
    pin_cycle: true
    title: "a failure that also fails at the start sha is baseline: the cycle closes"
    test: "tests/test_late_baseline.py::test_a_failure_present_at_the_start_sha_lets_the_cycle_close"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: pin — a start-sha failure in a late-baselined project is subtracted"

  - n: 7
    project: tddcli
    pin_cycle: true
    title: "a failure that passes at the start sha is a regression, even in a late-baselined project"
    test: "tests/test_late_baseline.py::test_a_failure_absent_at_the_start_sha_is_a_regression_in_a_late_baselined_project"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: pin — a run-introduced failure in a late-baselined project replies fix_regression"

  - n: 8
    project: tddcli
    title: "an unobservable start-sha probe blocks with no baseline row and no accept-failures advice"
    test: "tests/test_late_baseline.py::test_an_unobservable_late_probe_blocks_without_a_baseline_row"
    files: ["src/tddcli/machine.py", "src/tddcli/advance.py"]
    commit_red: "test: an unobservable late probe blocks without a row"
    commit_green: "fix: unobservable late probe → no_baseline_for_project with the reason; accept-failures no longer advised"

  - n: 9
    project: tddcli
    title: "accept-failures refuses a candidate that passes at the start sha"
    test: "tests/test_late_baseline.py::test_accept_failures_refuses_a_test_that_passes_at_the_start_sha"
    files: ["src/tddcli/cli.py"]
    modifies_tests:
      - "tests/test_baseline_integrity.py::test_unblocking_can_accept_the_failures_into_the_baseline"
      - "tests/test_baseline_integrity.py::test_stale_reused_baseline_recovers_via_accept_failures"
    commit_red: "test: accept-failures refuses a test that passes at the start sha"
    commit_green: "fix: accept-failures gates each candidate on failing at run.start_sha"

  - n: 10
    project: tddcli
    pin_cycle: true
    title: "accept-failures still accepts a candidate that fails at the start sha"
    test: "tests/test_late_baseline.py::test_accept_failures_accepts_a_test_that_fails_at_the_start_sha"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: pin — a start-sha failure the baseline missed is still accepted"

  - n: 11
    project: tddcli
    title: "baseline_amended records a per-test verdict and the start sha"
    test: "tests/test_late_baseline.py::test_baseline_amended_records_a_verdict_per_test"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: baseline_amended carries accepted/refused verdicts per test"
    commit_green: "feat: baseline_amended detail — {project: {start_sha, accepted, refused}}"

  - n: 12
    project: tddcli
    title: "accept-failures refuses every candidate of an unobserved project and inserts no row"
    test: "tests/test_late_baseline.py::test_accept_failures_refuses_an_unobserved_project_and_inserts_no_row"
    files: ["src/tddcli/cli.py"]
    modifies_tests:
      - "tests/test_baseline_integrity.py::test_accept_failures_inserts_baseline_row_for_unbaselined_project"
    commit_red: "test: accept-failures refuses an unobserved project"
    commit_green: "fix: accept-failures never creates a baseline row; unobserved candidates are refused"

  - n: 13
    project: tddcli
    title: "the friction log lists amended-baseline verdicts under Human interventions"
    test: "tests/test_late_baseline.py::test_friction_log_lists_amended_baseline_verdicts_under_human_interventions"
    files: ["src/tddcli/render.py"]
    commit_red: "test: friction log renders per-test accept/refuse verdicts"
    commit_green: "feat: friction log — amended baselines with per-test verdicts under Human interventions"

  - n: 14
    project: tddcli
    title: "the friction log names late baselines in the run header and keeps them out of the start line"
    test: "tests/test_late_baseline.py::test_friction_log_names_late_baselines_in_the_run_header"
    files: ["src/tddcli/render.py"]
    commit_red: "test: friction log header names late baselines"
    commit_green: "feat: friction log — Late baselines header line; start line excludes late_probe rows"
ancillary_files:
  - "docs/PRD.md"
  - "README.md"
  - "CHANGELOG.md"
---

# Issue #108 — late baselines must be probed at the run's start sha

https://github.com/geuben/tdd-cli/issues/108
Task file: `tasks/issue-108-late-baseline-start-sha.md`
Companion: #107 (shipped in PR #111) — not touched here.

## Context

A baseline means "what failed before this run touched anything" (PRD R9.6). `run start` honours
that by probing before cycle 1. Two later paths do not:

- **R9.5d, `no_baseline_for_project`.** When a close sweep reaches a project the plan's reachable
  set did not predict, `Engine.sweep` (`src/tddcli/machine.py`) reports its failures as
  `unbaselined`, and `_handle_refactor` (`src/tddcli/advance.py`) tells the agent, verbatim, to
  file the blocker and run `resume --unblock --accept-failures`.
- **R9.5b, `--accept-failures`.** `_accept_failures_into_baseline` (`src/tddcli/cli.py`) copies the
  last close sweep's `other_failures` into the baseline row — the failure set of the tree the run
  has been editing for N cycles, not the tree it started on. Nothing checks the "baseline missed
  it" premise, and the "human-only" guard is nominal: the agent is handed the exact command.

The consuming run in the issue did exactly that: a registry test the run itself broke was folded
into the baseline, subtracted from every later sweep, and the run closed "delivered" with CI red.

**The issue's one factual error, found in Phase B:** the `run` row does *not* carry the start sha
today (`ledger.py` `SCHEMA`, `run` table: `id … config_sha`; probe-confirmed by reading a live row's
keys). Cycles 1–2 add it. Runs that predate the column have `start_sha = NULL` and are treated as
unobservable (decision 4).

Probed empirically on `main` before drafting (throwaway `tests/test_zz_probe.py`, deleted, tree
clean):

- `repo_schema_other` with `svc` **green** at the start sha, broken during the run, plus a touch of
  `other/generated.json`: `advance` → `resolve_blocker`, `result.unbaselined = {svc:
  [svc::tests/test_svc.py::test_svc_ok]}` — the regression is unattributable today.
- `repo_schema_other` with `svc/tests/test_svc.py` **uncollectable** at the start sha (`import
  nope_missing`) and rewritten to a plain failing test during the run: `advance` →
  `resolve_blocker`; the detail quotes `resume --unblock --accept-failures`.
- `git worktree add --detach <tmp> <start_sha>` from the fixture repo: exit 0, `HEAD` in the temp
  tree equals the sha; `PytestAdapter.run(None)`/`.collect()` built against the temp path run
  there (collect error reported as `failed_files`, `tests=set()`, `verdict.failed=[]`); `git
  worktree remove --force` exits 0 and the live tree's dirty set is unchanged.
- `git ls-files -o -i --exclude-standard --directory -- svc` lists `svc/.venv/`,
  `svc/node_modules/`, **and nested** `svc/tests/__pycache__/`; symlinking the listed directories
  into the temp worktree makes `node_modules/pkg/index.js` readable there, the pytest run at the
  start sha observes `svc::tests/test_svc.py::test_svc_fails`, and the live tree stays clean.
- Doctoring `baseline.failing` to `[]` **before** the RED phase makes RED itself reply
  `fix_regression` (`run_projects` subtracts the baseline in every phase), so the accept-failures
  fixtures doctor the row only after reaching `AWAITING_REFACTOR`.
- `log render` on a run with an intervention prints `- Human interventions: 1` followed by
  `  - <at>: <note>`; `baseline_amended` today is `{"backend": [<ids>]}`.

The suite is green on `main` (491 passed). `tdd` on PATH is the editable install of this tree;
the referee is `uvx --from tdd-cli==0.10.1 tdd` (note: `uvx tdd-cli@0.10.1` fails — the
executable is `tdd`, not `tdd-cli`).

## Design decisions (locked)

1. **`run.start_sha` is a new column, captured as `gitutil.head(worktree)` in `cmd_run_start`
   before the probe** — *evidence*: no such column exists; the tree is clean or `--allow-dirty`
   at that point, so HEAD cannot move between capture and probe. Schema v9 → v10,
   `MIGRATIONS[9] = "ALTER TABLE run ADD COLUMN start_sha TEXT;"` (nullable: old runs have none).
2. **Probe tree = temporary detached worktree at `start_sha`, with the project root's ignored
   top-level directories symlinked in from the live root** — *user decision, 2026-09-07.*
   `gitutil.temporary_worktree(worktree, sha, link_ignored_under=()) ` is a context manager: `git
   worktree add --detach <tempfile.mkdtemp(prefix="tdd-probe-")> <sha>`, yield the path, `git
   worktree remove --force <path>` in `finally` (plus `shutil.rmtree(ignore_errors=True)` if the
   path survives). For each root in `link_ignored_under`, run `git ls-files -o -i
   --exclude-standard --directory -- <root>` in the *live* worktree and symlink only entries
   whose path relative to `<root>` has **exactly one segment** (`svc/node_modules/` yes,
   `svc/tests/__pycache__/` no — probe-verified the listing includes nested ones) and that do not
   already exist in the temp tree. Symlinks are best-effort: an `OSError` on one link is skipped,
   never fatal. The live tree is never written.
3. **The late probe lives on `Engine` and is shared by both consumers** — *evidence*: `sweep`
   (machine.py) and `cmd_resume` (cli.py, which already builds an `Engine` via `_engine`) both
   need "run this project's suite at the start sha". `Engine.probe_at_start_sha(name) ->
   StartShaProbe` where `StartShaProbe(observed: bool, reason: str, failing: set[str],
   collected: int, start_sha: str | None)`. It builds `adapters.build(project, tmp)` inside
   `temporary_worktree(self.worktree, self.run["start_sha"], link_ignored_under=[project.root])`
   and runs `run(None)` then `collect()`. It runs the **whole suite once per project**, never
   per test — `Adapter.run(target)` runs the full suite anyway and only changes what is reported.
4. **Unobservable = strict** — *user decision, 2026-09-07.* The probe is `observed=False` when
   any of: `run.start_sha` is NULL (reason `run predates start_sha; restart the run`),
   `gitutil.GitError` creating the worktree, `verdict.error` set, R9.5a "nothing collected"
   (`not collection.tests and collection.failed_files`), or R9.5a "collected but ran nothing"
   (`collection.tests and not verdict.passed and not verdict.failed`). Consequences: **no
   baseline row is written**; `sweep` keeps the project in `unbaselined` and adds
   `SweepOutcome.unobserved: dict[str, str]` (project → reason); the reply stays
   `resolve_blocker` / `no_baseline_for_project` but the detail quotes the reason, says a human
   must make the suite observable at the start sha (or restart the run) and resume with
   `--unblock --note`, and **no longer mentions `--accept-failures`**; `--accept-failures` refuses
   every candidate of that project with verdict `unobserved at start sha: <reason>`.
5. **Observed late probe** — *evidence + issue's "Expected"*. `sweep` calls the probe for every
   project with no baseline row, **regardless of the HEAD verdict** (the row is needed by every
   later sweep, and "observed green at HEAD" is not an observation of the start sha). On
   `observed`: insert `baseline(run_id, project, failing=sorted(probe.failing), source=
   "late_probe")`, insert the matching `collection_snapshot`, emit integrity event
   `baseline_late_probe` on the **cycle** (`cycle_id = cycle_row["id"]`, so the existing per-cycle
   event renderer lists it) with detail `{"project", "start_sha", "failing": [...], "collected":
   n}`, and feed the failing set into the *current* sweep's `baselines[name]` so subtraction
   happens in the same sweep. A failure at HEAD that is in the late row is baseline; one that is
   not is an ordinary regression → `fix_regression` via the existing `outcome.failures` branch.
   Unobserved emits `baseline_late_probe_unobserved` with `{"project", "start_sha", "reason"}`.
6. **`--accept-failures` gates per test on the start sha and never creates a row** — *user
   decision (start-sha gate only; the ≥2-of-N HEAD re-run rule is cut), 2026-09-07.*
   `_accept_failures_into_baseline(engine)` (signature changes from `(ledger, run_id)`; `cmd_resume`
   builds the engine before calling it): for each project in the last close sweep's failure set
   **that has a baseline row**, probe once at the start sha; a candidate absent from the row is
   `accepted` with verdict `fails at start sha` if it is in `probe.failing`, else `refused` with
   `passes at start sha`; if the probe is unobserved every candidate is `refused` with
   `unobserved at start sha: <reason>`. A project with **no row** is also probed and every
   candidate refused as unobserved (the row-less state only survives cycle 5 when the probe
   was unobservable) — accept-failures never inserts a row. The `resume` envelope gains
   `result.refused_from_baseline: {project: [ids]}` beside the existing `accepted_into_baseline`.
   The `baseline_amended` event is emitted whenever there was at least one candidate and its
   detail becomes `{project: {"start_sha": <sha>, "accepted": {id: verdict}, "refused": {id:
   verdict}}}`.
7. **Rendering** — *user decision, 2026-09-07.* Under `## Plan fidelity` → `- Human
   interventions:`, after the intervention lines, each `baseline_amended` event renders as
   `  - baseline amended (start sha <sha7>):` followed by one line per test:
   ``    - accepted: `<id>` (<verdict>)`` / ``    - refused: `<id>` (<verdict>)``. The run header
   gains `- Late baselines: <project>=<n failing> (at <sha7>)` per `baseline_late_probe` event,
   `<project>: unobserved at <sha7> (<reason>)` per `baseline_late_probe_unobserved`, or is
   omitted when there are none; `- Baseline failures at start:` counts only rows whose `source`
   is not `late_probe`. `Ledger.baselines()` is unchanged (subtraction still uses every row);
   the renderer reads `SELECT project, failing, source FROM baseline` itself.
8. **Blocker kinds are unchanged** — *evidence*. `no_baseline_for_project` keeps its meaning
   ("reached un-baselined and the tool could not baseline it itself"); `pre_existing_failure`
   remains the kind filed before `--accept-failures`. `BLOCKER_KINDS` is not edited.
9. **No invocation row for a start-sha probe** — *evidence*. `run start` writes none for its
   probe either; `_accept_failures_into_baseline` selects `MAX(id) … phase_at = 'CLOSE_SWEEP'`
   per project, so a probe row would need excluding anyway. The events carry the record.

## Deliberate scope cuts (do not build)

- **The "fails ≥2 of N re-runs at HEAD" flake gate.** Premise: a flake that fails only sometimes
  passes on the next close sweep, so the run unsticks by itself; a test that fails consistently
  at HEAD and passes at the start sha is a regression by definition. Re-evaluation trigger: if
  cycle 9's fixture (a test broken during the run) cannot be refused without also refusing cycle
  10's fixture (a test failing at the start sha), stop and file `plan_defect` — do not add a
  re-run loop to get green. Tracking: leave a note in the PR body; open an issue only if a real
  run hits it.
- **`--allow-dirty` runs probe HEAD-at-start, not HEAD plus the pre-existing dirty changes.**
  Premise: `preexisting_dirty` paths are excluded from authorship forever (R9.21) and cannot be
  reconstructed in a temp worktree without copying uncommitted content; the late probe records
  `start_sha` and a reviewer can see `allow_dirty = 1` on the run. Not built: no event, no flag.
- **No per-project `probe_setup` command in `tdd.toml`.** Premise (user decision): symlinked
  ignored directories cover pytest/vitest; a project whose deps cannot be linked surfaces as
  `unobserved` with the R9.5a reason, which is the honest state. Trigger: if the executor's own
  dogfood run of this plan hits `unobserved` on `tddcli`, that is a `tooling` blocker, not a
  reason to add config.
- **`baseline_late_probe` is not added to the stderr heartbeat table (R8.4).** Premise: heartbeats
  exist for long-running `run start`; the late probe already sits inside an `advance` that the
  caller is waiting on. A `project_completed` heartbeat with `phase="LATE_PROBE"` is emitted
  through the existing `heartbeat()` call so a slow probe is not silent — that is the only stderr
  change and needs no new event name.
- **`tdd doctor` does not inspect `start_sha`.** Nothing to check before a run exists.
- **The consuming project's pre-PR skill** (issue "Downstream") is outside this repo.

## Cycles

All test ids are relative to the `tddcli` project root (`.`). New tests live in
`tests/test_late_baseline.py` (created in cycle 1 — a **new test file needs no stub**: the tool
collects it as the RED test; do not declare it in `stub_expected`). It imports `git`, `run_cli`,
`run_cli_text`, `write_plan` from `conftest` and `BACKEND_ONLY_PLAN`, `PLAN`, `TEST_ADD`,
`reach_refactor` from `test_baseline_integrity` (the probe imported them the same way). Two
helpers are written in cycle 1 at the top of the new file and reused verbatim:

```python
def _drive_to_close(repo):
    """Register BACKEND_ONLY_PLAN, start, RED, GREEN; leave cycle 1 in AWAITING_REFACTOR."""
    plan = write_plan(repo, BACKEND_ONLY_PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    raise NotImplementedError\n")
    run_cli(repo, "advance")
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    return out

def _pull_svc_into_the_sweep(repo):
    """Touching other/'s root pulls artifact `schema`'s consumer svc into the close sweep."""
    (repo / "other" / "generated.json").write_text("{}")
```

Fixtures (from `tests/conftest.py`): `repo` (one pytest project `backend`), `repo_schema_other`
(`backend` + `svc` + `other`; artifact `schema` produced by `other`, consumed by `svc`; `svc` has a
pre-committed failing `test_svc_fails`; a `backend`-only plan leaves `svc` un-baselined).

### Cycle 1 — `run start` records the start sha

**Behaviour.** After `run start`, the run row's `start_sha` equals the worktree's HEAD at that
moment.

**Test.** `test_run_start_records_the_start_sha_on_the_run_row(repo)`: `sha =
gitutil.head(repo)`; `write_plan(repo, PLAN)` — note `write_plan` **commits**, so read `sha`
*after* it; register; `run start`; `row = ledger.one("SELECT * FROM run WHERE id = ?", …)`.
Single assertion: `dict(row).get("start_sha") == sha`.

**Production target.** `ledger.py` `SCHEMA`, `run` table: add `start_sha TEXT` (nullable) with the
comment `-- HEAD at run start; late probes and accept-failures run suites here`. `cli.py`
`cmd_run_start`: `start_sha = gitutil.head(worktree)` next to the `dirty` computation, passed as
`start_sha=start_sha` to `ledger.insert("run", …)`. Minimal green may leave `SCHEMA_VERSION` at 9
(fresh test ledgers get the column from `CREATE TABLE`); cycle 2 covers existing ledgers. Add the
field to the PRD's `### Run` table (`docs/PRD.md` §5) in this cycle: `start_sha` — HEAD at run
start; the tree every late baseline probe and `--accept-failures` verdict is taken from.

**EXPECTED FAILURE:** fails with `AssertionError: assert None == '<sha>'` (probe-verified: a live
run row has keys `id … config_sha` and no `start_sha`).

### Cycle 2 — migrate existing ledgers

**Behaviour.** A ledger stored at schema v9 is upgraded in place on open and gains
`run.start_sha`.

**Test.** `tests/test_release_surface.py::test_run_gains_start_sha_column(tmp_path,
ledger_home)`, mirroring `test_artifact_check_gains_regenerate_failed_column` in that file: open a
fresh ledger, `UPDATE meta SET value = '9'`, `ALTER TABLE run DROP COLUMN start_sha`, close, reopen,
`PRAGMA table_info(run)`. Single assertion: `"start_sha" in cols2` (keep the fresh-ledger
pre-check as in the sibling test; it is not the assertion under test).

**Production target.** `ledger.py`: `SCHEMA_VERSION = 10`; `MIGRATIONS[9] = "ALTER TABLE run ADD
COLUMN start_sha TEXT;"` with the usual `# v9 -> v10 …` comment line.

**EXPECTED FAILURE:** fails with `AssertionError: assert 'start_sha' in {...}` — with
`SCHEMA_VERSION` still 9 the migration loop does not run and `CREATE TABLE IF NOT EXISTS` does not
add columns. If cycle 1's green already bumped the version, this passes on arrival: record it as
the tool directs; the sensitivity check will show the migration line is load-bearing.

### Cycle 3 — `gitutil.temporary_worktree`

**Behaviour.** Inside the context, the yielded path is a checkout of the requested sha; after
the context, the path no longer exists.

**Test.** `test_temporary_worktree_checks_out_the_sha_and_is_removed_on_exit(repo)`: `first =
gitutil.head(repo)`; make and commit a second change; `with gitutil.temporary_worktree(repo,
first) as tmp: inside = gitutil.head(tmp)`; single assertion: `(inside, tmp.exists()) == (first,
False)`.

**Stub (`stub_expected`).** `src/tddcli/gitutil.py` gains the signature stub
`def temporary_worktree(worktree: Path, sha: str, link_ignored_under: Sequence[str] = ()) ->
Iterator[Path]: raise NotImplementedError` decorated `@contextlib.contextmanager` — the file exists
at HEAD, so it must be declared or the edit is recorded as implementation-during-RED.

**Production target.** `gitutil.py` `temporary_worktree` per decision 2 (the `link_ignored_under`
parameter is accepted and ignored until cycle 4 — minimal green).

**EXPECTED FAILURE:** fails with `NotImplementedError` raised from the stub (the function exists
and is callable; the test reaches the `with`).

### Cycle 4 — link ignored directories

**Behaviour.** With `link_ignored_under=["backend"]`, a git-ignored directory directly under
`backend/` in the live tree is reachable at the same relative path in the temporary worktree.

**Test.** `test_temporary_worktree_links_ignored_directories_under_the_project_root(repo)`:
append `node_modules/\n` to `.gitignore`, `git add -A && git commit`; `sha = gitutil.head(repo)`;
create `backend/node_modules/pkg/index.js` with content `x`; `with
gitutil.temporary_worktree(repo, sha, link_ignored_under=["backend"]) as tmp: seen = (tmp /
"backend/node_modules/pkg/index.js").read_text() if (tmp /
"backend/node_modules/pkg/index.js").exists() else None`. Single assertion: `seen == "x"`.

**Production target.** `gitutil.py` `temporary_worktree`: the listing + one-segment filter +
`os.symlink` loop from decision 2.

**EXPECTED FAILURE:** fails with `AssertionError: assert None == 'x'` (cycle 3's green ignores
the parameter, so the temp tree has no `node_modules`).

### Cycle 5 — late probe at the start sha

**Behaviour.** When a close sweep reaches a project with no baseline row, the tool runs that
project's suite at `run.start_sha` and records the result as a `late_probe` baseline row plus a
`baseline_late_probe` event on the cycle.

**Test.** `test_close_sweep_late_probes_an_unbaselined_project_at_the_start_sha(repo_schema_other)`:
`repo = repo_schema_other`; `_drive_to_close(repo)`; `sha = ledger row's start_sha` (or
`gitutil.head(repo)` read **before** `_drive_to_close` — `write_plan` commits, so read it after
writing the plan; simplest: `start_sha = ledger.one("SELECT start_sha FROM run WHERE id = ?")`);
`_pull_svc_into_the_sweep(repo)`; `run_cli(repo, "advance")`; read `row = SELECT source, failing
FROM baseline WHERE run_id = ? AND project = 'svc'` and `event = SELECT detail FROM integrity_event
WHERE run_id = ? AND kind = 'baseline_late_probe'`; `detail = json.loads(event["detail"]) if event
else {}`. Single assertion:
`(row["source"] if row else None, json.loads(row["failing"]) if row else None,
detail.get("start_sha")) == ("late_probe", ["svc::tests/test_svc.py::test_svc_fails"], start_sha)`.

**Production target.** `machine.py`: `StartShaProbe` dataclass; `Engine.probe_at_start_sha(name)`
(decisions 3, 4 — **all five unobserved conditions, including NULL `start_sha`, must be handled
here**, because the rewritten `test_sweep_reports_unbaselined_failures_separately` below sets
`start_sha` to NULL and expects `unbaselined`); `Engine.sweep`: in the `if name not in baselines:`
branch call the probe **before** classifying; on `observed` insert the row + snapshot, emit the
event, set `baselines[name] = probe.failing` and fall through to the normal subtraction; on
unobserved keep today's `unbaselined[name] = sorted(verdict.failed)` and record the reason in
`SweepOutcome.unobserved[name]`. Emit `heartbeat(event="project_completed", project=name,
phase="LATE_PROBE", elapsed_s=…)` around the probe.

**Test-side blast radius (declared in `modifies_tests`; rewrite, never delete):**

- `tests/test_baseline_integrity.py::reach_unbaselined_blocker` (helper) and
  `test_close_sweep_with_unbaselined_failures_directs_resolve_blocker`: with `svc`'s failure
  present at the start sha the sweep no longer blocks. Convert the helper to the **unobservable**
  fixture: before `write_plan`, write `svc/tests/test_svc.py` as `import nope_missing\n\ndef
  test_svc_fails():\n    assert False\n` and commit; after GREEN, rewrite it to `def
  test_svc_fails():\n    assert False\n` (an authored change outside the cycle's project — fires
  `undeclared_file_touched`, which the fixture tolerates today) and touch `other/generated.json`.
  The helper's `assert verb == "resolve_blocker"` then holds. In the test, drop the assertion
  that the detail contains `resume --unblock --accept-failures` (cycle 8 asserts its absence);
  keep `"no_baseline_for_project" in detail`.
- `test_accept_failures_inserts_baseline_row_for_unbaselined_project`: consumes the helper;
  with the unobservable fixture and today's `_accept_failures_into_baseline` it still passes
  (the row is inserted from the HEAD sweep). Leave its body alone in this cycle; cycle 12
  rewrites it.
- `test_sweep_reports_unbaselined_failures_separately`: deletes `svc`'s row and calls
  `engine.sweep` directly; `svc`'s smoke failure exists at the start sha, so after this cycle it is
  late-probed and subtracted. Rewrite: additionally `UPDATE run SET start_sha = NULL WHERE id = ?`
  before building the engine (a run that predates the column), keep every assertion, and add the
  docstring line "a run without a start sha cannot be late-probed; its failures stay
  unattributable". This is the only test of the NULL-`start_sha` path.

**EXPECTED FAILURE:** fails with `AssertionError: assert (None, None, None) == ('late_probe',
['svc::tests/test_svc.py::test_svc_fails'], '<sha>')` (probe-verified: today the sweep blocks and
writes no row).

### Cycle 6 — pin: a start-sha failure is baseline *(pin_cycle)*

**Behaviour.** In the cycle-5 scenario the advance that ran the late probe closes the cycle.

**Test.** `test_a_failure_present_at_the_start_sha_lets_the_cycle_close(repo_schema_other)`:
same setup as cycle 5; capture the closing `advance`. Single assertion:
`out["next_action"]["verb"] == "complete"`.

**Why a pin.** Cycle 5's production target feeds the late row into the same sweep; this locks
that. Must pass on arrival. If it fails, cycle 5 inserted the row but classified against the
stale `baselines` dict — fix `sweep` under this cycle's refactor phase; do not weaken the test.

### Cycle 7 — pin: a run-introduced failure is a regression *(pin_cycle)*

**Behaviour.** A late-baselined project whose failing test **passes** at the start sha replies
`fix_regression` naming the test.

**Test.** `test_a_failure_absent_at_the_start_sha_is_a_regression_in_a_late_baselined_project
(repo_schema_other)`: before `_drive_to_close`, write `svc/tests/test_svc.py` as `def
test_svc_ok():\n    assert True\n` and commit (`svc` green at the start sha); after GREEN, rewrite
it to `assert False`; `_pull_svc_into_the_sweep`; `advance`. Single assertion:
`(out["next_action"]["verb"], out["result"].get("failures")) == ("fix_regression",
["svc::tests/test_svc.py::test_svc_ok"])`.

**Why a pin.** The late row for `svc` is empty, so the existing `failures` branch in
`_handle_refactor` produces this reply without new code. Probe-verified that today the same
setup replies `resolve_blocker` with the test under `unbaselined`; after cycle 5 it must be a
regression. Must pass on arrival.

### Cycle 8 — an unobservable probe blocks, honestly

**Behaviour.** When the start-sha probe cannot observe the project, the sweep still blocks with
`no_baseline_for_project`, writes no baseline row, records `baseline_late_probe_unobserved`,
and the reply no longer points at `--accept-failures`.

**Test.** `test_an_unobservable_late_probe_blocks_without_a_baseline_row(repo_schema_other)`:
before `_drive_to_close`, write `svc/tests/test_svc.py` as `import nope_missing\n\ndef
test_svc_fails():\n    assert False\n` and commit; after GREEN rewrite it to `def
test_svc_fails():\n    assert False\n`; `_pull_svc_into_the_sweep`; `advance`; read the `svc`
baseline row and the `baseline_late_probe_unobserved` event. Single assertion:
`(out["next_action"]["verb"], row is None, "--accept-failures" in out["next_action"]["detail"],
event is not None) == ("resolve_blocker", True, False, True)`.

**Production target.** `machine.py` `sweep`: emit `baseline_late_probe_unobserved`
(`{"project", "start_sha", "reason"}`) on the cycle in the unobserved branch. `advance.py`
`_handle_refactor`, the `outcome.unbaselined` branch: new detail — "Close sweep found failures
in un-baselined project(s): <names>. The tool tried to baseline them at the run's start sha
and could not observe: <project>: <reason>. These are unattributable. File: `tdd blocker --kind
no_baseline_for_project --detail '...'`. A human must make the suite observable at the start sha
(dependencies present, or restart the run so it is baselined up front) and then `tdd resume
--unblock --note ...`; `--accept-failures` refuses unobserved tests." Pass
`late_probe_unobserved=outcome.unobserved` in the result. Also in this cycle: `docs/PRD.md`
R9.5d rewritten to describe the late probe (observed → `late_probe` row, subtraction as if
baselined up front; unobserved → blocker, no row, no accept path) and R9.6 gains the sentence
"A baseline row is only ever captured from `run.start_sha`, never from the current tree";
IntegrityEvent list (§5) gains `baseline_late_probe`, `baseline_late_probe_unobserved`;
`README.md` "When a sweep reaches an un-baselined project (R9.5d)" rewritten accordingly (drop
the two-command recovery snippet; describe the probe, the `unobserved` outcome, and the
`baseline_late_probe` line in the friction log).

**EXPECTED FAILURE:** fails with `AssertionError: assert ('resolve_blocker', True, True, False)
== ('resolve_blocker', True, False, True)` (after cycle 5 the unobservable path blocks without a
row but keeps today's wording and emits no event).

### Cycle 9 — `--accept-failures` refuses what passes at the start sha

**Behaviour.** A candidate that passes at the start sha is refused: the baseline row is left
unchanged and the `resume` envelope lists it under `refused_from_baseline`.

**Test.** `test_accept_failures_refuses_a_test_that_passes_at_the_start_sha(repo)`:
`reach_refactor(repo)`; write `backend/tests/test_smoke.py` as `def test_smoke():\n    assert
False\n`; `advance` (→ `fix_regression`); `blocker --kind pre_existing_failure --detail x`;
`resumed = resume --unblock --note n --accept-failures`; read the `backend` baseline row. Single
assertion: `(json.loads(row["failing"]), resumed["result"].get("refused_from_baseline")) == ([],
{"backend": ["backend::tests/test_smoke.py::test_smoke"]})`.

**Production target.** `cli.py`: `_accept_failures_into_baseline(engine)` per decision 6 —
probe each project once via `engine.probe_at_start_sha`, split candidates into
accepted/refused, amend the row only with `accepted`; `cmd_resume` builds `engine` before the
call and copies `refused_from_baseline` into `result`. Minimal green for *this* test: the
"has a row" branch only; the event shape is cycle 11 and the row-less branch is cycle 12.

**Test-side blast radius (declared, rewrite in place):**

- `test_unblocking_can_accept_the_failures_into_the_baseline`: its scenario (smoke broken
  during the run, green at the start sha) is now a refusal. Rewrite to assert `resumed["result"]
  .get("accepted_into_baseline") is None` and that the following `advance` still replies
  `fix_regression`; rename its docstring to say the escape hatch cannot launder a
  run-introduced failure. Keep the test name.
- `test_stale_reused_baseline_recovers_via_accept_failures`: same shape (smoke broken during
  the run under a reused baseline). Rewrite the tail: the resume result carries
  `refused_from_baseline == {"backend": [smoke id]}` and the next `advance` is `fix_regression`;
  update the docstring — a *drifted* reused baseline is recoverable only for tests that fail at
  the start sha (cycle 10 proves that path). Keep the test name.

**EXPECTED FAILURE:** fails with `AssertionError: assert (['backend::tests/test_smoke.py::
test_smoke'], None) == ([], {'backend': [...]})` (today the test is folded and nothing is refused).

### Cycle 10 — pin: what fails at the start sha is still accepted *(pin_cycle)*

**Behaviour.** A candidate that the baseline missed but that fails at the start sha is accepted.

**Test.** `test_accept_failures_accepts_a_test_that_fails_at_the_start_sha(repo)`: write
`backend/tests/test_flaky.py` as `def test_flaky():\n    assert False\n`, commit; `reach_refactor
(repo)` (the baseline holds `test_flaky`, so RED/GREEN are unaffected); then simulate the miss:
`UPDATE baseline SET failing = '[]' WHERE run_id = ? AND project = 'backend'`; `advance` (→
`fix_regression`); `blocker --kind pre_existing_failure`; `resume --unblock --note n
--accept-failures`. Single assertion: `resumed["result"].get("accepted_into_baseline") ==
{"backend": ["backend::tests/test_flaky.py::test_flaky"]}`.

**Why a pin.** Cycle 9's gate accepts exactly this; the pin guards against a green that refuses
everything. Probe-verified that doctoring the row **before** RED trips `fix_regression` in the
RED phase — the order above is mandatory. Must pass on arrival.

### Cycle 11 — `baseline_amended` carries verdicts

**Behaviour.** The `baseline_amended` event detail names, per project, the start sha and a
verdict per accepted and per refused test.

**Test.** `test_baseline_amended_records_a_verdict_per_test(repo)`: cycle-10 setup **plus**
breaking `test_smoke` after the row is doctored (one accepted, one refused candidate in one
resume); read the event; `start_sha` from the run row. Single assertion: `json.loads(event
["detail"]) == {"backend": {"start_sha": start_sha, "accepted": {"backend::tests/test_flaky.py::
test_flaky": "fails at start sha"}, "refused": {"backend::tests/test_smoke.py::test_smoke":
"passes at start sha"}}}`.

**Production target.** `cli.py` `_accept_failures_into_baseline`: build the per-project verdict
dict and emit it as the event detail; emit whenever there was at least one candidate.

**EXPECTED FAILURE:** fails with `AssertionError: assert {'backend': ['…test_flaky']} == {'backend':
{...}}` (cycle 9's minimal green keeps today's `{project: [accepted ids]}` shape).

### Cycle 12 — `--accept-failures` never creates a row

**Behaviour.** For a project with no baseline row (the unobservable case), every candidate is
refused and no row is inserted.

**Test.** `test_accept_failures_refuses_an_unobserved_project_and_inserts_no_row
(repo_schema_other)`: cycle-8 setup through the blocking `advance`; `blocker --kind
no_baseline_for_project --detail x`; `resume --unblock --note n --accept-failures`; read the `svc`
row. Single assertion: `(row is None, resumed["result"].get("refused_from_baseline")) == (True,
{"svc": ["svc::tests/test_svc.py::test_svc_fails"]})`.

**Production target.** `cli.py` `_accept_failures_into_baseline`, the `row is None` branch:
probe, refuse all with `unobserved at start sha: <reason>` (or, if the probe unexpectedly
observes, still refuse — accept-failures never inserts; the message says to re-advance so the
sweep late-probes it), never `ledger.insert("baseline", …)`. Also in this cycle: `docs/PRD.md`
R9.5b rewritten (per-test start-sha gate, verdict strings, `refused_from_baseline`, no row
insertion; delete the sentence "If a close sweep reached a project that was never baselined,
`--accept-failures` inserts a fresh baseline row"), R9.5e's last sentence ("always recoverable
via …") qualified to "for tests that fail at the start sha"; `README.md` R9.5e paragraph and the
`--accept-failures` prose updated to match; `resume --accept-failures` argparse `help` text in
`cli.py` updated.

**Test-side blast radius (declared, rewrite in place):**
`test_accept_failures_inserts_baseline_row_for_unbaselined_project` asserts the inverse of this
cycle. Rewrite it to assert `row is None` and that the `baseline_amended` event's `svc` entry has
an empty `accepted` map; rename **the docstring**, keep the test name (the name is now a
historical misnomer; renaming it is a `test_removed`-shaped change for no gain).

**EXPECTED FAILURE:** fails with `AssertionError: assert (False, None) == (True, {'svc': [...]})`
(today the row-less branch inserts the HEAD failures verbatim).

### Cycle 13 — render amended verdicts

**Behaviour.** `tdd log render` lists each `baseline_amended` event under Human interventions
with one `accepted:`/`refused:` line per test.

**Test.** `test_friction_log_lists_amended_baseline_verdicts_under_human_interventions(repo)`:
cycle-11 setup; `run_cli(repo, "log", "render", "--out", str(repo / "friction.md"))`; `text =
(repo / "friction.md").read_text()`. Single assertion:
`("    - accepted: `backend::tests/test_flaky.py::test_flaky` (fails at start sha)" in text,
"    - refused: `backend::tests/test_smoke.py::test_smoke` (passes at start sha)" in text) ==
(True, True)`.

**Production target.** `render.py` `friction_log`, after the interventions loop: read
`baseline_amended` events for the run, parse, and emit the lines from decision 7.

**EXPECTED FAILURE:** fails with `AssertionError: assert (False, False) == (True, True)`
(probe-verified: only `  - <at>: <note>` renders today).

### Cycle 14 — render late baselines in the header

**Behaviour.** The run header names late baselines with their start sha, and the "Baseline
failures at start" line counts only rows captured at run start.

**Test.** `test_friction_log_names_late_baselines_in_the_run_header(repo_schema_other)`:
cycle-5 setup (the run closes); render; `sha7 = start_sha[:7]`. Single assertion:
`("- Baseline failures at start: backend=0" in text, f"- Late baselines: svc=1 (at {sha7})" in
text) == (True, True)`.

**Production target.** `render.py` `friction_log` header per decision 7. Also in this cycle:
`CHANGELOG.md` `[Unreleased]` — **Fixed**: accept-failures gated on the start sha; un-baselined
projects late-probed at the start sha instead of folded from HEAD; **Added**: `run.start_sha`
(schema v10, `MIGRATIONS[9]`), `gitutil.temporary_worktree`, `baseline_late_probe` /
`baseline_late_probe_unobserved` events, `resume` result `refused_from_baseline`, new
`baseline_amended` detail shape, friction-log lines; **Changed**: the `no_baseline_for_project`
reply no longer recommends `--accept-failures`.

**EXPECTED FAILURE:** fails with `AssertionError: assert (False, False) == (True, True)` — the
start line today reads `backend=0, svc=1` (all rows) and no Late line exists.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-108-late-baseline-start-sha     # first, before anything else
    tdd doctor                                            # must report healthy: true
    tdd run start --plan tasks/issue-108-late-baseline-start-sha.md   # captures baselines, opens cycle 1

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. Expected summary
  line for `tddcli`: `491 passed` (0 baseline failures); anything else means the branch moved.
- The referee is the **released** tdd-cli (see the comment at the top of `tdd.toml`), not this
  working tree. The `tdd` on PATH is the venv's *editable* install of the tree you are editing,
  so run every `tdd` command in this plan as `uvx --from tdd-cli==0.10.1 tdd <args>` (the
  executable is `tdd`; `uvx tdd-cli@0.10.1` fails). Cycle 2 bumps the ledger schema the working
  tree writes into *test* ledgers under `TDD_LEDGER_HOME`; the referee's own ledger for this repo
  is untouched. The referee (0.10.1) has no `start_sha` and no late probe: if *its* close sweep
  ever reaches an un-baselined project it will offer `--accept-failures` — do not take it; every
  project this plan touches is `tddcli`, which is baselined.
- Verbs this plan will hit: `write_test` / `write_implementation` / `refactor_or_advance` on
  cycles 1–5, 8, 9, 11–14; `write_test` then `refactor_or_advance` on the pins (6, 7, 10), where
  the tool expects the test to pass on arrival; `run_sensitivity_check` → `tdd sensitivity
  begin|check|end` if a standard cycle's test passes on arrival (cycle 2 is the likely one);
  `annotate_cycle` — none, this plan declares no `annotation_keys`; `resolve_blocker` → `tdd
  blocker --kind --detail` with kinds `regression`, `plan_defect`, or `tooling`;
  `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason` (not expected:
  every cycle is applicable). `create_stub` should not appear: cycle 3 declares its stub; new
  test files need none.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-108-late-baseline-start-sha-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Ancillary docs are deliverables: `git diff --stat origin/main -- docs/PRD.md` must be non-empty
(§5 Run table and IntegrityEvent list, R9.5b, R9.5d, R9.5e, R9.6), `git diff --stat origin/main
-- README.md` must be non-empty (R9.5d and R9.5e sections), and `git diff --stat origin/main --
CHANGELOG.md` must be non-empty (`[Unreleased]` entries), or the PR body says which cycle
dropped them and why.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-108-late-baseline-start-sha-friction.md
    git commit -m "docs: friction log for issue-108-late-baseline-start-sha"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.
