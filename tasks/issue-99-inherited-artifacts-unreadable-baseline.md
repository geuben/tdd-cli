---
closes: 99
cycles:
  - n: 1
    project: tddcli
    pin_cycle: true
    title: "pin: run start still regenerates and commits an artifact whose producer the run cannot reach"
    test: "tests/test_artifact_regeneration.py::test_run_start_still_regenerates_an_artifact_outside_the_runs_projects"
    files: []
    commit_pin: "test: pin — run start regenerates an artifact outside the run's projects"
  - n: 2
    project: tddcli
    title: "a cycle close checks an artifact outside the run's projects only when the cycle touched its producer"
    test: "tests/test_artifact_regeneration.py::test_a_cycle_close_checks_an_outside_artifact_only_when_the_cycle_touched_its_producer"
    files: ["src/tddcli/config.py", "src/tddcli/machine.py", "src/tddcli/advance.py", "docs/PRD.md"]
    commit_red: "test: a cycle close must not check an artifact the run cannot reach"
    commit_green: "fix: scope per-cycle artifact checks to the run's reachable projects"
    commit_refactor: "refactor: tidy the per-cycle artifact scope"
  - n: 3
    project: tddcli
    title: "run start records outside stale artifacts once, as artifact_stale_inherited"
    test: "tests/test_artifact_regeneration.py::test_run_start_reports_outside_stale_artifacts_once_as_inherited"
    files: ["src/tddcli/machine.py", "docs/PRD.md"]
    commit_red: "test: run start must report inherited stale artifacts once"
    commit_green: "feat: run start records artifact_stale_inherited for artifacts outside the run"
    commit_refactor: "refactor: tidy inherited-artifact reporting"
  - n: 4
    project: tddcli
    pin_cycle: true
    title: "pin: a project with no tests is not refused when its suite writes no report"
    test: "tests/test_baseline_integrity.py::test_a_project_with_no_tests_is_not_refused_when_its_suite_writes_no_report"
    files: []
    commit_pin: "test: pin — a project with no suite yet starts even when its runner writes no report"
  - n: 5
    project: tddcli
    title: "run start refuses a baseline whose suite produced no readable report"
    test: "tests/test_baseline_integrity.py::test_run_start_refuses_a_baseline_whose_suite_produced_no_report"
    files: ["src/tddcli/cli.py", "docs/PRD.md", "README.md"]
    commit_red: "test: run start must refuse a baseline whose report could not be read"
    commit_green: "fix: run start refuses an unreadable baseline with reason baseline_unreadable"
    commit_refactor: "refactor: tidy the unreadable-baseline refusal"
  - n: 6
    project: tddcli
    title: "an unreadable baseline probe is never cached for --reuse-baselines"
    test: "tests/test_baseline_integrity.py::test_an_unreadable_baseline_is_not_cached_for_reuse"
    files: ["src/tddcli/cli.py", "docs/PRD.md"]
    commit_red: "test: a retry with --reuse-baselines must not reuse an unreadable probe"
    commit_green: "fix: never cache a baseline probe whose suite produced no readable report"
    commit_refactor: "refactor: tidy baseline caching"
  - n: 7
    project: tddcli
    title: "doctor notes a VIRTUAL_ENV that points outside every project root"
    test: "tests/test_doctor_blockers.py::test_doctor_notes_a_virtual_env_outside_every_project_root"
    files: ["src/tddcli/cli.py", "docs/PRD.md", "CHANGELOG.md"]
    commit_red: "test: doctor must note a foreign VIRTUAL_ENV"
    commit_green: "feat: doctor notes a VIRTUAL_ENV outside every project root"
    commit_refactor: "refactor: tidy the VIRTUAL_ENV notice"
---

# Inherited stale artifacts, and baselines whose report could not be read

## Context

[#99](https://github.com/geuben/tdd-cli/issues/99) reports two defects in what a run inherits
from its worktree, as opposed to what it causes.

**A. `stale_artifact` fires on every cycle of a run that cannot produce the artifact.** A plan
scoped to one JVM project recorded `stale_artifact: <generated api client>` on all 9 cycles.
Another project produces the artifact, so it was stale when the worktree branched and nothing
in the plan could clear it. `Engine.check_artifacts` (`src/tddcli/machine.py`) loops over
**every** artifact in `tdd.toml`, both at `run start` (`cycle_row` is `None`) and at every cycle
close (`advance.py::_handle_refactor`). It never asks which projects the run declares. The issue
asks for:

- staleness to be evaluated only for artifacts whose `produced_by` project (transitively) is
  in the run's project set;
- for any other artifact, staleness to be reported **once** at `run start`, as an inherited
  condition (`artifact_stale_inherited: [<name>]`), and never per cycle.

**B. A `tooling_defect` during baseline capture should refuse `run start`.** A foreign
`VIRTUAL_ENV` leaked into the executor, the suite produced no readable report, and the run went
on with no regression protection for that project. The issue asks for:

- refusing `run start` with `reason: "baseline_unreadable"`, naming the project and the defect,
  whenever a baseline suite invocation hits what a cycle would record as `tooling_defect`
  (`verdict.error`: no report produced, adapter parse failure), whatever
  `baseline_max_failure_ratio` says;
- `tdd doctor` warning when `VIRTUAL_ENV` is set and does not point inside a declared project
  root.

### What the code and the planning probes show (on `origin/main`, in a scratch worktree)

- `cmd_run_start` (`src/tddcli/cli.py`) never reads `verdict.error` from a baseline probe.
  `machine.py` turns `verdict.error` into a `tooling_defect` event, but only for cycle
  invocations (grep `"tooling_defect"`).
- Every adapter returns `verdict.error` **with no passed or failed ids**. Today an unreadable
  baseline is therefore refused only by accident, through R9.5a's generic refusal. With
  `test_command = "python -m pytest -p no:pytest_jsonreport tests/"` (a reporter-less
  environment as pytest sees it), `run start` replies `backend: the suite collected 1 test(s)
  but the baseline run executed no tests, so it observed nothing. Check `test_command` in
  tdd.toml and retry.` with `result: {"project": "backend", "collected": 1}`. That reply has no
  `reason` and does not name the defect. Where collection also finds nothing, the run starts
  with an empty baseline.
- **The refusal can be bypassed.** The serial path of `_probe_projects` writes the
  `--reuse-baselines` cache *before* `cmd_run_start` checks anything. In the probe, the first
  `run start --reuse-baselines` was refused, and the second, on the same tree, **started**
  (`ok: true`, `baselines: {backend: 0}`) from the cached empty probe. That still happens once
  the new refusal is in place (probed with the refusal and without the cache guard).
- Scope: with a project `svc` that produces an artifact (`check = "false"`) and a plan declaring
  only `backend`, `run start` records `stale_artifact` with `cycle_id` NULL, and the cycle close
  records it again with the cycle's id.
- The whole change, sketched in a scratch worktree and then deleted, kept the suite green
  (722 passed) once it had the exemption in decision 6. Without that exemption, one test broke:
  `tests/test_heartbeat.py::test_claim_records_projects_done_as_each_completes`. Its
  `repo_multi` fixture has an empty vitest `frontend`, and on this host `npx vitest run` printed
  no JSON there.

## Design decisions (locked)

1. **"The run's project set" is the R9.5c reachable set.** It is
   `config.reachable_projects([p for c in declared for p in c.projects])`: the declared
   projects plus the transitive `consumed_by` closure through artifacts. That is the set
   `run start` baselines and the set E-15 and the Execution section call "the projects the plan
   declares and those downstream of them". A downstream consumer is in it because a regenerated
   artifact rewrites its files during the run, so an artifact it produces can go stale through
   this run. An artifact is *in scope* when its root producer (`produced_by` resolved through
   any `artifact.<name>` chain, which `Config._root_project` already does, R7.5) is in that set.
   The set does not depend on `--baseline-all`, which is about baseline probing only.
   *Decided by evidence (PRD R9.5c, `Config.reachable_projects`, the issue's "(transitively)").*
2. **A cycle close also checks an out-of-scope artifact when that cycle touched its producer's
   root.** Applied literally, the issue's rule opens a hole. A cycle that edits an undeclared
   producer (allowed by P2, recorded as `undeclared_file_touched`; see the `repo_schema_other`
   fixture) could leave its artifact stale with nobody checking. R9.12 calls this check a hard
   gate because "a stale contract produces a *green* wrong answer". The close sweep already
   widens itself for the same edit (R9.2, `Config.close_sweep_projects`) with the predicate
   `Config._artifact_touched(art, touched)`. This plan reuses it, with the same `touched` set
   `_handle_refactor` hands the sweep. That staleness was caused by the run, not inherited, so it
   stays a `stale_artifact` with the cycle's id. *Decided by evidence (PRD R9.12's rationale, R9.2
   and its existing predicate).*
3. **`run start` still evaluates every artifact, and keeps today's behaviour for everything except
   the event name.** An out-of-scope artifact is still checked at `run start`. It is still
   regenerated and committed when its hook can do that, which leaves nothing inherited (pinned by
   cycle 1). A failing hook still refuses `run start` (#107, R9.12). Only an out-of-scope artifact
   that **stays stale** changes: it gets the inherited event instead of `stale_artifact`. In-scope
   artifacts are unchanged everywhere. *Decided by convention (keep today's behaviour wherever the
   issue asks for no change; #107 chose the refusal).*
4. **The inherited condition is one run-level integrity event.** Its kind is
   `artifact_stale_inherited`, its `cycle_id` is NULL, and its detail is
   `json.dumps(sorted(names))`, for example `["client", "spec"]`. It is written once, at
   `run start`, and only when at least one artifact is inherited. Nothing is added to the
   `run start` envelope, because the issue's audience is the auditor, and integrity events reach
   the auditor through `tdd metrics` and the friction log. *Decided by evidence (the issue names
   the kind and the list shape). The JSON-list detail follows `baseline_scoped` and
   `baseline_reused` in `cmd_run_start`.*
5. **Refuse on `verdict.error` from any probed baseline, before every other baseline check.**
   In `cmd_run_start`, straight after `_probe_projects` returns, gather every probed project
   (`name not in reused`) whose `verdict.error` is set, with the exemption in decision 6. If any
   are found, refuse before R9.5a's two checks and before R9.5g's ratio gate. `--accept-baseline`
   does not override it: that flag is R9.5g's, and a report that could not be read has no ratio.
   The refusal returns before `ledger.start_run`, so no run row is written. The surrounding
   `finally` releases the claim, as for R9.5a. *Decided by evidence: the issue says "independent
   of `baseline_max_failure_ratio`", and its reason is "a suite whose report cannot be read has
   produced no baseline at all".*
6. **Exemption: a project with no suite yet.** A probe whose collection found no tests **and** no
   failed files (`not collection.tests and not collection.failed_files`) is not refused, even when
   its runner wrote no report. The PRD already says so in R9.5a: "A project with no test files and
   no collection errors is not an error; it simply has no suite yet". With no tests there is no
   pre-existing failure for an unreadable report to hide. R9.5a's own "executed no tests" check
   is gated on `collection.tests` in the same way. Without the exemption,
   `test_claim_records_projects_done_as_each_completes` breaks (probed). Cycle 4 pins the
   exemption before cycle 5 adds the refusal. *Decided by evidence (PRD R9.5a, the probe).*
7. **The refusal follows its siblings' shape.** It is
   `failure(error, reason="baseline_unreadable", projects=[{"project": name, "defect": verdict.error}, ...])`,
   so `result.reason` and `result.projects` (the notes: a refusal's `reason` is never at the
   envelope's top level). `projects` lists every unreadable project in `probes` order, as
   `baseline_implausible` (R9.5g) and `services_unreachable` (R9.5i) do. The key is `defect`,
   after the `tooling_defect` event the same text produces mid-run. `error` is exactly:

   ```python
   "\n".join(
       f"{u['project']}: the baseline run produced no report the tool could read — {u['defect']}"
       for u in unreadable
   )
   + "\nA baseline that cannot be read observed nothing, whatever its failure count, so"
   " --accept-baseline does not apply. Fix the environment (`tdd doctor` notes a foreign"
   " VIRTUAL_ENV) and retry."
   ```

   *Decided by convention (R9.5g and R9.5i); the reason name comes from the issue.*
8. **A probe whose `verdict.error` is set is never written to the baseline cache.** In the serial
   loop of `_probe_projects`, the `ledger.cache_baseline(...)` call gains `and not verdict.error`.
   The parallel path never caches, so it needs no change. Without this, a retry with
   `--reuse-baselines` on the same tree reuses the empty probe and skips every check (probed).
   The probe is refused, and a refusal that a cache hit can undo is no refusal. *Decided by
   evidence (the probe, the order of operations in `_probe_projects` and `cmd_run_start`).*
9. **The doctor warning is a notice that always passes, shown only when `VIRTUAL_ENV` is set.**
   Doctor has no warning level: its checks pass or fail, and a failing one stops the executor
   (E-15). The repo's notices are checks that always pass and say what is wrong in their detail
   (`ledger isolation`, `executor identity`, PRD §5.1). The check is named `VIRTUAL_ENV` and is
   recorded with no `project`, after `executor identity` and before the per-project loop:
   - `VIRTUAL_ENV` unset or empty: no check is recorded.
   - Inside a project root: `rel = Path(venv).resolve().relative_to(worktree.resolve())`, and
     `cfg.owning_project(rel.as_posix())` names the project (longest root wins; a `"."` root owns
     everything in the worktree). The detail is `f"VIRTUAL_ENV={venv} is inside project {owner.name}'s root"`.
   - Outside (`relative_to` raises `ValueError`, or no project owns `rel`): the detail is exactly

     ```python
     f"VIRTUAL_ENV={venv} is outside every project root in tdd.toml, so it was inherited from"
     " whatever launched this shell. A suite runner that honours VIRTUAL_ENV runs in that"
     " environment instead of the project's own, where the reporter or the dependencies may be"
     " missing. Unset it before `tdd run start`."
     ```

   `{venv}` is the variable's value exactly as set, never the resolved path. A `.venv` at the root
   of a multi-project worktree that no project owns gets the notice, as the issue words it ("does
   not point inside a declared project root"). Because the notice always passes, that costs
   nothing. *Decided by evidence (the issue says "warn") and by convention (PRD §5.1's
   informational check).*
10. **No ledger shape change.** The new event is a row in the existing `integrity_event` table,
    and the cache guard only writes less. There is no `SCHEMA_VERSION` bump and no frozen referee
    (the repo note on schema bumps). *Decided by convention.*
11. **Docs.** PRD R9.12 gains the per-cycle scope (cycle 2) and the inherited event (cycle 3).
    The IntegrityEvent list in PRD §5 gains `artifact_stale_inherited` (cycle 3). A new R9.5j
    describes the refusal (cycle 5). R9.5e gains the cache rule (cycle 6). §8.1 gains the
    `VIRTUAL_ENV` notice (cycle 7). The README gets an "Unreadable baseline" subsection (cycle 5).
    `CHANGELOG.md` gets one entry under `## [Unreleased]` (cycle 7). *Decided by convention
    (`RELEASING.md`; every earlier plan's docs cycles).*

### Interactions with other open plans

- **#184** (`tasks/issue-184-silent-collection-failures.md`, plan merged, not implemented) edits
  R9.5a's nothing-collected refusal in `cmd_run_start` and PRD R9.5a. This plan adds a separate
  block before that loop and a separate R9.5j. They do not conflict in meaning. #184's tests break
  only `collect_command`, so their suite still writes a report and decision 5 never fires for
  them. Whichever lands second rebases a neighbouring hunk.
- **#110** (needs a decision: whether an unresolved `stale_artifact` should block the close and
  refuse `run start`). Under this plan, inherited staleness is no longer a `stale_artifact`. If
  #110's gate lands, it gates only what still emits `stale_artifact`, the in-scope and touched
  artifacts, which is what makes that gate livable for single-project plans. Neither plan
  depends on the other.

## Deliberate scope cuts (do not build)

None. Everything the issue asks for is built: the per-cycle scope, the inherited event, the
refusal and the doctor warning. Neighbouring paths the issue does not mention are left alone.
They are not cuts:

- R9.5a's own refusals ("no test could be collected", "executed no tests") still run after a
  cache write. A probe they refuse without a `verdict.error` (for example `-k` matching nothing)
  is still cached. Decision 8 closes the hole only for the probes this issue is about.
- A `tooling_defect` during a cycle is unchanged: it is recorded, not refused.
- The late start-sha probe (R9.5d, `Engine.probe_at_start_sha`) keeps its own observability
  rules.

## Fake/real divergence

There are no fakes. The unreadable suite is real pytest with its reporter plugin disabled
(`-p no:pytest_jsonreport`). pytest then rejects `--json-report` and writes no report, exactly as
in a venv without pytest-json-report (`unrecognized arguments: --json-report …`). Stale artifacts
use real shell `check`/`regenerate` commands. *Acceptable.*

## Cycles

Shared test material, used by the cycles below. Each piece is added by the first cycle that
uses it:

- In `tests/test_artifact_regeneration.py` (cycle 1 adds these; cycle 2 adds `import shutil` at
  the top):

  ```python
  def _add_svc(repo, artifact_toml: str) -> None:
      """A second pytest project, `svc`, that the module's `PLAN` (backend only) cannot reach."""
      (repo / "svc" / "tests").mkdir(parents=True, exist_ok=True)
      (repo / "svc" / "tests" / "test_smoke.py").write_text(
          "def test_smoke():\n    assert True\n"
      )
      with (repo / "tdd.toml").open("a") as f:
          f.write(
              "\n[project.svc]\n"
              'root       = "svc"\n'
              'adapter    = "pytest"\n'
              'test_paths = ["tests/"]\n'
              "lint       = []\n"
              "typecheck  = []\n" + artifact_toml
          )
      git(repo, "add", "-A")
      git(repo, "commit", "-q", "-m", "add svc")


  def _artifact_events(repo, run_id: int) -> list[tuple]:
      ledger = Ledger(gitutil.repo_identity(repo))
      return [
          (r["kind"], r["cycle_id"], r["detail"])
          for r in ledger.all(
              "SELECT kind, cycle_id, detail FROM integrity_event WHERE run_id = ?"
              " AND kind IN ('stale_artifact', 'artifact_stale_inherited') ORDER BY id",
              (run_id,),
          )
      ]


  OUTSIDE_CHECK_TOML = (
      "\n[artifact.client]\n"
      'path        = "svc/client.txt"\n'
      'produced_by = "svc"\n'
      'check       = "false"\n'
  )
  ```

  The module's `PLAN` declares one `refactor_cycle` on `backend`, so one `tdd advance` after
  `run start` closes the cycle and runs `check_artifacts(cycle)`.
- In `tests/test_baseline_integrity.py` (cycle 4 adds this; cycle 5 adds `import shutil`):

  ```python
  NO_REPORT = "python -m pytest -p no:pytest_jsonreport tests/"
  NO_REPORT_DEFECT = (
      "`python -m pytest -p no:pytest_jsonreport tests/` produced no JSON report"
      " (is pytest-json-report installed?): "
  )
  ```

  The module's `set_test_command(repo, command)` appends `test_command` to the `[project.backend]`
  table and commits with `git add -A`. Collection still uses the default `pytest`, so it still
  finds `tests/test_smoke.py`.

**Cycle 1 (pin): `tests/test_artifact_regeneration.py::test_run_start_still_regenerates_an_artifact_outside_the_runs_projects`.**

- **Setup:** `(repo / "svc").mkdir()` and `(repo / "svc" / "client.txt").write_text("v1\n")`. Then
  `_add_svc(repo, ...)` with this artifact:

  ```python
  "\n[artifact.client]\n"
  'path        = "svc/client.txt"\n'
  'produced_by = "svc"\n'
  "regenerate  = \"printf 'v2\\\\n' > svc/client.txt\"\n"
  ```

  Then `plan = write_plan(repo, PLAN)`, `run_cli(repo, "plan", "register", plan)`, and
  `out = run_cli(repo, "run", "start", "--plan", plan)`.
- **Single assertion:**
  `("chore(client): regenerate" in git(repo, "log", "--pretty=%s"), git(repo, "status", "--porcelain").strip(), _artifact_events(repo, out["run"]["id"])) == (True, "", [])`.
- **Kind:** pin. It passes on arrival (probed on `origin/main`), and it guards decision 3 while
  cycle 3 restructures `check_artifacts`'s `run start` path. No production change.

**Cycle 2: `tests/test_artifact_regeneration.py::test_a_cycle_close_checks_an_outside_artifact_only_when_the_cycle_touched_its_producer`.**

- **Setup:** `_add_svc(repo, OUTSIDE_CHECK_TOML)` and `plan = write_plan(repo, PLAN)`. Then, for
  `case in ("untouched", "touched")`: `r = shutil.copytree(repo, tmp_path / case)`, register `plan`
  in `r`, `out = run_cli(r, "run", "start", "--plan", plan)`. For `"touched"` only, also
  `(r / "svc" / "extra.py").write_text("X = 1\n")`. Then `run_cli(r, "advance")`, and
  `seen[case] = [(kind, detail) for kind, cycle_id, detail in _artifact_events(r, out["run"]["id"]) if cycle_id is not None]`.
  The touched copy's `advance` replies `blocked`, because the run-close gate sees
  `svc/extra.py` uncommitted. That reply is expected and not asserted: the check runs before the
  gate.
- **Single assertion:** `seen == {"untouched": [], "touched": [("stale_artifact", "client")]}`.
- **Production:**
  - `src/tddcli/config.py`: add `Config.producer_root(self, art: Artifact) -> str | None`, which
    returns `self._root_project(art.produced_by)`. Rename `_artifact_touched` to
    `artifact_touched` and update its one caller, `close_sweep_projects`. No test references
    either name (grepped).
  - `src/tddcli/machine.py`: `check_artifacts(self, cycle_row, touched: set[str] | None = None)`.
    Compute `scope = set(self.config.reachable_projects([p for c in self.declared for p in c.projects]))`.
    When `cycle_row is not None`, skip (`continue`, before `_artifact_stale` runs and before any
    `artifact_check` row) every artifact whose `producer_root` is not in `scope` and for which
    `not self.config.artifact_touched(art, touched or set())`.
  - `src/tddcli/advance.py::_handle_refactor`: call `engine.check_artifacts(cycle, touched)`.
  - `docs/PRD.md` R9.12: add, after its first sentence: "At a cycle close only the artifacts the
    run can affect are checked: those whose root producer is in the run's reachable set (R9.5c),
    and any whose producer root the closing cycle touched (the test R9.2 uses to widen the close
    sweep)."
- **EXPECTED FAILURE:** `AssertionError`: `{'untouched': [('stale_artifact', 'client')], 'touched': [('stale_artifact', 'client')]}`
  is not equal to the expected dict (probed on `origin/main`).

**Cycle 3: `tests/test_artifact_regeneration.py::test_run_start_reports_outside_stale_artifacts_once_as_inherited`.**

- **Setup:** `_add_svc(repo, OUTSIDE_CHECK_TOML + "\n[artifact.spec]\n" 'path        = "svc/spec.json"\n' 'produced_by = "svc"\n' 'check       = "false"\n')`,
  then `plan = write_plan(repo, PLAN)`, register it, and `out = run_cli(repo, "run", "start", "--plan", plan)`.
  `run start` succeeds.
- **Single assertion:**
  `_artifact_events(repo, out["run"]["id"]) == [("artifact_stale_inherited", None, '["client", "spec"]')]`.
- **Production:** `Engine.check_artifacts` in `src/tddcli/machine.py`. When `cycle_row is None`
  and an artifact is out of scope (decision 1) and still unresolved, append `art.name` to a local
  `inherited` list instead of writing `stale_artifact`. After the loop, if `inherited` is not
  empty, `self.ledger.event(self.run["id"], None, "artifact_stale_inherited", json.dumps(sorted(inherited)))`.
  Evaluation, regeneration and hook-failure handling stay exactly as they are (cycle 1 guards
  them). In `docs/PRD.md`, add to R9.12: "Any other artifact's staleness was inherited from the
  branch point. `run start` still checks it, regenerates it, and refuses when its hook fails. If
  it stays stale, `run start` records one `artifact_stale_inherited` integrity event instead of
  `stale_artifact`. Its detail is a JSON array of those artifact names, and no cycle checks them
  again (issue #99)." Then add `artifact_stale_inherited` to the IntegrityEvent "Typed:" list
  (grep `` `off_protocol_invocation`, `stale_artifact` ``).
- **EXPECTED FAILURE:** `AssertionError`: `[('stale_artifact', None, 'client'), ('stale_artifact', None, 'spec')]`
  is not equal to `[('artifact_stale_inherited', None, '["client", "spec"]')]` (probed on
  `origin/main`, and cycle 2 does not touch the `run start` path).

**Cycle 4 (pin): `tests/test_baseline_integrity.py::test_a_project_with_no_tests_is_not_refused_when_its_suite_writes_no_report`.**

- **Setup:** `(repo / "backend" / "tests" / "test_smoke.py").unlink()`, then
  `set_test_command(repo, NO_REPORT)`, which commits the deletion too. Then
  `plan = write_plan(repo, PLAN)`, register it, and `out = run_cli(repo, "run", "start", "--plan", plan)`.
- **Single assertion:** `(out["ok"], out["result"]["baselines"]) == (True, {"backend": 0})`.
- **Kind:** pin. It passes on arrival (probed: `ok: true`, `baselines: {backend: 0}`), and it
  guards decision 6 before cycle 5 adds the refusal. No production change.

**Cycle 5: `tests/test_baseline_integrity.py::test_run_start_refuses_a_baseline_whose_suite_produced_no_report`.**

- **Setup:** `set_test_command(repo, NO_REPORT)` and `plan = write_plan(repo, PLAN)`. Then, for
  `jobs in ("1", "2")`: `r = shutil.copytree(repo, tmp_path / f"jobs{jobs}")`, register `plan` in `r`,
  and
  `out = run_cli(r, "run", "start", "--plan", plan, "--baseline-jobs", jobs, "--accept-baseline")`.
  `--accept-baseline` is there on purpose: it pins that the flag does not override this refusal
  (decision 5). `--baseline-jobs 2` pins that the parallel probe path is refused the same way.
  Record:

  ```python
  projects = out["result"].get("projects", [])
  seen[jobs] = (
      out["ok"],
      out["result"].get("reason"),
      [(p.get("project"), str(p.get("defect", "")).startswith(NO_REPORT_DEFECT)) for p in projects],
      "backend: the baseline run produced no report the tool could read — " + NO_REPORT_DEFECT
      in (out.get("error") or ""),
  )
  ```
- **Single assertion:**
  `seen == {j: (False, "baseline_unreadable", [("backend", True)], True) for j in ("1", "2")}`.
- **Production:** `cmd_run_start` in `src/tddcli/cli.py`. Straight after the
  `except RuntimeError` that wraps `_probe_projects`, and before the R9.5a loop, gather
  `unreadable = [{"project": n, "defect": v.error} for n, (v, c) in probes.items() if n not in reused and v.error and (c.tests or c.failed_files)]`.
  If it is not empty, return decision 7's `failure`. In `docs/PRD.md`, add **R9.5j** after R9.5i:
  "`run start` refuses a baseline whose suite produced no report the tool could read (the
  adapter's `Verdict.error`, which a cycle records as `tooling_defect`). The refusal returns
  `reason: "baseline_unreadable"` and a `projects` array carrying `{project, defect}`. It runs
  before R9.5a's checks and R9.5g's ratio gate, and `--accept-baseline` does not override it. A
  project with no tests and no collection errors is exempt, as in R9.5a. Nothing is written to
  the ledger (issue #99)." In `README.md`, add a `### Unreadable baseline (R9.5j)` subsection
  after "Baseline sanity gate (R9.5g)" (before `### Standing-failure delta`). It takes three
  sentences: what refuses, the `reason` and `projects` shape, and the fix (`tdd doctor`, a
  foreign `VIRTUAL_ENV`, the reporter installed).
- **EXPECTED FAILURE:** `AssertionError`. Today each case is
  `(False, None, [], False)`: the reply is R9.5a's "the suite collected 1 test(s) but the baseline
  run executed no tests" with `result: {"project": "backend", "collected": 1}` (probed for
  `--baseline-jobs 1` and 2 on `origin/main`).

**Cycle 6: `tests/test_baseline_integrity.py::test_an_unreadable_baseline_is_not_cached_for_reuse`.**

- **Setup:** `set_test_command(repo, NO_REPORT)`, `plan = write_plan(repo, PLAN)`, register it.
  Then `first = run_cli(repo, "run", "start", "--plan", plan, "--reuse-baselines")` and
  `second = run_cli(repo, "run", "start", "--plan", plan, "--reuse-baselines")`, on the same
  tree, with nothing in between.
- **Single assertion:**
  `(first["result"].get("reason"), second["result"].get("reason")) == ("baseline_unreadable", "baseline_unreadable")`.
- **Production:** `_probe_projects` in `src/tddcli/cli.py`, serial loop: cache only
  `if reuse_baselines and cfg is not None and config_sha is not None and not verdict.error`. In
  `docs/PRD.md` R9.5e, add: "A probe whose suite produced no readable report (R9.5j) is never
  cached."
- **EXPECTED FAILURE:** `AssertionError` against `('baseline_unreadable', None)`. After cycle 5,
  `second` is `ok: true` with `baselines: {backend: 0}`, reused from the cached empty probe
  (probed with cycle 5's change and without this one).

**Cycle 7: `tests/test_doctor_blockers.py::test_doctor_notes_a_virtual_env_outside_every_project_root`.**

- **Setup:** fixtures `repo, tmp_path, monkeypatch`. `inside = repo / "backend" / ".venv"` and
  `outside = tmp_path / "some-other-repo" / ".venv"`. Neither needs to exist. For
  `case, venv in (("unset", None), ("inside", inside), ("outside", outside))`: when `venv` is
  `None`, call `monkeypatch.delenv("VIRTUAL_ENV", raising=False)`. That is needed because
  `uv run pytest` sets it for the whole test process. Otherwise call
  `monkeypatch.setenv("VIRTUAL_ENV", str(venv))`. Then `out = run_cli(repo, "doctor")` and
  `seen[case] = [c for c in out["result"]["checks"] if c["check"] == "VIRTUAL_ENV"]`. Do not
  use the module's `_check` helper: it asserts exactly one match, and `"unset"` has none.
- **Single assertion:**

  ```python
  seen == {
      "unset": [],
      "inside": [
          {"check": "VIRTUAL_ENV", "ok": True,
           "detail": f"VIRTUAL_ENV={inside} is inside project backend's root"}
      ],
      "outside": [
          {"check": "VIRTUAL_ENV", "ok": True,
           "detail": f"VIRTUAL_ENV={outside} is outside every project root in tdd.toml, so it"
           " was inherited from whatever launched this shell. A suite runner that honours"
           " VIRTUAL_ENV runs in that environment instead of the project's own, where the"
           " reporter or the dependencies may be missing. Unset it before `tdd run start`."}
      ],
  }
  ```
- **Production:** `cmd_doctor` in `src/tddcli/cli.py`, after the `executor identity` check
  (decision 9). `os` and `Path` are already imported there. In `docs/PRD.md` §8.1, add a
  paragraph after the "Every failing check carries a `detail`" paragraph: when `VIRTUAL_ENV` is
  set, doctor records an informational `VIRTUAL_ENV` check (always `ok: true`). It names the
  owning project, or warns that the variable points outside every project root and was
  inherited (issue #99). In `CHANGELOG.md`, under `## [Unreleased]`:
  - a `### Fixed` entry naming #99, saying `stale_artifact` is no longer recorded on every cycle
    for an artifact the run cannot produce (it is reported once at `run start` as
    `artifact_stale_inherited`);
  - a `### Fixed` entry saying `run start` refuses a baseline whose suite produced no readable
    report (`baseline_unreadable`), also on a `--reuse-baselines` retry;
  - an `### Added` entry for doctor's `VIRTUAL_ENV` notice.
- **EXPECTED FAILURE:** `AssertionError` against `{'unset': [], 'inside': [], 'outside': []}`
  (probed on `origin/main`; doctor stays `ok: true` in all three cases).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-99-inherited-artifacts-unreadable-baseline   # first, before anything else
    tdd doctor                                  # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-99-inherited-artifacts-unreadable-baseline.md   # captures baselines, opens cycle 1

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
  - Cycles 1 and 4 are pins: their tests pass on arrival by design, and they need no production
    change.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`, if a standard cycle's RED
    pre-passes. Mutate the increment that cycle added.
  - `annotate_cycle` → `tdd annotate --key --value`. This plan declares no keys of its own;
    `plan_defect` and `friction_note` are reserved.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|tooling> --detail '...'`.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.
  - No cycle declares a stub: every test imports only names that exist today (`shutil` is the
    standard library).

**Minimal GREEN, per cycle — add this and nothing earlier:**

- cycle 2 adds the per-cycle skip (`producer_root`, the `artifact_touched` rename, the `touched`
  argument). It does not change what `run start` records.
- cycle 3 adds the `inherited` list and the `artifact_stale_inherited` event on the `run start`
  path, and nothing else.
- cycle 5 adds the `baseline_unreadable` refusal (with decision 6's exemption) and does not touch
  `_probe_projects`.
- cycle 6 adds the `not verdict.error` cache guard, and nothing else.
- cycle 7 adds the `VIRTUAL_ENV` check to `cmd_doctor`, and nothing else.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-99-inherited-artifacts-unreadable-baseline-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-99-inherited-artifacts-unreadable-baseline-friction.md
    git commit -m "docs: friction log for issue-99-inherited-artifacts-unreadable-baseline"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #99`. Cycles 2, 3, 5, 6 and 7 own the docs:

- `git diff --stat origin/main -- docs/PRD.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- README.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.

The visible changes are a JSON refusal, an integrity event and a doctor check, so no demo
recording is required. In the PR body, quote one `baseline_unreadable` refusal and the
`VIRTUAL_ENV` doctor check for a path outside the worktree.
