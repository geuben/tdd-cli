---
closes: 44
cycles:
  - n: 1
    project: tddcli
    title: "reachable_projects returns declared projects when no artifacts exist"
    test: "tests/test_config_and_staging.py::test_reachable_projects_returns_declared_when_no_artifacts"
    files: ["src/tddcli/config.py"]
    commit_red: "test: reachable_projects with no artifact graph"
    commit_green: "feat: Config.reachable_projects, declared-only case"

  - n: 2
    project: tddcli
    title: "reachable_projects follows consumed_by transitively"
    test: "tests/test_config_and_staging.py::test_reachable_projects_includes_transitive_consumers"
    files: ["src/tddcli/config.py"]
    commit_red: "test: reachable_projects transitive consumed_by closure"
    commit_green: "feat: transitive consumer closure in reachable_projects"

  - n: 3
    project: tddcli
    title: "reachable_projects resolves artifact.<name> producer chains to their root project"
    test: "tests/test_config_and_staging.py::test_reachable_projects_resolves_artifact_upstream_chain"
    files: ["src/tddcli/config.py"]
    commit_red: "test: reachable_projects follows artifact upstream chains"
    commit_green: "feat: resolve artifact.<name> producers in reachable_projects"
    commit_refactor: "refactor: shared root-producer resolution for touched and reachable"

  - n: 4
    project: tddcli
    title: "downstream projects excluded from the close sweep are not reachable"
    test: "tests/test_config_and_staging.py::test_reachable_projects_excludes_downstream_not_in_close_sweep"
    files: ["src/tddcli/config.py"]
    commit_red: "test: in_close_sweep filter on reachable consumers"
    commit_green: "feat: reachable_projects respects in_close_sweep"

  - n: 5
    project: tddcli
    title: "run start probes only reachable projects"
    test: "tests/test_baseline_integrity.py::test_run_start_probes_only_reachable_projects"
    files: ["src/tddcli/cli.py", "tests/conftest.py"]
    modifies_tests: ["tests/test_heartbeat.py::test_claim_records_projects_done_as_each_completes"]
    commit_red: "test: run start scopes baseline probe to reachable projects"
    commit_green: "feat: scope run-start baseline capture to plan-reachable projects"

  - n: 6
    project: tddcli
    title: "skipped projects are recorded via a baseline_scoped event"
    test: "tests/test_baseline_integrity.py::test_run_start_records_baseline_scoped_event"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: baseline scoping is recorded on the run"
    commit_green: "feat: record baseline_scoped event with skipped projects"

  - n: 7
    project: tddcli
    title: "--baseline-all restores full probing"
    test: "tests/test_baseline_integrity.py::test_run_start_baseline_all_probes_every_project"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: --baseline-all opts out of scoping"
    commit_green: "feat: --baseline-all flag on run start"

  - n: 8
    project: tddcli
    title: "no_baseline_for_project is a typed blocker kind"
    test: "tests/test_baseline_integrity.py::test_blocker_accepts_no_baseline_for_project_kind"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: no_baseline_for_project blocker kind"
    commit_green: "feat: no_baseline_for_project blocker kind"

  - n: 9
    project: tddcli
    title: "the sweep separates un-baselined projects' failures from regressions"
    test: "tests/test_baseline_integrity.py::test_sweep_reports_unbaselined_failures_separately"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: sweep separates unattributable failures"
    commit_green: "feat: sweep classifies un-baselined failures as unattributable"

  - n: 10
    project: tddcli
    title: "close sweep with unattributable failures directs the blocker path"
    test: "tests/test_baseline_integrity.py::test_close_sweep_with_unbaselined_failures_directs_resolve_blocker"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: unattributable sweep failures direct the blocker path"
    commit_green: "feat: unattributable sweep failures get a legible blocker reply"

  - n: 11
    project: tddcli
    title: "--accept-failures creates a baseline row for a project that never had one"
    test: "tests/test_baseline_integrity.py::test_accept_failures_inserts_baseline_row_for_unbaselined_project"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: accept-failures covers projects with no baseline row"
    commit_green: "fix: accept-failures inserts missing baseline rows"
---

# Issue #44 — scope baseline capture at run start to plan-reachable projects

https://github.com/geuben/tdd-cli/issues/44
Task file: `tasks/issue-44-scoped-baselines.md`

## Context

`run start` probes **every** project in `tdd.toml` to capture its baseline
(`_probe_projects`, R9.5a). On repos with many projects this makes starting a run
expensive even when the plan only touches a few. A run can only ever execute the
projects its cycles declare plus downstream consumers pulled in by the close sweep via
the artifact graph — both computable at `run start` from the registered contract. The
baseline exists solely to be subtracted from later failure sets (R9.6); for a project
that never runs there is nothing to subtract, so skipping its probe loses no safety.

The one hole: the sweep's `touched` set is worktree-wide (`Engine.authored_changes`
returns every changed path minus pre-existing dirt), so an edit inside a *non-declared*
project's root marks that project's artifacts touched and pulls their consumers —
un-baselined — into the close sweep. Those failures are *unattributable*: there is no
baseline to subtract, and they must surface as a typed blocker
(`no_baseline_for_project`), never as regressions. Recovery is the existing R9.5b path
(`resume --unblock --accept-failures`), which must learn to insert a baseline row for a
project that never had one.

Ordering: cycles 1–4 build the pure reachability computation in `config.py`; 5–7 wire it
into `cmd_run_start` with auditability and an opt-out; 8–11 handle the dynamic escape
hatch (blocker kind → sweep classification → advance reply → recovery).

## Verified repo facts

*Every fact below was probed against the codebase or executed during hardening — none
are asserted from memory. Locators are function names; grep for them at execution time.*

- **Probed, current behavior:** a three-project repo (`backend`, `svc`, `other`;
  artifact `schema` produced_by `backend`, consumed_by `svc`) with a plan declaring only
  `backend` reports `baselines: {"backend": 0, "svc": 0, "other": 0}` from
  `run start` today. Under scoping the same fixture must report
  `{"backend": 0, "svc": 0}` with `other` skipped. The fixture recipe: extend the
  `repo` fixture, write the three-project `tdd.toml` with the artifact edge, commit the
  artifact's path (`backend/schema.json`), commit everything before registering.
- Declared cycles are available pre-run: `contract_row["declared_cycles"]` JSON, parsed
  by `contract_mod.cycles_from_json` (see `Engine.__init__` in `machine.py`); each
  `DeclaredCycle` carries `projects`.
- `_probe_projects` (`cli.py`) iterates `cfg.projects.items()`; `cmd_run_start` passes
  `projects_total=len(cfg.projects)` into `ledger.claim` and inserts a `baseline` +
  `collection_snapshot` row per probe. Scoping means: compute the reachable set *before*
  `ledger.claim`, pass the subset mapping into `_probe_projects`, and derive
  `projects_total` and both row inserts from that same mapping.
- **`Config._artifact_touched` keys on the producer's root, not the artifact's path**:
  its base case is `any(proj.owns(p) for p in touched)` over the producing project's
  root, recursing through `artifact.<name>` chains via `upstream_artifact`. Static
  reachability therefore closes over: artifact whose root producer ∈ set → union
  `consumed_by`. Reuse this recursion (extract a shared root-producer helper in cycle
  3's refactor step).
- `close_sweep_projects` (`config.py`) filters **all** sweep names by
  `Project.in_close_sweep` — including cycle projects — but `Engine.run_projects`
  (RED/GREEN) runs declared projects unfiltered. Hence cycle 4's rule: closure-added
  consumers respect `in_close_sweep`; declared projects are always reachable.
- Only the close sweep can reach an un-baselined project: `run_projects` runs only
  declared projects, which are always probed.
- `Engine.sweep` (`machine.py`) uses `baselines.get(name, set())` — a missing baseline
  silently means "empty", classifying every pre-existing failure as a regression.
  `Ledger.baselines(run_id)` returns a dict keyed by project, so `name not in
  baselines` cleanly distinguishes "no row" from "empty row".
- **Probed:** `SweepOutcome` (`machine.py`) has fields `failures`, `gates` and an `ok`
  property; nothing outside `machine.py` constructs it, so adding an `unbaselined`
  field with a default breaks no existing test.
- `advance._handle_refactor` branches `if not outcome.ok:` → `if outcome.failures:` →
  FIX_REGRESSION, else a gates reply. After cycle 9 and before cycle 10, an
  unbaselined-only outcome therefore replies FIX_REGRESSION with **empty** `gates` —
  that malformed reply is cycle 10's expected RED evidence.
- **Probed:** `BLOCKER_KINDS` (`cli.py`) does not contain `no_baseline_for_project`;
  `cmd_blocker` rejects unknown kinds with `unknown blocker kind ...`.
- `_accept_failures_into_baseline` (`cli.py`) does `if row is None: continue` — the
  exact gap cycle 11 closes. It reads the last CLOSE_SWEEP invocation per project, so
  cycle 11's fixture must reach a close sweep before blocking.
- **Existing-test blast radius — exactly one test.** Every test file with a
  multi-project config was enumerated:
  `tests/test_heartbeat.py::test_claim_records_projects_done_as_each_completes` uses
  `repo_multi` with a plan declaring only `backend` and asserts both projects are
  probed (`len(seen) == 2`, `projects_total == 2`). Scoping breaks it. Authorized fix
  (declared in cycle 5's `modifies_tests`): add a second cycle
  (`n: 2, project: frontend, refactor_cycle: true`) to that test's module-level `PLAN`
  so both projects stay reachable and every existing assertion keeps its meaning. Do
  not weaken the assertions. All other multi-project fixtures are safe:
  `repo_broken` is doctor-only, `test_stub_hint` starts runs on single-project `repo`,
  `test_example_plan` registers without starting, `test_batch_collection`'s run-start
  test uses single-project `repo`, `test_progress` builds claims by hand.
- The `repo_multi` docstring in `tests/conftest.py` claims `run start` reports both
  baselines — update the docstring in cycle 5 (conftest is in its `files`).
- `Config.full_sweep_projects` has **no callers** — no code path sweeps every project,
  so no hidden reachability escape. If a future full-repo sweep command appears it must
  compose with scoping; out of scope here.
- Cycles 1–4 tests: `tests/test_config_and_staging.py` already has a `cfg` fixture
  (backend/frontend/e2e with `in_close_sweep = false` on e2e, plus chained artifacts
  `openapi` → `api_client`) and sits beside the existing `close_sweep_projects` tests —
  write the new tests in its style; build a small inline TOML variant where the shared
  fixture lacks the needed edge (cycle 4 needs a consumer with
  `in_close_sweep = false`).
- Test-harness helpers: `run_cli` returns parsed envelope dicts; `write_plan` commits
  the plan; both in `tests/conftest.py`. `test_baseline_integrity.py` drives full runs
  through `run_cli` — copy its style for cycles 5–11.

## Cycle detail

*Expected failure per cycle, probe-verified where marked; minimum GREEN; resist future
cycles' behavior.*

### Cycle 1 — declared-only reachability

**Expected RED (probed):** `AttributeError: type object 'Config' has no attribute
'reachable_projects'`.

Test: use the existing `cfg` fixture but pass a declared list touching no artifact
producer — or a minimal inline TOML with no artifacts; `reachable_projects(["b"]) ==
["b"]`. GREEN: `return sorted(set(declared))`. No artifact logic yet.

### Cycle 2 — transitive consumers

**Expected RED:** assertion — result lacks the consumers.

Inline TOML: artifact X `produced_by p1, consumed_by [p2]`; artifact Y `produced_by p2,
consumed_by [p3]`. `reachable_projects(["p1"]) == ["p1", "p2", "p3"]`. GREEN: fixpoint
loop unioning `consumed_by` of artifacts whose producing project is in the set.

### Cycle 3 — artifact upstream chains

**Expected RED:** assertion — the chained consumer is missing (producer `artifact.X`
not resolved to its root project).

The shared `cfg` fixture already chains `api_client` (`produced_by =
"artifact.openapi"`) — assert `reachable_projects(["backend"])` includes `frontend`
via the chain. GREEN: resolve producers through `upstream_artifact` to a root project
before the membership check. REFACTOR (declared `commit_refactor`): extract the shared
root-producer resolution used by `_artifact_touched` and `reachable_projects` into one
helper — the suite, including the existing `close_sweep_projects` tests, is the guard.

### Cycle 4 — in_close_sweep filter

**Expected RED:** assertion — the opted-out consumer is present.

Inline TOML variant: consumer `p2` has `in_close_sweep = false`.
`reachable_projects(["p1"])` omits it; `reachable_projects(["p2"])` still includes it
(declared always wins — mirrors `run_projects`, which runs declared projects
unfiltered). GREEN: filter closure-added, non-declared projects by `in_close_sweep`,
matching `close_sweep_projects`.

### Cycle 5 — scoped probing at run start

**Expected RED (probed):** `assert {"backend": 0, "svc": 0, "other": 0} == {"backend":
0, "svc": 0}` — today every project is probed.

Fixture (probe-verified recipe, add to `tests/conftest.py` as e.g. `repo_three`): the
`repo` fixture plus projects `svc` and `other` (each one trivial passing test) and
artifact `schema` (`path = "backend/schema.json"`, `produced_by = "backend"`,
`consumed_by = ["svc"]`, `regenerate = "true"`); commit `backend/schema.json` and all
of it. Plan declares only `backend` → reachable = `{backend, svc}`.

Test: `run start` envelope `result.baselines == {"backend": 0, "svc": 0}` and the
ledger has baseline rows for exactly those two projects.

GREEN: in `cmd_run_start`, parse declared cycles from `contract_row`, compute
`cfg.reachable_projects(union of cycle projects)`, pass the subset mapping to
`_probe_projects` (change its signature to take the mapping), and derive
`projects_total`, the `baseline` rows, and the `collection_snapshot` rows from that
same mapping. Guard: when the contract has no declared cycles (`--allow-undeclared`) or
`--baseline-all` is set (cycle 7), probe all of `cfg.projects` — see scope cuts.

Authorized test edit (`modifies_tests`): extend the module-level `PLAN` in
`tests/test_heartbeat.py` with `n: 2, project: frontend, refactor_cycle: true` plus a
`commit_refactor` line, so `test_claim_records_projects_done_as_each_completes` keeps
asserting exactly what it asserts today. Also update the `repo_multi` docstring in
`tests/conftest.py`. Never weaken either assertion.

### Cycle 6 — auditability

**Expected RED:** assertion — no `baseline_scoped` event found.

Same fixture. After a scoped start, an event `baseline_scoped` exists on the run whose
detail JSON is `["other"]`. GREEN: beside the `plan_blob_changed` event emission (after
the run row exists), emit `ledger.event(run_id, None, "baseline_scoped",
json.dumps(sorted(skipped)))` when the probed set is smaller than `cfg.projects`. A
quietly smaller baseline is worse than a slow one — never scope silently.

### Cycle 7 — opt-out

**Expected RED:** the CLI rejects the flag — argparse `unrecognized arguments:
--baseline-all` (surface: `run_cli` raising `SystemExit`, so write the test with
`pytest.raises(SystemExit)` around the *current* behavior inverted: call
`run start --baseline-all` and assert three baseline entries; today the call dies on
argparse before producing an envelope).

Same fixture: `run start --plan <p> --baseline-all` → `result.baselines` has all three
projects and no `baseline_scoped` event exists. GREEN: add `--baseline-all` to the
`run start` subparser; when set, probe `cfg.projects` unchanged.

### Cycle 8 — typed blocker kind

**Expected RED (probed):** envelope failure `unknown blocker kind
'no_baseline_for_project'` — the kind is absent from `BLOCKER_KINDS` today.

Copy the harness of the existing
`test_a_failure_the_baseline_missed_has_its_own_blocker_kind`: start a run on `repo`,
then `tdd blocker no_baseline_for_project --detail ...` succeeds and blocks the run.
GREEN: add the kind to `BLOCKER_KINDS` with a comment distinguishing it from
`pre_existing_failure` (no baseline to subtract vs. a baseline that missed one).

### Cycle 9 — sweep classification

**Expected RED (probed):** `SweepOutcome` has fields `failures`, `gates` only → the
test fails on the missing `unbaselined` attribute (`AttributeError` or `TypeError` on
construction, depending on how the test reads it).

Engine-level test (construct `Engine` directly, or drive a run and delete the consumer's
baseline row via the ledger — the direct-ledger route is simpler and legitimate here):
a sweep over a project with **no baseline row** and a failing test →
`outcome.unbaselined == {"svc": [<the failing id>]}`, that id absent from
`outcome.failures`, and `outcome.ok` is False. GREEN: add
`unbaselined: dict[str, list[str]]` (default empty) to `SweepOutcome`, include it in
`ok`, and in `Engine.sweep` route `verdict.failed` there when `name not in baselines`.

### Cycle 10 — advance reply

**Expected RED (derived from the handler's branch order, stated above):** the envelope
verb is `fix_regression` with **empty** `failures` and `gates` — the malformed
gates-reply branch — where the test expects `resolve_blocker`.

End-to-end on the cycle-5 fixture, reshaped: artifact `schema` is `produced_by =
"other"`, `consumed_by = ["svc"]`, and `svc` carries one committed **failing** test;
plan declares `backend` only, so `svc` is un-baselined. Drive the run through RED and
GREEN (`tdd advance` twice with a real test + implementation, copying the loop style in
`test_baseline_integrity.py`), and during GREEN also write a file under `other/` —
`authored_changes` is worktree-wide, so the sweep's `touched` set includes it,
`_artifact_touched` fires on `other`'s root, and the close sweep pulls in `svc`.
Assert: verb `resolve_blocker`, detail names `no_baseline_for_project` and
`resume --unblock --accept-failures`, and the per-project failure map is in the reply.

GREEN: in `_handle_refactor`, branch on `outcome.unbaselined` **before** the
`outcome.failures` branch, replying RESOLVE_BLOCKER with the map and both recovery
commands.

**This is the fiddliest cycle.** The fixture must commit `svc`'s failing test *before*
`run start` (it must be pre-existing, not authored), and the stray `other/` edit must
happen before `tdd advance` closes the cycle. If the sweep does not pull `svc` in,
debug via the ledger's CLOSE_SWEEP invocations before touching production code.

### Cycle 11 — recovery

**Expected RED:** assertion — no baseline row inserted for the un-baselined project
(`_accept_failures_into_baseline` skips projects without a row).

Reuse cycle 10's end state: blocked run whose last close sweep saw `svc` failures with
no `svc` baseline row; `resume --unblock --accept-failures --note ...` → a fresh
baseline row exists for `svc` containing exactly those failures, and the
`baseline_amended` event records them. GREEN: replace the skip with an insert
(`failing` = the sweep's failures, `captured_at=now()`).

## Deliberate scope cuts (do not build)

- **Baseline reuse across runs (#45) and parallel probing (#46).** Separate issues.
- **`projects_total` on the claim** is derived from the probed mapping in cycle 5's
  GREEN but has no dedicated test: it is released before the envelope returns and is
  cosmetic (progress display) — do not add machinery to pin it. The heartbeat test in
  `modifies_tests` keeps it honest for the both-projects case.
- **Undeclared contracts keep full probing** (no declared cycles → no reachable set to
  compute). One guard line in cycle 5's GREEN, no dedicated test: an undeclared run
  fails at "contract declares no cycles" regardless, so the branch is unobservable in
  an envelope.
- **No new sweep of every project.** `full_sweep_projects` stays uncalled; do not wire
  it up.
- **PRD/README documentation** of the scoping and the new blocker kind: same PR, after
  the run completes, not a cycle (see Done-criteria).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do
not ask the user to start the run. `tdd run start` records which model is executing,
resolved from your own session; a run started by anyone else attributes this work to
the wrong agent.

**Referee rule:** run the *released* `tdd`, never this working tree's editable install.
Do not work in a shell with this repo's `.venv` activated. Verify before starting:
`which tdd` → `~/.local/bin/tdd` and `tdd --version` → the pinned release (0.6.0 at
hardening time). The suites under test are still this working tree's code; only the
controller is pinned.

    git checkout feat/44-scoped-baselines           # exists: created at hardening, carries this plan
    tdd doctor                                      # must report healthy: true
    tdd run start --plan tasks/issue-44-scoped-baselines.md

The branch already exists and carries this plan's commit — check it out; if it has
grown unrelated work, stop and ask.

Then repeat until done: read `next_action.verb`, do exactly what it says, run
`tdd advance`. Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit
it, and raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or
  `git commit` — the tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. Expected
  baseline for this repo: `{"tddcli": 0}` — anything else means a moved branch; stop.
- Verbs this plan can hit: `run_sensitivity_check` → `tdd sensitivity begin|check|end`
  (only if a RED passes on arrival — none is expected to); `resolve_blocker` →
  `tdd blocker --kind --detail` (kinds: `plan_defect`, `tooling`, `regression`,
  `pre_existing_failure`); `confirm_cycle_applicable` on a cycle the codebase has
  outgrown → `tdd cycle skip --reason`. This plan declares no `annotation_keys`.

## Done-criteria

**Before finishing:** run
`tdd log render --out tasks/friction-logs/issue-44-scoped-baselines-friction.md` and
`tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped —
and every integrity event. Do not narrate what the ledger already records.

Then the documentation follow-up, committed as ordinary commits on the branch after the
run is terminal: PRD R9.5 family (add R9.5c for scoping and the
`no_baseline_for_project` kind) and the README's `run start` section.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-44-scoped-baselines-friction.md
    git commit -m "docs: friction log for issue-44-scoped-baselines"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates,
pushes the branch and opens the PR against `main`. Do not push or call the GitHub API
by hand. If a gate fails, fix it and re-run the skill — a failed gate is work, not a
reason to hand back.
