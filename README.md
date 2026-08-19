# tdd-cli

A ledger-backed TDD process controller for autonomous coding agents.

Process state is **derived from observed test execution**, never asserted by the caller.
There is no command that accepts a phase, and no file an agent can edit to claim progress
it has not made.

Implements [`tdd-cli-prd.md`](./docs/PRD.md). Requirement ids (`R9.14`, `§6.2`) in the source
refer to that document.

## Why

An agent instructed to follow TDD will report that it did. The usual ways to hold it to
that — prompt rules, a checklist, a state file in the worktree — all share one flaw: the
record of progress is written by the same agent it is meant to constrain. That flaw
produces four failure classes, reliably: state that is corrupted or edited to claim
progress never made; "the test failed first" as an unverifiable self-report; runs that
stop silently mid-plan; and no record comparable across runs, plans, or models.

This tool removes the agent from the reporting path. It runs the suites itself, computes
every phase transition from what the tests observably did, and records the whole run in a
ledger the agent cannot reach — which is also what makes the friction logs and metrics at
the end trustworthy.

## Install

```sh
pip install tdd-cli        # or: uv tool install tdd-cli
tdd --help
```

From source:

```sh
uv sync
uv run tdd --help
```

## Quick start

```sh
tdd init                       # scaffold tdd.toml from detected projects — then review it
tdd doctor                     # environment preflight
tdd plan register tasks/my-plan.md
tdd run start --plan tasks/my-plan.md
tdd advance                    # the only command that changes phase
```

Every command emits JSON with a `next_action`. That verb is the single authority on control
flow — skills describe *how* to do the work and must never contain stopping instructions.
[`docs/harness-integration.md`](./docs/harness-integration.md) specifies the verb set and how
to write such a skill; [`examples/skills/tdd-drive/`](./examples/skills/tdd-drive/) is a
runnable one for Claude Code. Its planning-side counterpart,
[`examples/skills/tdd-handoff/`](./examples/skills/tdd-handoff/), hardens a
draft plan and authors its contract before the run starts.

## Configuration

`tdd.toml` at the worktree root. Roots are declared, never discovered by scanning for marker
files: two projects can share a marker, and directory-listing order must not decide which
suite runs.

A single-project repository declares the worktree root itself:

```toml
[project.app]
root       = "."
adapter    = "pytest"
test_paths = ["tests/"]
```

A monorepo declares one project per root:

```toml
[project.backend]
root       = "backend"
adapter    = "pytest"
test_paths = ["tests/"]
lint       = ["ruff check"]
typecheck  = ["mypy ."]

[project.frontend]
root       = "frontend"
adapter    = "vitest"
test_paths = ["**/__tests__/**", "**/*.test.ts"]
typecheck  = ["tsc --noEmit"]

[artifact.openapi]
path        = "schema/openapi.json"
produced_by = "backend"
regenerate  = "uv run python -m app.export_openapi"
consumed_by = ["frontend"]

[artifact.api_client]
path        = "frontend/generated"
produced_by = "artifact.openapi"     # artifacts chain
regenerate  = "npm --prefix codegen run generate"
check       = "npm --prefix codegen run check"
consumed_by = ["frontend"]
generated   = true                   # excluded from authorship accounting
```

A generator that is never hand-edited (`codegen`) is an artifact regeneration command, not a
project. It has no tests and no cycles.

Some tests intentionally live outside the project's default runner config — contract tests
that need a live backend being the common case, where CI runs the default suite with no
backend up. Widening the default config to make such a test collectable is the wrong fix:
the plain suite starts making real network calls, and the other suite's tests pollute
target adoption. Instead, declare an override per pattern:

```toml
[project.frontend]
root         = "frontend"
adapter      = "vitest"
test_paths   = ["**/*.test.ts"]
test_command = "npx vitest run"

[[project.frontend.override]]
pattern         = "src/__contract__/"
test_command    = "npx vitest run --config vitest.contract.config.ts"
collect_command = "npx vitest list --config vitest.contract.config.ts"
env             = { API_URL = "http://localhost:${API_PORT}" }
```

Collection and suite runs union the default suite with every override suite, so a cycle can
target a test only the alternate config reaches. Patterns match paths relative to the
project root with `test_paths` semantics, and override files classify as tests without
being repeated in `test_paths`. `env` values may reference `${VAR}`, expanded from the
environment at invocation. For pytest, `collect_command` is optional (`--collect-only`
composes with the run command); a vitest override must declare one — `vitest list` knows
nothing of the override config, and the mismatch is refused at `tdd run start`, not
mid-cycle.

## Sharing cores between concurrent agents

Several agents running tdd-cli on one machine (each in its own worktree) face a bad
trade: a fixed worker count in the test command either oversubscribes the box when
agents run together or serialises every suite when an agent is alone. Instead, declare
where the worker count goes and let the tool compute it:

```toml
[project.backend]
test_command = "uv run pytest -n {workers}"

[project.frontend]
test_command = "npx vitest run --maxWorkers={workers}"
```

Each suite invocation takes a lease in a machine-wide directory (`~/.cache/tdd-cli/leases`,
override with `TDD_LEASE_DIR`) held for the duration of the run, and receives
`max(1, cores // live_leases)` workers: one agent gets the whole machine, four agents get a
quarter each. Leases whose process has died, or older than a suite could legitimately run,
are swept — a crash never throttles the machine.

`{workers}` is opt-in per project; without it the declared command runs verbatim, but the
budget is still exported as `TDD_WORKERS` for commands that prefer to read it themselves,
and the lease is still held so other agents account for the running suite. Set
`TDD_CORE_BUDGET` to cap the total below `os.cpu_count()` and keep headroom for the agents
themselves.

The split is computed at lease acquisition: an agent arriving mid-run takes the smaller
share immediately, and the earlier agent's share corrects on its next invocation. Per-file
collection stays serial — collection is cheap and xdist adds startup cost per file.

## Watching every agent at once

The ledger is one database per repository, shared by all worktrees, so every agent's
progress is already in one place. `tdd fleet` reads it:

```sh
tdd fleet          # one line per active run, plus in-flight baselines and executing suites
tdd fleet --json   # the same as a machine envelope
```

Each run line carries the worktree, plan, cycle N of M, phase, and the age of the newest
suite invocation — a stale age is the signal for a wedged agent. Baselines still being
collected are listed separately, and the worker-lease directory is read (never modified)
to show how many suites are executing right now and each one's share of the cores.

The command is safe to run while agents are mid-run from any worktree on any branch: it
opens the ledger with SQLite's read-only mode, so it is structurally incapable of creating,
migrating, or writing the database, and it requires no `tdd.toml`, plan, or active run.

## Plan contracts

The plan carries its own contract in YAML front-matter, so a planning agent needs no
integration with this tool. The contract is hashed at the **committed blob**, so editing
front-matter mid-run raises `plan_blob_changed`.

```yaml
---
cycles:
  - n: 1
    project: backend
    title: "unmapped exception is not swallowed"
    test: "tests/test_map.py::test_unmapped_is_not_swallowed"
    stub_expected: ["app/exception_map.py"]
    commit_red: "test: unmapped exception is not swallowed"
    commit_green: "feat: domain exception map skeleton"
  - n: 8
    project: backend
    pin_cycle: true                 # characterisation; passes on arrival by design
    test: "tests/test_keys.py::test_enrol_maps_signature_error_to_422"
  - n: 12
    projects: ["backend", "frontend"]
    contract_cycle: true            # breaking change: no intermediate green state
    tests:
      - "backend::tests/test_openapi.py::test_upload_body_schema"
      - "frontend::services/__tests__/upload.test.ts > matches contract"
annotation_keys: ["literal_detail_handlers_kept"]
---
```

Absent front-matter is legitimate — the run proceeds as `undeclared` with
`--allow-undeclared`, and fidelity metrics are unavailable. **Malformed** front-matter
hard-fails registration: it is almost always a defect in the planning process, and that
signal must surface rather than degrade silently.

[`examples/plan.md`](./examples/plan.md) is a complete plan — every cycle kind, the full
front-matter vocabulary, and the body structure (context, verified repo facts, per-cycle
expected failures) that lets an agent execute it without conversation context. The test
suite registers it, so it cannot drift from the contract parser.

Producing a plan of that shape is itself a process.
[`examples/skills/tdd-handoff/`](./examples/skills/tdd-handoff/) is a Claude
Code skill that takes a draft plan, verifies its claims against the codebase, probes each
cycle's RED path empirically, assigns cycle kinds, and authors the contract — gated on
`tdd plan register` succeeding with the intended cycle count and kind breakdown.

## The friction log

`tdd log render` projects the ledger into a markdown friction log — the feedback channel
back to the **planning** process. It reports plan fidelity (declared vs delivered vs
skipped vs never-reached cycles, human interventions) and, per cycle: the target, suite
runs by phase, the first-run outcome against expectation, sensitivity checks, commits,
and integrity events.

Every observable fact in it is projected from recorded events. The agent that did the
work cannot compose it — that is what makes it worth reading, and why the log is
rendered, never written. Judgement enters in exactly two ways:

- **Per cycle, through `tdd annotate`** — rendered inline in the cycle it concerns.
  Beyond keys the plan requires via `annotation_keys`, these keys are reserved for
  judgement agents volunteer: `plan_defect`, `friction_note`, `red_expectation`,
  `commit_shape_deviation`, `test_setup_smell`, `unplanned_change`, `new_work_raised`.
  `plan_defect` is the one that matters most: it records where the plan and the codebase
  disagreed, which is precisely what the next plan needs to know.
- **Per run, as prose appended below the rendered document.** Legitimate and expected —
  post-run narrative (CI failures, patterns noticed) has no cycle to attach to. But it
  is unverified: an auditor should trust the projected sections and read appended
  narrative as the agent's opinion.

`tdd metrics` is the quantitative companion: attempts per cycle, RED-first violation
rate, fidelity, blockers, interventions. Cross-plan aggregates are deliberately labelled
non-comparable — cycle difficulty varies too much — so compare runs of the same contract
only (e.g. the same plan executed by two models).

The loop closes when the rendered log is committed alongside the plan and read before
the next plan is written.

## Adapters

`pytest`, `vitest`, `gradle`, `xctest`, and `exec` are built in. The pytest adapter runs
the suite through the project's own environment manager, detected from its marker files —
`uv.lock`, `poetry.lock`, `Pipfile`, `pdm.lock`, or `[tool.poetry]` in `pyproject.toml` —
checked at the project root first, then the worktree root (workspace layouts keep one
lockfile at the top). With no marker, the active environment's bare `pytest` runs. An
explicit `test_command` always wins.

The `gradle` adapter drives Kotlin/JVM and Android projects. It runs the project's Gradle
test task and reads per-test verdicts from the JUnit XML Gradle writes, rather than
scraping the console. The task is a config choice — `./gradlew test` or `testDebugUnitTest`
for fast JVM unit tests, `connectedDebugAndroidTest` for instrumented tests on a device
(give those a longer `timeout` and a `lease` so only one run touches the device at a time).
A *compile* failure maps to `not_collected`, not `failed`: Kotlin has no separate
collection phase, so a stub referencing a missing symbol fails the build, and the "stub
before RED" discipline holds exactly as it does for a Python import error.

```toml
[project.android-app]
root         = "android-app"
adapter      = "gradle"
test_paths   = ["src/test/"]
test_command = "./gradlew testDebugUnitTest"
```

Third-party adapters register under the
`tddcli.adapters` entry-point group:

```toml
[project.entry-points."tddcli.adapters"]
cargo = "tddcli_cargo:CargoAdapter"
```

The class must implement `tddcli.adapters.base.Adapter`. Built-in names cannot be
shadowed: a plugin named `pytest` is ignored, so what "observed test execution" means for
existing configs can never change underneath them.

## Platform support

Linux and macOS. Windows is refused at startup with `reason: "unsupported_platform"` —
worker leases and process-liveness checks are POSIX-only. Use WSL.

Every JSON envelope carries `envelope_version`; consumers should check it rather than
assuming the shape is stable across releases. See also [SECURITY.md](./SECURITY.md) for
the trust model: running `tdd` executes the repository's declared commands.

## Cycle kinds

**Standard / contract** — `AWAITING_TEST → AWAITING_IMPL → AWAITING_REFACTOR → CLOSED`

**Pin** — `AWAITING_PIN → SENSITIVITY_REQUIRED → AWAITING_REFACTOR → CLOSED`

A pin characterises existing behaviour before deleting or restructuring it, so its test
passes on arrival by design and its sensitivity check is mandatory. Pins are excluded from
the RED-first violation metric; a *standard* cycle that passes on arrival remains a violation
and is never reclassified as a pin.

## What the tool does, that agents do not

- **Stages and commits.** The staged set is derived from the phase: RED takes tests and
  declared stubs, GREEN takes the rest. This makes "implementation written during RED" an
  exact, language-independent detection with no source parsing.
- **Regenerates stale artifacts**, in their own commit, so hand-written and generated changes
  stay separately reviewable.
- **Resolves executor identity** from the session transcript. It is never an argument.
- **Runs the close sweep** over the cycle's projects plus anything downstream of an artifact
  it touched — not every project every time.

## Commands

| Command | Purpose |
|---|---|
| `tdd init` / `tdd doctor` | scaffold config; environment preflight |
| `tdd plan register <path>` | parse and hash the contract |
| `tdd run start --plan <path>` | capture baselines, resolve executor, open cycle 1 |
| `tdd status` | position and `next_action`; safe any time |
| `tdd advance [--retry]` | run suites, compute the transition, commit |
| `tdd cycle skip --reason` | sanctioned path for a cycle the plan got wrong |
| `tdd sensitivity begin\|check\|end` | prove a passing test can fail; verify restore |
| `tdd annotate --key --value` | attach judgement to the current cycle |
| `tdd blocker --kind --detail` | typed blocker; releases the stop hook |
| `tdd resume [--unblock --note]` | reconstruct position; human intervention |
| `tdd log render [--out]` | project the ledger into a friction log |
| `tdd metrics` | fidelity, attempts, violations, interventions |
| `tdd fleet [--json]` | all active runs across every worktree; read-only |

## Running a long baseline

`run start` probes every project's suite before a run exists (R9.5a), and on a real project
that can take minutes — well past an agent harness's default Bash timeout. If the command
appears to hang or time out, **do not re-run it**: the probe is still making progress in the
background, and a second `run start` against the same worktree is refused with
`reason: "baseline_in_progress"` — retrying on timeout just stacks refusals on top of a
baseline that was never stuck. In order of preference:

1. **Background it.** Run `tdd run start` in the background if your harness supports it. The
   heartbeat (`baseline_captured` / `project_completed` lines on stderr) lands in the task log
   as each project finishes, and most harnesses re-invoke the agent when a backgrounded command
   exits — a real completion callback, with no timeout ceiling.
2. **Raise the timeout.** Claude Code's Bash tool takes an explicit `timeout` (default 120000ms,
   max 600000ms). A baseline that takes 3–8 minutes fits inside ten.
3. **Poll.** `tdd progress` (and `tdd status`) report `collecting_baseline` with per-project
   counters and elapsed time while a baseline is in flight, with `next_action.verb ==
   "await_baseline"` — the fallback for an agent that inherited a run it did not start itself.

## Storage

One SQLite ledger **per repository**, in `~/.local/share/tdd-cli/` (override with
`TDD_LEDGER_HOME`), keyed by the common git dir. Never inside the worktree, never resolved
from the current directory, never committed. `worktree_path` is a column, so concurrent runs
in separate worktrees are isolated without a pruned worktree orphaning its history.

## Enforcement boundary

The CLI cannot compel an agent — only the harness can.

**Hard gates here:** phase is never caller-supplied; a cycle cannot close over a stale
artifact; a passed-on-arrival cycle cannot close without a verified sensitivity check;
`advance` refuses an unchanged tree unless `--retry`.

**Recorded, never blocked:** non-stub writes during RED, undeclared file touches, scope
divergence, extra attempts. Prevention rules with edge cases produce false denials, and a
blocked agent improvises around them — putting it right back in the reporting path the
tool exists to keep it out of.

**Delegated to hooks:** a Stop hook that queries `tdd status` and refuses to let an agent
stop while a run is live; a Bash hook redirecting bare `pytest`/`vitest` through `tdd advance`.
Ready-made Claude Code implementations of both live in
[`examples/claude-code-hooks/`](./examples/claude-code-hooks/).

**Delegated to the skill:** how to respond to each `next_action` verb — writing the test,
the stub, the implementation. [`docs/harness-integration.md`](./docs/harness-integration.md)
is the contract for writing one against any harness.

## Development

```sh
uv run pytest
uv run ruff check src tests
```

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

[MIT](./LICENSE)
