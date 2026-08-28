# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.8.0] - 2026-08-28

### Added

- **`--reuse-baselines` caches baseline probes by content hash.** `run start`
  can skip re-probing a project whose tree is unchanged: a probe result is
  cached keyed by `(project, tree_hash, config_sha)` — where `tree_hash` folds in
  every upstream producer root — and an identical rerun emits `baseline_reused`
  instead of `baseline_captured`, reusing the cached failing set and collection
  snapshot rather than re-running the suite. Provenance is recorded on the
  baseline row (`source`), and `--reuse-max-age` re-probes any entry older than
  the given age. Off by default; the cache stays empty unless the flag is passed
  (#45, #59).

- **`--baseline-jobs` parallelizes baseline probing.** `run start` probes each
  project's baseline under a bounded `ThreadPoolExecutor` when `--baseline-jobs`
  is greater than 1 (default 1, must be >= 1). The `baseline_captured` heartbeat
  survives the pool, and a worker probe that raises becomes an attributed failure
  that aborts cleanly and frees the worktree rather than wedging it (#46, #62).

- **Plan-level `ancillary_files`.** A top-level front-matter key declaring
  cross-project or companion paths a plan touches (README, generated fixtures,
  sibling-project files). Declared ancillary paths are bucketed into their own
  staging bucket, committed with the cycle, and fire no `undeclared_file_touched`
  event. Validated as a list of strings at registration and persisted to the
  ledger via a v5→v6 migration (#70, #80).

- **Run-close gate on undeclared touched paths.** `run close` now blocks when a
  path previously flagged as `undeclared_file_touched` is still dirty in the
  worktree, so undeclared changes cannot slip through at the end of a run. A
  flagged path that was since committed does not block; one that has vanished is
  reported via a new `undeclared_file_dropped` event rather than blocking (#69,
  #81).

- **Reserved per-cycle `meta:` passthrough.** A cycle may carry an authored
  `meta:` mapping in the plan front-matter; it round-trips through storage
  unchanged and is available for plan-time metadata. A non-mapping `meta:`
  hard-fails registration with a `ContractError` (#58, #65).

### Fixed

- `undeclared_file_touched` is deduplicated within a cycle, so a path touched
  across multiple phases no longer floods the cycle with repeated events (#55,
  #61).
- vitest test ids are normalised on the describe/test separator before matching,
  so a formatting-only difference between a declared target and the observed
  verdict is no longer reported as a spurious `declared_test_mismatch` (#57,
  #63).
- The `stale_artifact` event is suppressed when the tool auto-regenerates the
  artifact and commits it, so a successful regeneration no longer also emits a
  staleness warning (#64).

## [0.7.0] - 2026-08-23

### Fixed

- **Concurrent `tdd advance` no longer corrupts a run.** Two `advance` processes
  racing on the same worktree could both close the same cycle row. Because
  `close_cycle` unconditionally opened the next ordinal, a double-close forked the
  run into two parallel cycle chains; every remaining cycle ran twice, the run
  "completed" with one chain's last row permanently open, and the doubling was
  invisible from the agent's perspective. `close_cycle` now re-reads `closed_at`
  before acting; if the row is already closed it returns the currently-open cycle
  without transitioning or opening anything. `open_cycle` returns the existing open
  row for an ordinal rather than inserting a duplicate.

### Added

- **Per-worktree advance claim.** `tdd advance` now acquires a `advance_claim` row
  before dispatching. A second concurrent `advance` is refused immediately with
  `ok: false`, `reason: "advance_in_flight"`, and metadata (`pid`, `started_at`,
  `elapsed_s`) that lets the agent confirm the holder is still alive. The claim is
  released in a `finally` so a raising handler cannot wedge the worktree; a claim
  held by a dead pid is reclaimed automatically on the next call. Schema version
  bumped to 3.

## [0.6.0] - 2026-08-19

### Added

- **gradle adapter** — Gradle driver for Kotlin/JVM and Android projects. Runs the
  project's Gradle test task (`./gradlew test`, `testDebugUnitTest`, or
  `connectedDebugAndroidTest`) and reads per-test verdicts from the JUnit XML Gradle
  writes, rather than scraping the console — unit and instrumented tasks share one
  parser, so the task is a config choice, not a code path. A compile failure maps to
  `not_collected` rather than `failed`: Kotlin has no separate collection phase, so a
  test referencing a missing symbol fails the build, and the "stub before RED"
  discipline holds exactly as it does for a Python import error. The discriminator is
  whether fresh JUnit XML was produced, not "BUILD FAILED" (a test failure prints that
  too); a `--tests` filter matching nothing maps to `not_found`. Stale results are
  cleared before each run, which also invalidates Gradle's up-to-date check so a
  targeted run is scored only against the XML it produced. Collection is a per-file
  grep of Kotlin/Java sources (Gradle has no cheap whole-suite enumerator), so one
  unreadable file cannot destroy the set. `tdd doctor` gains a `gradle wrapper present`
  check, active only when the command uses `./gradlew` (#41).

## [0.5.1] - 2026-08-17

### Added

- **exec adapter** — exit-code oracles as first-class test suites. Any executable
  file (or any file paired with a `test_command`) becomes a test: exit 0 → passed,
  non-zero → failed, stdout+stderr captured as failure output. Non-executable files
  without a `test_command` map to `not_collected` rather than `failed`, so a missing
  executable bit is a configuration error rather than a test failure. Supports a
  `{file}` placeholder in `test_command` for per-file invocation, with shell-quoting
  so paths with spaces are handled correctly (#33).

- **xctest adapter** — XCTest/xcodebuild driver for Swift and Objective-C projects.
  Test ids use xcodebuild's own `-only-testing:` format (`Bundle/Class/method`) so
  targeted runs compose without translation. A build failure maps to `not_collected`
  rather than `failed` — Swift has no separate collection phase, so a missing-symbol
  build error is not the RED state; the discipline is to write a compiling stub first,
  then observe an assertion failure. Collection tries `xcodebuild test
  -enumerate-tests` (Xcode 16+) and falls back to grepping Swift source files for
  `class Foo: XCTestCase` and `func testBar()` patterns. Requires `test_command` in
  `tdd.toml` so the adapter can append `-only-testing:` and `-enumerate-tests` flags
  without guessing the scheme or destination (#34).

- **Named exclusive leases** (`lease = "<name>"` on a project or override) — before
  running a suite the tool acquires an exclusive machine-wide named lease using the
  same lease-directory machinery as the worker budget. Only one holder machine-wide
  can hold a given name at a time; a waiting invocation blocks with a `lease_waiting`
  heartbeat every 5 s rather than silently hanging. Stale locks (pid dead or older
  than 1 h) are swept immediately so a crash can never permanently block a name.
  The name is free-form and machine-scoped; two repos naming the same lease
  intentionally contend, which is the intended semantics for shared physical hardware
  or a port-bound service (#35).

- **Per-project suite timeouts** (`timeout = <seconds>` on a project or override) —
  overrides the 1800 s default for suite invocations. `tdd doctor` warns when a
  configured timeout is shorter than the longest recorded full-suite invocation for
  that project, so a mis-configuration is caught at preflight rather than at the
  timeout boundary (#35).

## [0.4.1] - 2026-08-16

### Changed

- `collect()` runs one invocation per declared suite instead of one per test
  file, falling back to the per-file loop for anything a batch did not account
  for. Per-file collection was **77% of a real `run start`** — 313 subprocesses
  costing 402s, against 117s to actually run every test — because cost scaled
  with file count at a ~1.08s floor per invocation (the environment manager
  resolving plus the runner booting). Measured 38.8x faster on a 60-file
  project, with an identical collected set. R10.3's guarantee is unchanged: a
  file that fails to collect is still attributed to itself and cannot destroy
  the set, and a file the batch never reports is still collected individually,
  so the set can only match or improve on the old one (#27).

## [0.4.0] - 2026-08-16

### Added

- `baseline_captured` reports `run_s` and `collect_s` alongside `elapsed_s`. The
  suite run and the per-file collection have unrelated cost models — one scales
  with tests, the other with files — so a single total could not say which was
  slow, and answering that meant measuring projects by hand outside the tool.
- `TDD_TIMING=1` emits a `command_timing` line per subprocess on stderr
  (`label`, `command`, `cwd`, `duration_ms`, `exit_code`), covering every
  subprocess the tool spawns: suite runs, per-file collection, lint/typecheck
  gates, doctor probes and artifact hooks. Off by default — the per-file loop
  would otherwise emit one line per test file on every invocation. `label` is
  one of `suite`, `collect`, `gate`, `doctor`; an unlabelled row comes from a
  third-party adapter, since every built-in call site names itself (R8.4).

### Fixed

- `tdd doctor` no longer emits a blocker it cannot explain. Every failing check
  now carries a `detail` naming what to fix, enforced by the checklist recorder
  so a check added later inherits the guarantee. Previously `worktree clean`
  failed with `detail: ""`, leaving an agent with `resolve_blocker` and nothing
  to resolve — it re-ran doctor and read the identical output.
- `worktree clean` is scoped to dirt a run would actually read: a declared
  project root, a declared artifact path, or `tdd.toml`. Build residue is
  excluded via `config.is_ignored`, so doctor's own `uv run` / `vitest list`
  probes (`.venv`, `node_modules`, caches) can no longer be what makes doctor
  fail. Unrelated dirt is reported in the passing check's `detail` rather than
  blocking the run.

## [0.3.0] - 2026-08-10

### Added

- `env` on `[project.<name>]`: environment for the default suite's runs and
  collection, with the same semantics as an override's `env` (`${VAR}` expands
  from the environment at invocation). An override's `env` layers on top for
  its own suite. Previously only override suites could declare environment,
  leaving a default suite that reads an endpoint from a variable with no
  registry-level way to receive it (#16).

### Fixed

- vitest test ids are project-root-relative (`frontend::app/x.test.tsx > name`),
  matching pytest nodeids and the form plan declarations qualify to — they were
  worktree-relative (`frontend::frontend/app/...`), so a declared vitest target
  could never match a verdict: standard cycles limped through on R8.9 adoption
  (a spurious `declared_test_mismatch` per cycle) and pin cycles deadlocked in
  `AWAITING_PIN`, since a pre-existing test is never adoptable (#21).
- `tdd target` refuses a name that is not a collected test in the cycle's
  projects, suggesting the closest collected ids — previously any string was
  recorded as the target and failed later, misattributed, as `not_found` (#15).
- Failure text (`target_failure`, uncollected-suite messages) is clipped keeping
  both ends instead of truncated from the head: Python puts the actual error at
  the tail of a traceback, so a head-only cut on a deep stack delivered
  framework frames and cut exactly the line that says what went wrong (#17).

## [0.2.1] - 2026-08-10

### Added

- `tdd doctor` check `default suite cannot reach override files`: when a
  project declares overrides, doctor probes the default suite's discovery
  (pytest: the test command with `--collect-only`; vitest: `vitest list`) and
  fails if it reaches files an override owns — the premise suite overrides
  require, which nothing previously enforced.

### Fixed

- A test observed by more than one suite invocation of the union (the default
  suite's discovery sweeping an override's files, e.g. a bare `pytest` default)
  is now a loud tooling error naming the overlapping tests and the fix, instead
  of the target being silently judged by whichever suite reported it first —
  previously an env-less run whose failure said nothing about the overlap.

## [0.2.0] - 2026-08-10

### Added

- Per-pattern suite overrides (`[[project.<name>.override]]` in `tdd.toml`): an
  alternate `test_command` — plus optional `collect_command` and `env` — for
  files the default runner config cannot reach, such as contract tests that need
  a live backend. Collection and suite runs union the default suite with every
  override suite, so a cycle can target such a test without widening the default
  config (which breaks CI and pollutes target adoption with the other suite's
  tests). Override patterns classify their files as tests without being repeated
  in `test_paths`; `env` values may reference `${VAR}`, expanded at invocation.

## [0.1.0] - 2026-08-08

Initial release.

- Ledger-backed TDD process controller: phase is derived from observed test
  execution, never asserted by the caller.
- Plan contracts in YAML front-matter, hashed at the committed blob.
- Standard, pin, and contract cycle kinds.
- pytest and vitest adapters. The pytest adapter runs suites through the
  project's environment manager (`uv.lock`, `poetry.lock`, `Pipfile`,
  `pdm.lock`, or `[tool.poetry]`), falling back to bare `pytest`; an explicit
  `test_command` always wins.
- Single-project repositories (`root = "."`) and monorepos alike; `tdd init`
  scaffolds the registry from evidence and reports directories it could not
  match instead of guessing.
- Phase-derived staging and committing; artifact regeneration in separate commits.
- Machine-wide worker leases so concurrent agents share cores.
- `tdd fleet`: read-only view of every agent's run on a repository.
- Fidelity metrics, typed blockers, friction-log rendering.
- `tdd --version`; every JSON envelope carries `envelope_version`.
- Ledger schema versioning: older ledgers are migrated forward on open; a
  ledger written by a newer tdd-cli is refused with a clear error.
- Third-party adapters via the `tddcli.adapters` entry-point group
  (built-in names cannot be shadowed).
- Windows is refused at startup (`reason: "unsupported_platform"`); use WSL.
- `docs/harness-integration.md`: the contract for writing a driving skill
  against any harness — the envelope, the closed verb set, and authoring rules.
- Example Claude Code integrations: Stop + PreToolUse hooks
  (`examples/claude-code-hooks/`), a driving skill (`examples/skills/tdd-drive/`),
  and a plan-hardening skill (`examples/skills/tdd-handoff/`).
- `examples/plan.md`: a complete example plan exercising every cycle kind and
  the full front-matter vocabulary, registered by the test suite so it cannot
  drift from the contract parser.
- SECURITY.md documenting the command-execution trust model.
