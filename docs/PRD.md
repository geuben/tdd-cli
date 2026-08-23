# TDD CLI — Product Requirements & Specification

Status: implemented — v0.1.0 implements this specification; changes to specified behaviour amend this document in the same PR
Date: 2026-08-03
Scope: greenfield. Nothing from the predecessor system (§1) is reused.
Consumers: autonomous coding agents (primary), humans supervising them (secondary).

---

## 1. Problem

This tool's predecessor coordinated agent-driven TDD through a markdown skill and a
read-only test runner, with a JSON file on disk as the shared state. The agent both
performed the work and recorded its own compliance. That produced four failure classes,
all observed in practice:

1. **State corruption.** Phase transitions are written by the agent, so they record what the
   agent believes rather than what happened. State files proliferate per-directory, drift in
   schema, go stale, and get worked around (in one case with a symlink) when path resolution
   misbehaves.
2. **Unverifiable self-reporting.** Compliance facts the tooling already observes — whether the
   RED test really failed, which files changed, whether a test was weakened — are re-narrated by
   the agent in prose after the fact.
3. **Premature termination.** Long autonomous runs stop mid-plan, because control flow lives in
   two prose documents that disagree, and because there is no sanctioned transition for the
   irregular cases that occur routinely.
4. **No comparable record.** There is no way to compare models, or to measure whether a change
   to the planning process improved anything, because nothing durable and structured is kept.

Appendix A lists the specific incidents that motivate individual requirements.

## 2. Goals

- **G1.** Process state is *derived from observed test execution*, never asserted by the agent.
- **G2.** A plan spanning multiple projects and languages executes as one run.
- **G3.** Every fact the tool can observe is recorded automatically; agents contribute only judgement.
- **G4.** An autonomous run has exactly one source of truth for what to do next.
- **G5.** A run survives agent death and resumes without loss.
- **G6.** Accumulated runs support comparison across models, agents and planning methods.

## 3. Non-goals

- Not a CI system, test runner, or build tool. It orchestrates existing per-project runners.
- Not a code generator or auto-fixer. It never edits source.
- Not a web application. No UI in v1 (see §14).
- Not a general workflow engine. It implements one process: RED → GREEN → REFACTOR.

## 4. Design principles

**P1 — Derived, not asserted.** No command accepts a phase as input. Phases are computed from
test results. There is no way for a caller to declare that it is in a given state.

**P2 — Measure, don't block.** Except where a check is unambiguous, deviations are *recorded*
as typed events, not prevented. Prevention rules with edge cases produce false denials, and a
blocked agent improvises — which is the original problem. Enforcement is reserved for cases with
no legitimate exception (§12).

**P3 — The contract is a baseline, not a gate.** Plans are frequently wrong about their own
scope, and discovering that is a valuable output. Divergence from the declared plan is recorded
as a plan defect and never fails a run.

**P4 — Observation over cooperation.** Prefer facts obtainable without the agent's help (git
diffs, test collection sets, process exit codes) over facts that require the agent to be honest.

**P5 — Explicit over inferred.** Project roots, artifact dependencies and plan scope are declared
in configuration, never discovered by scanning the filesystem.

---

## 5. Domain model

```
PlanContract  1 ── n  Run  1 ── n  Cycle  1 ── n  Invocation
                                     │
                                     ├── n  Annotation
                                     ├── n  IntegrityEvent
                                     ├── n  SensitivityCheck
                                     └── 0..1 Blocker
```

### PlanContract
The declared scope of a plan, captured once and immutable thereafter.

| Field | Notes |
|---|---|
| `id` | |
| `plan_path` | repo-relative |
| `git_blob_sha` | hash of the plan **as committed**, not as found in the working tree |
| `git_commit` | commit the blob was read from |
| `declared_cycles` | ordered list: ordinal, title, project, declared test id(s), authorised test modifications, declared file blast radius |
| `registered_at` | |

Registering the same plan at a different blob SHA creates a **new** contract. Contracts are never
edited.

### Run
One execution of one contract by one executor.

| Field | Notes |
|---|---|
| `id`, `plan_contract_id` | |
| `executor_model`, `executor_session` | **resolved by the tool, never accepted as an argument** (§5.1) |
| `worktree_path` | runs are scoped to a worktree, not a repo |
| `started_at`, `ended_at`, `outcome` | `complete` / `blocked` / `abandoned` |

Many runs may reference one contract. This is what makes A/B comparison across models possible.

#### 5.1 Resolving executor identity

The harness exposes a session identifier but **not** the model. Resolution order:

1. `CLAUDE_CODE_SESSION_ID` from the environment → locate
   `~/.claude/projects/<slug>/<session-id>.jsonl` → read the `model` field.
2. Failing that, a `--executor` label supplied by a **human** at `run start`.
3. Failing that, `unknown`, and the run is excluded from model-comparison metrics.

- **R5.1** The transcript lookup is isolated behind a single resolver so an undocumented format
  change breaks one function, not the tool.
- **R5.2** Agents never supply executor identity by any path. Step 2 is a human affordance.
- **R5.3** Resolution requires the tool to run on the same host as the agent. Remote or CI
  execution falls through to step 2.

### Cycle
| Field | Notes |
|---|---|
| `id`, `run_id`, `ordinal` | |
| `projects` | the set of registered projects this cycle targets; exactly one except for contract cycles (§9.3) |
| `declared_test` / `target_tests` | normally one; a set only for contract cycles (§9.3) |
| `phase` | `AWAITING_TEST` / `AWAITING_IMPL` / `AWAITING_REFACTOR` / `CLOSED` / `SKIPPED` |
| `opened_at`, `closed_at` | |
| `head_at_open` | git SHA, for diffing the cycle's changes |

### Invocation
One execution of one project's test suite. **Never overwritten; append-only.**

| Field | Notes |
|---|---|
| `id`, `cycle_id`, `phase_at_invocation`, `project`, `adapter` | |
| `target_test`, `target_outcome` | `passed` / `failed` / `not_collected` / `not_found` |
| `target_failure_excerpt` | truncated |
| `total_passed`, `total_failed` | |
| `other_failures` | after baseline subtraction (§9.2) |
| `lint_outcome`, `typecheck_outcome` | per §9.4 |
| `duration_ms`, `started_at` | |

Invocation count per cycle is `COUNT(*)`, segmented by phase — never a stored counter.

### Annotation
Free-form agent judgement, keyed, plus arbitrary keys the plan declares for itself (R7.5).

Reserved per-cycle keys: `plan_defect`, `friction_note`, `red_expectation`,
`commit_shape_deviation`, `test_setup_smell`, `unplanned_change`, `new_work_raised`.

Reserved per-run keys: `plan_quality_score` (per plan phase, with rationale), `census_on_entry`,
`census_on_exit`.

- **R5.4** These keys are drawn from the fields agents already invent unprompted in hand-written
  friction logs. Reserving them makes the summary a projection rather than a composition.
- **R5.5** `plan_quality_score` is subjective and self-reported. It is retained because it is a
  direct signal on the planning process, and reported as an agent opinion, never as an observation.

### IntegrityEvent
Typed: `test_removed`, `test_weakened`, `undeclared_file_touched`, `restore_mismatch`,
`off_protocol_invocation`, `stale_artifact`, `plan_blob_changed`.

### Blocker
Typed: `regression`, `target_unfixable`, `bad_red`, `plan_defect`, `tooling`, `context_exhausted`,
`pre_existing_failure`.

`pre_existing_failure` is failing-but-not-caused-here: a flake, or something the baseline missed.
Without it the only available label is `regression`, which records a defect the run introduced —
so the agent must either misreport its own work or leave the failure unfiled.

---

## 6. State machine

Two cycle kinds. Every transition is the consequence of an observed suite run.

### 6.1 Standard cycle — three phases

```
AWAITING_TEST ──advance──▶ AWAITING_IMPL ──advance──▶ AWAITING_REFACTOR ──advance──▶ CLOSED
      ▲                          │                            │                        │
      └────── skip / next cycle ─┴────────────────────────────┴────────────────────────┘
```

| Phase | Agent's job | `advance` passes when |
|---|---|---|
| `AWAITING_TEST` | write exactly one failing test | target **fails**, no new failures elsewhere |
| `AWAITING_IMPL` | write the minimum implementation | target **passes**, no new failures elsewhere |
| `AWAITING_REFACTOR` | refactor, or nothing | lint/typecheck clean and the close sweep green (R9.2). The cycle's own suites are **skipped** when the tree hash is unchanged since the GREEN commit — they just passed on an identical tree. The downstream sweep always runs, having not run yet. |

Outcomes that are not simple advancement:

- **Target passes in `AWAITING_TEST`** → not an error. Phase holds; `next_action` directs a
  sensitivity check (§8.4). Recorded as `red_first_violation` for metrics.
- **Target not collected** (import error, missing module) → distinguished from `not_found`
  (identifier matches nothing). Not-collected is a legitimate RED in `AWAITING_TEST` if the plan
  declares a stub step; otherwise `next_action` directs stub creation. Never routes to a human.
- **New failures elsewhere** → phase holds, `next_action` names the regressed tests.
- **Nothing changed since the last invocation** → refused with `no_change_since_last_run`, to stop
  loops that re-run an unmodified tree. `tdd advance --retry` proceeds anyway: re-running a suite
  is legitimate (flaky tests, environmental failures). Retries are counted, and after three
  consecutive retries with no tree change `next_action` escalates toward a blocker. "Changed" is
  the hash of tracked files under the cycle's project roots.

There is no phase for "state unknown". If the ledger has no open cycle, `status` says so.

### 6.2 Pin cycle — characterisation before refactor

Declared `pin_cycle: true`. Used when existing behaviour must be pinned by a test *before* the
code producing it is deleted or restructured. There is no RED: the test must pass on arrival, by
design.

```
AWAITING_PIN ──advance──▶ SENSITIVITY_REQUIRED ──advance──▶ AWAITING_REFACTOR ──advance──▶ CLOSED
```

| Phase | Agent's job | `advance` passes when |
|---|---|---|
| `AWAITING_PIN` | write a test asserting current behaviour | target **passes**, no failures elsewhere |
| `SENSITIVITY_REQUIRED` | mutate the behaviour under test | §8.4 completes: target fails under mutation, restore verified byte-identical |
| `AWAITING_REFACTOR` | perform the planned refactor | close sweep green (R9.2) |

- **R6.1** A pin cycle's sensitivity check is **mandatory**, not discretionary. A characterisation
  test that has never been shown to fail pins nothing.
- **R6.2** Pin cycles are **excluded** from the RED-first violation metric. Passing on arrival is
  their defined behaviour, not a discipline failure.
- **R6.3** Rationale: in the motivating run, 9 of 17 cycles passed on arrival, 5 of them declared
  refactor-preparation pins. Without a distinct kind, the most diagnostic metric in §11 is
  unusable on any refactoring plan — and refactoring plans are a large share of real work.
- **R6.4** A standard cycle whose test passes on arrival is still a violation, still requires a
  sensitivity check, and is **not** silently reclassified as a pin. The kind is declared by the
  plan in advance, never inferred from the outcome.
- **R6.5** It nonetheless routes through `SENSITIVITY_REQUIRED`, exactly as a pin does — the
  violation is recorded once, on entry. A demand the phase does not follow is a livelock: the
  verified check is only ever read on leaving `SENSITIVITY_REQUIRED`, so a cycle that demands
  one while remaining in `AWAITING_TEST` re-demands it for as long as the agent keeps obeying.

---

## 7. Configuration

### 7.1 Project registry — `tdd.toml` at the worktree root

```toml
[project.backend]
root       = "backend"
adapter    = "pytest"
test_paths = ["tests/"]
lint       = ["ruff check", "ruff format --check"]
typecheck  = ["mypy ."]

[project.frontend]
root       = "frontend"
adapter    = "vitest"
test_paths = ["**/__tests__/**", "**/*.test.ts", "**/*.test.tsx"]
lint       = ["eslint ."]
typecheck  = ["tsc --noEmit"]

[project.e2e]
root    = "frontend"
adapter = "detox"
in_close_sweep = false          # too slow per cycle; runs at plan completion

# Tests the default command cannot reach — contract tests needing a live backend
# being the motivating case — declare the alternate command per pattern (R7.13).
[[project.frontend.override]]
pattern         = "src/__contract__/"
test_command    = "npx vitest run --config vitest.contract.config.ts"
collect_command = "npx vitest list --config vitest.contract.config.ts"
env             = { API_URL = "http://localhost:${API_PORT}" }

# Artifacts chain. `codegen` is a generator tool, not a project: it is never a
# cycle target, has no tests, and its output is owned by the artifact edge.
[artifact.openapi]
path        = "schema/openapi.json"
produced_by = "backend"
regenerate  = "uv run python -m app.export_openapi"
consumed_by = ["frontend"]

[artifact.api_client]
path        = "frontend/generated"
produced_by = "artifact.openapi"          # chained: upstream is another artifact
regenerate  = "npm --prefix codegen run generate"
check       = "npm --prefix codegen run check"
consumed_by = ["frontend"]
generated   = true                        # excluded from authorship accounting
```

Requirements:

- **R7.1** Project roots are declared. The tool never infers a root by scanning for marker files.
- **R7.2** A repo may register any number of projects, including several in the same language.
- **R7.3** Artifact edges declare producer, consumers and a regeneration command. These edges also
  determine close-sweep scope (R9.2).
- **R7.4** `test_paths` classifies files for staging (R9.13) and must be declared per project.
- **R7.5** Artifacts chain: an artifact's `produced_by` may name another artifact. Staleness
  propagates downstream through the chain.
- **R7.6** A `check` command, where declared, is preferred over regenerate-and-diff for staleness
  detection.
- **R7.7** Paths under a `generated = true` artifact are **excluded from authorship accounting**:
  never counted as `undeclared_file_touched` (R9.16), never counted toward blast-radius
  divergence, never subject to stub analysis. They are staged by the tool as part of a
  regeneration step, not attributed to the agent.
- **R7.8** Generator tools that are not hand-edited during TDD — `codegen` being the motivating
  case — are modelled as artifact regeneration commands, never as projects.
- **R7.12** A project declares its own suite command (`test_command`, and `collect_command` for
  collection). Adapters append only reporting flags: parallelism, plugins and markers stay
  exactly as the project declared, so the suite under TDD is the suite the team trusts.
- **R7.13** A project may declare **per-pattern suite overrides**: an alternate `test_command`
  (plus optional `collect_command` and `env`) for files matching a root-relative pattern.
  Collection and suite runs union the default suite with every override suite, so a cycle can
  target a test only an alternate runner config reaches — without widening the default config,
  which breaks the suite CI runs and pollutes target adoption (R8.9) with the other suite's
  tests. Override patterns classify their files as tests (R7.4) without being repeated in
  `test_paths`; first declared match wins; `env` values may reference `${VAR}`, expanded at
  invocation. A suite that produces no report fails the run loudly — a silent gap would
  resolve a target in that suite as `not_found`.

### 7.2 Plan front-matter

The plan file carries its own contract, so the planning agent needs no integration with this tool:

```yaml
---
tdd_plan: one-exception-status-table
cycles:
  - n: 1
    project: backend
    test: "tests/evidence/test_exception_map.py::test_unmapped_exception_is_not_swallowed"
    stub_expected: ["app/exception_map.py"]
    files: ["app/exception_map.py"]
    commit_red: "test: unmapped exception is not swallowed"
    commit_green: "feat: domain exception map skeleton"
  - n: 4
    project: backend
    test: "tests/routers/test_children_router.py::test_close_nonexistent_arrangement_returns_403"
    modifies_tests: ["tests/blackbox/test_input_validation.py::test_close_..._returns_404"]
    files: ["app/routers/children.py"]
  - n: 12
    project: frontend
    contract_cycle: true
    tests:
      - "frontend/services/__tests__/imageMessages.test.ts > upload matches contract"
      - "backend/tests/test_openapi.py::test_upload_body_schema"
  - n: 15
    project: backend
    pin_cycle: true              # characterisation before deletion; passes on arrival by design
    test: "tests/routers/test_signing_keys.py::test_enrol_maps_invalid_box_key_signature_to_422"
    files: ["app/routers/signing_keys.py"]
annotation_keys: ["literal_detail_handlers_kept"]
---
```

- **R7.4** `modifies_tests` authorises changes to named existing tests, suppressing the
  test-weakening integrity event for exactly those.
- **R7.5** `annotation_keys` lets a plan define its own judgement fields, which `log render`
  emits per cycle.
- **R7.9** **Absent** front-matter is legitimate (pre-existing plans, exploratory work). The
  contract is recorded as `undeclared`, plan-fidelity metrics are unavailable, and `run start`
  requires a human-supplied `--allow-undeclared`.
- **R7.10** **Malformed** front-matter hard-fails at `tdd plan register`. A contract that does not
  parse is almost always a defect in the planning skill, and that signal must surface rather than
  degrade silently into a metrics-free run. This does not conflict with P3, which governs
  divergence *during* a run, not whether a contract parses.
- **R7.11** Editing front-matter mid-run changes the plan blob and raises `plan_blob_changed`,
  which is the backstop against escaping a contract by corrupting it.

---

## 8. CLI surface

Every command emits JSON on stdout with a common envelope:

```json
{
  "ok": true,
  "run": {"id": "...", "cycle": 8, "of": 13, "phase": "AWAITING_IMPL", "project": "backend"},
  "result": { },
  "next_action": {
    "verb": "write_implementation",
    "detail": "Write the minimum code to pass tests/...::test_x, then run `tdd advance`.",
    "terminal": false
  }
}
```

- **R8.1** `next_action` is the single authority on control flow. Skill documents describe *how*
  to do the work and must not contain stopping instructions.
- **R8.2** `terminal: true` appears only on genuine completion or an unrecoverable blocker.
- **R8.3** No command accepts a phase, cycle number or executor identity as an argument.

**R8.3a — `verb` is a closed, versioned enum.** Skills and hooks dispatch on `verb`; `detail` is
human-readable and explicitly non-authoritative. Adding a verb is a specification change.

```
write_test          write_implementation      create_stub
fix_regression      run_sensitivity_check     name_target_test
refactor_or_advance confirm_cycle_applicable  annotate_cycle
resolve_blocker     await_baseline            complete (terminal)
blocked (terminal)
```

Any situation the tool cannot express with one of these verbs is a gap in the state machine.
Surfacing it as a specification change — rather than as prose in a skill — is the point of
closing the set.

**R8.4 — progress and timing go to stderr as NDJSON, never stdout.** stdout carries the envelope
above; a consumer does `json.loads(stdout)` and NDJSON in front of it breaks every one. Two
streams of events use it:

| Event | When | Fields |
|---|---|---|
| `baseline_captured` | after each project's baseline (§8.2) | `project`, `test_count`, `elapsed_s`, `run_s`, `collect_s` |
| `command_timing` | per subprocess, only under `TDD_TIMING=1` | `label`, `command`, `cwd`, `duration_ms`, `exit_code` |

`run_s` and `collect_s` are reported separately because their cost models are unrelated — a suite
run scales with tests, per-file collection (R10.3) with *files* — so a single total cannot say
which one was slow, and answering that question otherwise means measuring the projects by hand
outside the tool. `elapsed_s` remains the total.

`command_timing` is off by default: the per-file collect loop emits one line per test file, which
would drown the heartbeats that exist to make a slow baseline legible. Its `label` (`suite`,
`collect`, `gate`, `doctor`) is what makes the rows groupable — `run_command` sees a command and a
cwd, not which project or phase asked for it. `doctor` covers all three of preflight's probe
sites: the reporter check in `cmd_doctor`, plus `collectable()` and `override_isolation()`, which
are called from nowhere else. An unlabelled row is a third-party adapter's; every built-in call
site names itself.

**`verb_set_version: 2`** — added `await_baseline` (issue #2): a baseline can take minutes on a
real project (R10.3/R10.4's per-file collection), and a polling agent that inherited a run it did
not start had no verb telling it to wait rather than re-run. `await_baseline` is non-terminal;
`tdd progress` and `tdd status` emit it while a `baseline_claim` is open and no run row exists yet
(§8.3).

### 8.1 Setup
| Command | Behaviour |
|---|---|
| `tdd init` | scaffold `tdd.toml` from detected projects, for human review |
| `tdd doctor` | preflight: registry valid, adapters runnable, reporters installed, worktree resolvable, no stale report artifacts, tree clean enough. `ok` mirrors `healthy` (cycle 17) — a failing check is a non-zero exit, not `ok: true` with `healthy: false` buried in `result` |

**"Clean enough"** is scoped, not absolute: `worktree clean` fails only on dirt a run
would read — a declared project root, a declared artifact path, or `tdd.toml` — with
`config.is_ignored` excluding build residue (including the `.venv`/`node_modules`
doctor's own probes write). Dirt anywhere else is named in the passing check's
`detail` and left alone. Absolute cleanliness blocked agents on unrelated notes and
editor settings.

**Every failing check carries a `detail` naming what to fix**, enforced by the
recorder rather than by each call site. A blocker with an empty `detail` is
unfalsifiable — `resolve_blocker` with nothing to resolve — and an agent that meets
one has no move left but to re-run doctor and read the same output again.

### 8.2 Registration
| Command | Behaviour |
|---|---|
| `tdd plan register <path>` | parse front-matter, resolve plan blob at HEAD, store contract |
| `tdd run start --plan <path\|id>` | create run; capture executor identity from environment; capture per-project baselines; verify artifact freshness; open cycle 1 |

### 8.3 The loop
| Command | Behaviour |
|---|---|
| `tdd status` | current position and `next_action`; safe to call any time |
| `tdd advance` | run the relevant suite(s), record an Invocation, compute the transition, emit `next_action`. **The only command that changes phase.** |
| `tdd cycle skip --reason <text>` | mark the current cycle `SKIPPED` with a mandatory reason; open the next. Sanctioned path for cycles the plan got wrong |
| `tdd annotate --key <k> --value <v>` | attach agent judgement to the current cycle |
| `tdd blocker --kind <k> --detail <text>` | record a typed blocker; set run `outcome = blocked`, releasing the stop hook (H1) |
| `tdd resume` | reconstruct position from the ledger and emit `next_action` |
| `tdd resume --unblock --note <text>` | **human only.** Reopen a blocked run, recording a `human_intervention` event with the note |

- **R8.7** A blocked run is not live. H1 must permit the agent to stop, or a blocker traps it.
- **R8.8** `human_intervention` events are the input to interventions-per-run, the primary
  autonomy metric.
- **R8.9** In `AWAITING_TEST`, `advance` resolves the target by diffing `collect()` against cycle
  open. If exactly one new test appeared and it fails, it is adopted as the target and
  `declared_test_mismatch` is recorded against the contract. If several appeared, that is the
  one-behaviour-per-cycle violation: it is recorded, and `next_action` requires the agent to name
  the intended target rather than guessing.

### 8.4 Sensitivity checks

For the passed-on-arrival case, which occurred in 4 of 8 executed cycles in the motivating run.

| Command | Behaviour |
|---|---|
| `tdd sensitivity begin` | record `git diff` and the untracked-file set as the reference state |
| `tdd sensitivity check` | run the suite with the agent's mutation in place; require the target to now fail; record the mutation diff and the observed failure |
| `tdd sensitivity end` | `git checkout --` the mutated tracked paths, then assert the resulting `git diff` is byte-identical to the reference; emit `restore_mismatch` on any difference |

- **R8.4** A cycle that passed on arrival cannot reach `CLOSED` without a completed sensitivity
  check or an explicit annotated waiver.
- **R8.5** The reference state is a recorded diff, not a stash. At a passed-on-arrival the RED test
  is written but uncommitted, so the tree is legitimately dirty; restoration must return to *that*
  state, never to HEAD, and must never touch the uncommitted test.
- **R8.6** Commits are refused while a sensitivity check is open (R9.19).

### 8.5 Reporting
| Command | Behaviour |
|---|---|
| `tdd log render [--format md]` | project the ledger into a friction-log document |
| `tdd metrics <query>` | §11 |
| `tdd verify` | re-run integrity checks over a completed run |

---

## 9. Execution semantics

### 9.1 Regression scope
- **R9.1** During `AWAITING_TEST` and `AWAITING_IMPL`, the suites of the **union of projects named
  by the cycle's targets** run. For an ordinary cycle that is one project; for a contract cycle
  (§9.3) it is all projects the cycle spans.
- **R9.2** On the transition out of `AWAITING_REFACTOR`, the close sweep runs: the cycle's own
  projects, plus every project **downstream of an artifact the cycle modified** per the
  `consumed_by` edges in §7.1, plus lint and typecheck for each. Projects with
  `in_close_sweep = false` are always excluded.
- **R9.3** A **full sweep** — every registered project, lint and typecheck, including
  `in_close_sweep = false` suites — runs once at plan completion.
- **R9.4** Rationale: a per-cycle sweep of all four projects with `mypy` and `tsc` costs minutes,
  which the inner loop cannot absorb. The declared artifact graph identifies which projects a
  cycle could plausibly have broken without running anything.

### 9.2 Baselines
- **R9.5** `run start` records the set of already-failing tests per project.
- **R9.5a** A baseline that observed nothing is refused, not recorded: a project whose files
  all failed to collect, or whose baseline run executed no tests despite collection finding
  some. Because R9.6 subtracts the baseline from every later failure set, an empty one that
  merely looks clean is worse than no run at all — every pre-existing failure reads as a
  regression, at every close sweep, for the life of the run. The check runs before the run row
  is written, so a refusal leaves nothing behind to block the next attempt. A project with no
  test files and no collection errors is not an error; it simply has no suite yet.
- **R9.5b** `resume --unblock --accept-failures` folds the failures the last close sweep saw into
  the baseline, recorded as `baseline_amended` alongside the mandatory `--note`. A run whose
  baseline missed a failure cannot otherwise recover: unblocking returns it to the phase it
  blocked in, and the next sweep finds the same failure and blocks again. The flag is explicit
  and human-only precisely because it launders a failure into the accepted set — an unblock must
  never do it silently. If a close sweep reached a project that was never baselined, `--accept-failures`
  inserts a fresh baseline row for it rather than skipping it.
- **R9.5c** `run start` scopes baseline capture to plan-reachable projects. The reachable set is
  the union of declared cycle projects plus the transitive `consumed_by` closure of artifacts
  whose root producer is in that set (respecting `in_close_sweep = false` on closure-added
  consumers). Projects outside the reachable set are never run during the plan, so there is no
  later failure set to subtract their baseline from. The scoping is recorded as a
  `baseline_scoped` integrity event listing the skipped projects. Pass `--baseline-all` to probe
  every project and suppress the event.
- **R9.5d** When a close sweep reaches a project with no baseline row (because an edit fell
  outside the predicted reachable set, pulling an un-baselined consumer into the sweep), its
  failures are classified as `unattributable` — there is no baseline to subtract, so they cannot
  be labelled regressions. The advance reply is `resolve_blocker` with kind
  `no_baseline_for_project`, directing the agent to file the blocker and recover via
  `resume --unblock --accept-failures`, which inserts the missing baseline row.
- **R9.6** Baseline failures are subtracted from `other_failures` in every subsequent invocation.
- **R9.7** A baseline failure that starts passing is recorded, not ignored.

### 9.3 Contract cycles
- **R9.8** A cycle may declare multiple target tests, spanning multiple projects, **only** if the
  plan marks it `contract_cycle: true`.
- **R9.9** All targets must fail together to leave `AWAITING_TEST`, and pass together to leave
  `AWAITING_IMPL`. Per R9.1 the inner loop runs every project the targets span.
- **R9.10** This exists for breaking contract changes, where no intermediate green state exists.
  Additive changes must be expressed as ordinary sequential cycles.

### 9.4 Lint, typecheck and artifacts
- **R9.11** Lint and typecheck results are part of the close-sweep verdict, surfaced alongside
  test failures rather than discovered later at commit time.
- **R9.12** Before a run starts and at every cycle close, declared artifacts are checked for
  staleness against their producer. A stale artifact emits `stale_artifact` and blocks the close
  until regenerated — this is one of the few hard gates (§12), because a stale contract produces
  a *green* wrong answer.

### 9.5 Staging and commits

The CLI stages; it never delegates staging to the agent, and it never runs `git add -A`.

- **R9.13** The staged set is derived from the phase being left:
  - **RED commit** — files matching the project's declared `test_paths`, plus files the cycle
    declared under `stub_expected`.
  - **GREEN commit** — all other modified files within the cycle's project roots, since the RED
    commit.
  - **REFACTOR commit** — as GREEN; skipped without error if nothing changed.
- **R9.14** If the RED commit's staged set would contain a file that is neither a test nor a
  declared stub, that is the "implementation written during RED" violation. It is detected here,
  exactly, in both languages, with no source parsing.
- **R9.14a** A file created in answer to the tool's own `create_stub` directive is exempt from
  R9.14 and joins the RED commit as a stub, recorded as `stub_adopted`. The exemption is narrow:
  it applies only in the cycle where the directive was issued, and only to paths absent from
  HEAD — an uncollectable import is answered by a module that did not exist, so a change to an
  existing file remains implementation. Without this, an undeclared `stub_expected` makes the
  tool instruct the agent and then convict it for complying, and an alarm that fires on correct
  work is one that gets ignored.
- **R9.15** Nothing outside a registered project root is ever staged. Plan files, friction logs
  and repository documentation are committed separately, at plan completion. Paths the agent
  supplies for these — `log render --out` — are resolved from the worktree root, never the
  current directory, which is wherever the agent happened to be standing.
- **R9.16** Files modified inside a project root matching neither classification are left
  unstaged and recorded as `undeclared_file_touched`, and named in `next_action`. Per P2 this
  does not block.
- **R9.17** Commit messages come from the plan front-matter where declared, falling back to a
  `--message` argument. Plans already specify them; this places them under plan review.
- **R9.18** Ordering within `advance` is: run suites → verdict → stage → commit → record
  transition. A failed commit means no transition, so the ledger cannot record progress that is
  absent from git.
- **R9.19** Committing is refused while a sensitivity check is open (§8.4).
- **R9.20** When an artifact is stale, the **tool** runs its declared `regenerate` command; the
  agent is informed, not asked. The regenerated paths are staged and committed **separately** from
  the GREEN commit, as `chore(<artifact>): regenerate`, and an `artifact_regenerated` event is
  recorded. Hand-written and generated changes stay independently reviewable, which matters most
  on exactly the contract cycles that touch both.
- **R9.21** `run start` refuses a dirty working tree unless `--allow-dirty` is given. When allowed,
  the pre-existing modified and untracked set is recorded and permanently excluded from authorship
  attribution, so pre-existing edits are never absorbed into the first cycle's commits.
- **R9.22** A run has **at most one open cycle row** at any time. `open_cycle` returns the existing
  open row for an ordinal rather than inserting a duplicate; `close_cycle` re-reads `closed_at` and
  no-ops if the row is already closed (returning the currently-open cycle so the caller can reply
  with the run's real position).
- **R9.23** `advance` is **single-flight per worktree**. Before dispatching to the advance handler,
  the command acquires a per-worktree `advance_claim`. A second concurrent `advance` is refused with
  `ok: false` and `reason: "advance_in_flight"`. A claim held by a dead pid is reclaimed before the
  new claim is inserted. The claim is released in a `finally` so a raising handler cannot leave the
  worktree wedged.

### 9.5 Test identity
- **R9.12** Test ids are namespaced by project: `backend::tests/x.py::test_y`,
  `frontend::path/f.test.ts > full name`.
- **R9.13** Adapters normalise their runner's quirks (parametrisation suffixes, async markers,
  path relativity) so ids are stable across invocations.

---

## 10. Adapter interface

```
Adapter.run(project, target_test | None) -> Verdict
Adapter.collect(project)                 -> set[test_id]
Adapter.collectable(project)             -> GateResult
Adapter.lint(project)                    -> GateResult
Adapter.typecheck(project)               -> GateResult
```

- **R10.1** `pytest` and `vitest` adapters ship in v1; `detox`/Playwright is a v2 adapter.
- **R10.2** Adapters own runner-specific failure modes: pytest collection errors must be reported
  as `not_collected` and never conflated with an unmatched identifier; vitest's non-JSON stdout
  preamble must be handled.
- **R10.3** `collect()` runs **one invocation per declared suite** (the default plus each
  override), then the **per-file loop for every file no batch accounted for** — whether the batch
  failed, returned nothing, or never mentioned that file. The guarantee is unchanged: a file that
  fails to collect yields `collect_failed` for that file alone, and every other file still
  contributes its test ids. Both pytest and vitest support single-file targeting, which is what
  makes the fallback possible.
- **R10.3a** The two paths do not discover alike: a batch uses the runner's own config, the loop
  walks `test_paths`. Reconciling them — per-file for anything the batch did not report — is what
  keeps the collected set from silently shrinking when a declared file is outside the runner's
  discovery. A quietly smaller baseline is worse than a slow one.
- **R10.4** Rationale: `collect()` is load-bearing for target adoption (R8.9), test-weakening
  detection and the one-behaviour check — and in `AWAITING_TEST` the tree frequently does not
  import, which is exactly what `stub_expected` describes. Whole-suite collection fails precisely
  in the phase that depends on it, which is why the per-file loop remains the fallback rather than
  being replaced. The cost is asymmetric on purpose: a healthy project pays one invocation instead
  of one per file (measured 38.8x on 60 files; 77% of a real `run start` was per-file collection,
  issue #27), while a non-importing tree pays one failed probe on top of the loop it would have
  run anyway.
- **R10.5** Where per-file collection still yields nothing usable, the tool falls back to the
  contract's declared test id and records the degradation.
- **R10.6** Adding an adapter requires no change to core logic.
- **R10.7** `collectable()` is a single **whole-suite** `--collect-only` (pytest) / `vitest list`
  (vitest) probe used only by `tdd doctor` (§8.1, issues #3/#5). `collect()` now opens with the
  same *shape* (R10.3) but remains a distinct path: `collectable()` reports whether a suite can be
  enumerated at all, and never substitutes for the fallback loop that attributes a failure to the
  file it came from. `tdd doctor` reads the subprocess's **stdout**: `uv` writes
  environment warnings (e.g. `VIRTUAL_ENV=... does not match ...`) to stderr, while pytest writes
  the actual collection error (e.g. `ModuleNotFoundError`) to stdout. A check that reads stderr
  reports the wrapper's noise and loses the real error underneath it.

---

## 11. Observed facts and metrics

### 11.1 Captured without agent cooperation
| Fact | Source |
|---|---|
| RED-first violation | invocation verdict in `AWAITING_TEST` |
| Implementation attempts | `COUNT(invocation)` where phase = `AWAITING_IMPL` |
| Convergence vs thrash | trajectory of `other_failures` across attempts in a cycle |
| Implementation written during RED | staged-set classification at the RED commit (R9.14) — exact, both languages |
| Stub-only *content* during RED | Python: `ast` check that added function bodies are sentinels. TypeScript: line-count heuristic only. **The metric is labelled partial for TS rather than reported as uniform.** Secondary to R9.14 |
| Tests removed or weakened | `collect()` set diff + assertion-count diff, minus `modifies_tests` |
| Files outside declared blast radius | `git diff --name-only` vs contract |
| Commits per cycle | commit trailers (§13.3) |
| Suite duration, wall clock, cost | invocation records |
| Plan fidelity | declared vs executed cycles and tests |

### 11.2 Contributed by the agent
`plan_defect`, `friction_note`, sensitivity reasoning, plan-declared annotation keys.

### 11.3 Queries the system must answer
- Attempts-per-cycle distribution, by model, by project.
- RED-first violation rate, by model and by plan — **standard cycles only** (R6.2).
- Cycles declared vs delivered, by plan — the score for the planning process.
- Blocker rate by type, by model.
- Cost and wall clock per cycle, by model and project.
- Frontend vs backend cycle performance for the same executor.

**R11.1** Cross-plan aggregates must be labelled as non-comparable. Cycle difficulty varies too
much for them to mean anything. Model comparison is only valid across **runs of the same
contract** (§13.4).

---

## 12. Enforcement boundary

The CLI cannot compel an agent. Only the harness can. The division:

**Hard gates inside the CLI** (no legitimate exception):
- Phase cannot be set by a caller.
- A cycle cannot close with a stale declared artifact.
- A cycle that passed on arrival cannot close without a sensitivity check or waiver.
- `advance` refuses when nothing changed since the previous invocation.

**Recorded, never blocked** (per P2): non-stub writes during RED, undeclared file touches,
scope divergence, test modifications, extra attempts.

**Delegated to harness hooks** (specified here, implemented by the consumer):
- **H1 — Stop hook.** On agent stop, query `tdd status`; if the run is live, block and return
  `next_action`. This is the enforcement for premature termination, and it has no false-positive
  risk because "is this run complete" is unambiguous.
- **H2 — Bash hook.** Redirect bare `pytest` / `vitest` invocations through `tdd advance`, so
  off-protocol runs are visible rather than silent.
- **H3 — Write hook (optional).** Deny writes to the ledger. Not required if the ledger lives
  outside the worktree (§13.2).

**R12.1** The CLI must expose everything H1–H3 need as machine-readable output, and must not
depend on any of them being installed.

---

## 13. Architecture

### 13.1 Storage
- **R13.1** SQLite, single file, append-only for invocations and events.
- **R13.2** Schema versioned and migrated. The schema is the long-lived asset; the transport is not.
  Current schema version: **3** (v3 adds the `advance_claim` table, R9.23).

### 13.2 Location
- **R13.3** **One ledger per repository**, in a per-user data directory keyed by the repository's
  canonical path (the common git dir, not the worktree). It is never a file inside the repo, never
  resolved relative to the process's current directory, and never committed.
- **R13.4** `Run.worktree_path` provides isolation. Concurrent runs in separate worktrees are
  isolated by run scoping, not by separate files; SQLite WAL covers the write volume involved.
- **R13.5** Rationale: keying by worktree path orphans a run's entire history when the worktree is
  pruned — a live condition in the motivating repository. A repo-level ledger also makes
  cross-worktree metrics a `GROUP BY` rather than a merge.

### 13.3 Git integration
- **R13.6** Commits made during a run carry `TDD-Run`, `TDD-Cycle` and `TDD-Phase` trailers.
- **R13.7** The tool creates the commits (§9.5). Agents do not stage and do not commit. This makes
  commit-to-cycle linkage an observation rather than a claim, per P4, and lets the tool refuse to
  close a cycle over uncommitted work.

### 13.4 Interface evolution
- **R13.7** v1 is a local CLI over SQLite. No daemon, no HTTP.
- **R13.8** The command surface must be transport-agnostic so a later daemon exposes the same
  verbs over HTTP without changing agent-facing behaviour. Concurrency across worktrees is the
  trigger for that move, not a milestone in itself.

### 13.5 Implementation
- **R13.9** Single self-contained executable, installable independently of any project it manages.
  Python is the pragmatic choice given both adapters shell out and the primary consumer repo is
  Python-led; the choice is not load-bearing.

---

## 14. Out of scope for v1

Web UI or dashboard. HTTP/daemon mode. Auto-fix or auto-revert on blocker. Cross-plan benchmark
orchestration (the *data model* must support it; the runner need not). Non-TDD workflows.
IDE integration. Multi-repo runs.

---

## 15. Phasing

| Phase | Contents | Unlocks |
|---|---|---|
| **1 — Ledger and loop** | registry, contract registration, run/cycle/invocation model, pytest + vitest adapters, three-phase machine, `advance`/`status`/`resume`, `next_action` | replaces the predecessor (§1); state corruption and premature stopping addressed |
| **2 — Fidelity** | baselines, collect-diff weakening detection, blast-radius diffing, `cycle skip`, `sensitivity`, artifact freshness, typed blockers | the self-reporting problem addressed |
| **3 — Record** | annotations, `log render`, commit trailers, lint/typecheck gates in the close sweep | friction logs become a projection |
| **4 — Evaluation** | metrics queries, cost capture, same-contract comparison | model and planning-process evaluation |

Phase 1 is the prerequisite for everything. Phases 2 and 3 are independently useful and can be
reordered. Phase 4 is worthless without a set of stable benchmark contracts to run repeatedly —
producing those is a separate exercise and the real gate on evaluation. The ledger starts
empty — records from outside it are never imported.

---

## 16. Impact on the skill layer

The tool does not run agents; an agent drives it through a skill. The one skill it
requires — execution: respond to each `next_action` verb — is specified in
[`harness-integration.md`](./harness-integration.md), with a reference implementation
in [`examples/skills/tdd-drive/`](../examples/skills/tdd-drive/). The skill retains
only what the CLI cannot supply: craft guidance — how to write one good failing test,
what "minimum implementation" means, when a refactor is warranted. Loop control, stop
conditions and cycle counting are owned by `next_action` / `terminal` / the contract,
never by prose.

**R16.1** No skill may contain control flow. Skills describe *how to do the work*; `next_action`
decides *what happens next*. Specifically, no skill may instruct an agent to stop, to report and
await input, or to decide whether to continue. This rule exists because the predecessor's
execution skill ended every branch with a stop instruction while its wrapper forbade stopping.

---

## Appendix A — Observed defects motivating requirements

Drawn from the predecessor system's (§1) own friction logs and working tree.

| Observation | Requirement |
|---|---|
| Four `.tdd-state.json` files across the tree; one a symlink created to work around path resolution; root file stale by a day and pointing at a different plan; schema drift between them (`total_cycles` present in one, absent in another) | R13.3, R13.4 |
| "Runner must be invoked from `backend/` — running from repo root reads the wrong state file" | R13.3, `tdd doctor` |
| Two projects both containing `pyproject.toml`; root selected by directory listing order | R7.1 |
| `[asyncio]` node-id suffix present in a cached report, absent in a fresh run | R10.2, R13.3 |
| Import errors surfaced as `not_found`, indistinguishable from a mistyped identifier, routing the agent to ask a human | §6, R10.2 |
| Passed-on-arrival in 9 of 17 cycles, each handled by an ad-hoc manual mutate/restore ritual reported only as prose | §8.4, R8.4 |
| 5 cycles executed as "pin characterisation test → refactor", a shape with no RED phase at all, indistinguishable in the record from a discipline failure | §6.2, R6.1–6.4 |
| Orphaned `try:` blocks leaving the tree syntactically invalid mid-cycle | R10.3 |
| Run summary inventing its own fields — commit-shape deviations, test setup smells, unplanned changes, new work raised, per-phase plan quality scores | R5.4, R5.5 |
| Five cycles skipped as non-existent ("the plan counted direct raises, not handlers"), requiring manual cycle-counter edits | `tdd cycle skip`, P3 |
| Cycle 4 absorbing the production work of cycles 5–7, reconstructed narratively afterwards | per-cycle capture at close |
| Four friction notes concerning lint failures caught only at commit time (`I001` twice, `SIM115`, mypy `unused-ignore`) | R9.10 |
| Pre-existing flaky test manually verified against `main` to rule out a regression | R9.4–R9.6 |
| An entire plan's tests asserting against `schema/openapi.json`, with nothing verifying that artifact was current | R9.11 |
| A cycle authorised by its plan to weaken an existing assertion | R7.4 |
| Executor recorded as free text typed by the executor itself | Run.executor_model from environment |
| Every phase handler ending in an explicit stop instruction, inside a skill whose wrapper forbids stopping | R8.1, R8.2, H1 |
