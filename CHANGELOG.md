# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- **vitest ids from named vitest projects** (#163). Whole-suite collection read `vitest list`
  text, which prefixes `[<project>] ` to every line of a named vitest project and prints paths
  relative to that project's `root`, so it collected ids no run ever reports (and, via the
  per-file loop, a second spelling of every test). It now reads `vitest list --json` and roots
  each id at the test's own file. tdd appends `--json` itself; a collect command must not.
- **The vitest override-isolation check sees named vitest projects** (#163). `tdd doctor`'s
  check that the default config does not reach an override's files read the same text
  listing, so a `[<project>] ` prefix meant it could never match. It now reads
  `vitest list --json`, and a listing that is not JSON fails the check, naming the command.
- **Adoption never picks another cycle's test** (#163). When a cycle's declared test was
  missing, `tdd advance` adopted any test new since the run started, including an earlier
  cycle's target, so a premature advance handed cycle 1's test to cycle 2. Every target in
  the run is now excluded, compared by normalised id.
- **`tdd target` accepts the plan's spelling of a test** (#163). It matched only the exact
  collected id, so it could not name the declared vitest id (`src/a.test.ts > math > adds`
  for a collected `frontend::src/a.test.ts > math adds`). It now qualifies and normalises
  its argument as a plan declaration is, and stores the collected id.
- **An adopted target the run cannot find is refused** (#163). A test that collection
  listed but no run reported was recorded as the target and came back `not_found` on every
  advance, re-adopting a different test each time. The adoption is now evaluated first; on
  `not_found` the declared target is kept, `adopted_target_not_found` is recorded, and
  `tdd advance` answers `resolve_blocker`.

## [0.14.0] - 2026-09-24

### Added

- **`tdd run abandon`: end a run that will not be finished** (#150). `tdd run abandon
  --reason <text>` ends the worktree's live or blocked run with `outcome = abandoned`;
  `--run <id>` does the same for a run whose worktree is gone. It records the reason and
  who did it (account and executor) in a new `abandonment` table, counts as a human
  intervention, and releases the worktree's claims. `tdd fleet` stops listing the run,
  `tdd metrics` reports it with an `abandoned: {reason, by}` entry, and a new run can
  start at the same path. The table is added on open; the ledger schema version is
  unchanged.

## [0.13.0] - 2026-09-23

### Added

- **Where a run's time went** (#147). `tdd metrics` gains a per-run `time` object:
  `wall_clock_s`, `suite_s`, `suite_share` and `by_phase` (runs and suite seconds for
  every phase recorded). A live run's wall clock runs to now. The friction log gains a
  `## Time` section with the same split, a per-phase table and a per-cycle table
  (wall clock, suite time and suite runs). Nothing new is recorded: these are the
  ledger's existing timestamps and `invocation.duration_ms`.
- **Split mode: a ledger the agent's account cannot open** (#142). With
  `/etc/tdd-cli/runner.toml` in place, a separate runner account owns the ledger
  in a mode-700 directory. The agent's `tdd` forwards every verb except `docs`
  and `init` to it through `sudo`, and the runner executes every suite, gate,
  hook and git command as the agent. Executor identity is recorded as `operator`
  when the runner's config assigns the calling account a model, and `claimed`
  otherwise. `tdd runner import <ledger>` brings an existing ledger under the
  runner, marked `pre_split_import`, which `tdd metrics` reports. Setup and a
  verification checklist: `tdd docs split`.
- `tdd doctor` reports `mode` (`single` or `split`). In split mode it probes,
  live and as the agent, that the uid drop works, that the agent cannot read the
  ledger, and that it cannot write the install.

### Changed

- **GREEN runs the target first** (#149). An `AWAITING_IMPL` advance whose target
  still fails now says so after running only the target. A passing target is followed
  by the whole-suite run that decides GREEN, as before. `tdd metrics` counts
  `impl_attempts` from each advance's target-only run only, and still counts every
  `AWAITING_IMPL` run in cycles recorded before this change.
- `tdd doctor` on a single-user machine no longer lets "ledger outside
  worktree" stand for isolation: a `ledger isolation` notice says the ledger is
  owned by the same uid that runs the agent. The README and SECURITY.md say the
  same. Single-user installs behave exactly as before.
- **RED runs only the target test** (#148). `AWAITING_TEST`, `AWAITING_PIN` and
  `tdd sensitivity check` now run the target alone: pytest runs the owning suite's
  collect command with the node id, and vitest filters to the file and an anchored,
  escaped `-t` name. A failure elsewhere no longer blocks RED. It is caught at
  GREEN, which runs the whole suite for **every** adapter. A collection error in
  the target's own file is still `not_collected`. A target adopted in place of the
  declared id is run in the same advance. The ledger is now schema 12:
  `invocation.others_observed` is `0` for a target-only run.

### Fixed

- **GREEN ran only the target on cargo, gradle, xctest and exec** (#153), so a
  regression elsewhere reached the close sweep unseen, and the sweep could skip the
  cycle's own project without the whole suite ever running. These adapters now
  narrow only when asked for a target-only run.

- **The close sweep re-ran a tree that had just passed** (#146): `gitutil.tree_hash` hashed git
  state (index entries plus the unstaged diff), so the same content hashed differently before
  and after the GREEN commit, and the §6.1 skip of a cycle's own suites never fired. It now
  hashes working-tree content through a throwaway index, independent of what is staged or
  committed. A skipped close sweep still runs the cycle project's lint/typecheck gates; before
  this fix, the skip would have dropped them too. `--reuse-baselines` cache entries written by
  earlier versions no longer match and are re-probed once.

## [0.12.2] - 2026-09-17

### Fixed

- **A wildcard directory in `test_paths` matched nothing** (#136): a pattern ending in `/` was
  compared as a literal prefix by `Project.is_test_file` and joined as a literal path by the cargo
  adapter's `_test_files`, so `crates/*/tests/` — how a workspace declares one pattern instead of
  one per crate — matched no file at all. Every test file in such a project classified as
  implementation, so a RED commit touching only tests was recorded as `implementation_during_red`,
  reporting the agent for writing production code it had not written; `_test_files` returned an
  empty list, leaving the unaccounted-files check with nothing to compare. A directory pattern is
  now matched per path segment (`crates/*/tests/` covers `crates/x/tests/main.rs`, not
  `crates/x/src/tests/main.rs`), and the adapter globs it.

## [0.12.1] - 2026-09-17

### Fixed

- **cargo: a test target whose name differs from its file's stem** (#134): the adapter derived the
  target from the `Running tests/<file>.rs` header's path, which is only the target's name under
  cargo's default of one binary per `tests/*.rs`. A crate that sets `autotests = false` and declares
  its own `[[test]]` — many files compiled into one binary named something else — was unreachable:
  collection ran `--test <stem>` and cargo answered ``no test target named `<stem>` in default-run
  packages``, so every cycle target came back `not_collected`, whatever id the plan declared. The
  target is now read from the artifact the header names (`…/deps/bridge_tests-<hash>`), which is
  also the only thing distinguishing two crates in a workspace whose test files are both
  `tests/main.rs`. The crate manifests supply the mapping back: target → the file it is built from
  for `target_path` and the collection file set, and the declared spelling for `--test`, since cargo
  writes a target's `-` as `_` in the artifact. Manifests are located by walking up from the declared
  `test_paths`, not from `_test_files()`, which does not expand a wildcard directory pattern such as
  `crates/*/tests/`. Under the default layout target and stem still agree and nothing changes.

## [0.12.0] - 2026-09-17

### Changed

- **Close sweep runs all gates before any suite** (#129): lint and typecheck now run for every
  project in the sweep set before any project's suite executes. A failing gate short-circuits the
  sweep immediately — no suite runs, and `next_action` returns `fix_regression` with the failing
  gate entry. Previously each project ran its suite first and only then checked its gates.
- **`Adapter._gate` stops at the first failing command** (#129): the first non-zero exit ends the
  gate; subsequent commands in the same gate list are not executed.
- **Gate memoisation** (#129): a gate whose project tree hash is unchanged since it last passed
  within the same run is skipped (no command executed) and recorded with `skipped = 1` in
  `gate_result`. A failed gate or a changed tree always re-runs.
- **`fix_regression` detail wording** (#129): the reply for a gate failure now reads
  `"Close sweep stopped before the suite: lint/typecheck gates failed."` (was `"Close sweep is
  green but lint/typecheck gates failed."`).
- **Schema v11** (#129): `gate_result` gains `tree_hash TEXT` and
  `skipped INTEGER NOT NULL DEFAULT 0`. Existing ledgers are migrated on open via `MIGRATIONS[10]`.

## [0.11.0] - 2026-09-16

### Added

- **`tdd fleet` reports baseline-collector and advance-holder liveness** (follow-up to #115,
  fixes #122): `fleet --json` now includes `stale` and `pid` on every `collecting` row,
  matching the fields already on `tdd status` / `tdd progress` result objects. A new
  top-level `advancing` list exposes in-flight `tdd advance` claims with the same liveness
  fields. Human text gains ` — collector (pid N) is dead` / ` — holder (pid N) is dead`
  suffixes; `no active runs` is suppressed when an advance claim is held.

- **`run.start_sha`** (schema v10, `MIGRATIONS[9]`): the HEAD commit at run start is now
  recorded on the run row and used as the reference point for late probes and
  `--accept-failures` gating.
- **`gitutil.temporary_worktree`**: context manager that checks out a given sha into a
  detached temporary worktree and removes it on exit; used by the late-probe and
  `--accept-failures` implementations.
- **`baseline_late_probe` / `baseline_late_probe_unobserved` integrity events**: emitted
  when the close sweep late-probes an un-baselined project at `start_sha` (observed) or
  cannot observe it (unobserved).
- **`resume` result `refused_from_baseline`**: lists per-project tests that `--accept-failures`
  refused because they pass at `start_sha`.
- **New `baseline_amended` event detail shape**: `{project: {start_sha, accepted: {id: verdict},
  refused: {id: verdict}}}` with per-test verdicts.
- **Friction-log lines for amended baselines**: accepted/refused tests appear under Human
  interventions; the run header gains a "Late baselines" line separate from "Baseline failures
  at start".

- **`tdd docs [topic]` prints the documentation shipped with this version.** The wheel now
  carries `docs/harness-integration.md`, both example skills, the hooks README, the example
  plan, and the README under `tddcli/_docs/`. An agent meeting the tool in an unfamiliar
  project can read the protocol without network access — and without the version hazard of
  fetching a skill from `main` that targets a different `verb_set_version` than the installed
  binary emits. `tdd docs` with no topic returns a machine-readable index; `tdd --help` and
  `tdd init` now point at it.
- **`artifact_regenerate_failed` integrity event.** When a `regenerate` hook exits non-zero,
  an `artifact_regenerate_failed` event is emitted on the cycle (or run, for `run start`)
  with the artifact name, exit code, and last 2000 chars of stderr. It is listed in the
  friction log under its cycle via the existing per-cycle event renderer.
- **`artifact_check.regenerate_failed` column (ledger schema v9).** A non-zero hook exit
  sets this flag on the `artifact_check` row. Existing ledgers are migrated on open via
  `MIGRATIONS[8]`.

### Fixed

- **`--accept-failures` is now gated on `run.start_sha`**: only tests that also fail at the
  start sha are accepted into the baseline; tests that pass there are refused and listed in
  `result.refused_from_baseline`. This prevents laundering run-introduced regressions.
- **Un-baselined projects are late-probed at `start_sha`** in the close sweep instead of
  accepting HEAD failures verbatim. An observed probe inserts a `late_probe` baseline row and
  subtracts it like a normal baseline; an unobservable probe blocks with `resolve_blocker`
  and no longer recommends `--accept-failures`.
- **The `no_baseline_for_project` reply no longer recommends `--accept-failures`** for
  unobservable projects.
- **A dead baseline collector no longer bricks the worktree.** When a `tdd run start`
  process is killed during baseline collection, the stale `baseline_claim` row was left
  behind. `tdd status` and `tdd progress` computed `stale: true` correctly but emitted
  `await_baseline` anyway — a non-terminal verb that instructed autonomous executors to
  poll forever. Both commands now emit `confirm_cycle_applicable` with `result.stale == true`
  and `result.pid` when the collector pid is dead, and the `detail` names the recovery
  action: re-run `tdd run start --plan <path>`. The `collecting_baseline` result body always
  carries `stale` and `pid` so callers can inspect liveness without a separate `tdd fleet`
  call. (Fixes #115.)
- **`check_artifacts`: a failed regenerate hook is now a hard close-sweep failure.**
  Previously, a `regenerate` hook that exited non-zero left the artifact path untouched
  (tree hash unchanged), so the staleness probe reported "fresh" and `tdd advance` replied
  `complete`. The exit code is now captured; a non-zero exit surfaces `fix_regression` with
  `result.artifact_failures` listing the affected artifact(s) and their stderr.
- **`run start` refuses when a regenerate hook fails before the first cycle.** The run row
  is ended with `outcome = "refused"` so `tdd status` reports no active run.

## [0.10.1] - 2026-09-06

### Fixed

- **pytest adapter: `--dist loadgroup` node ids.** pytest-xdist reports a test marked
  `xdist_group("<g>")` as `<nodeid>@<g>` and pytest-json-report records that spelling, so a
  grouped target was `not_found` on every suite run even though it was collected and
  passed, and its `passed`/`failed` ids never matched collected ids. The adapter now strips
  the trailing `@<group>` when reading report and `--collect-only` ids. Only an `@` after
  the last `]` is treated as the suffix, so parametrised ids such as
  `test_x[user@example.com]` are left intact.

## [0.10.0] - 2026-09-05

### Added

- **cargo adapter** — Rust driver through `cargo test`. Ids are `<target>::<path>`
  (`lib::…` for unit tests, `<tests-file-stem>::…` for integration tests) and compose
  to `--lib`/`--test <name>` + `-- --exact <path>` for targeted runs. Verdicts are
  parsed from cargo's per-test console lines, attributed to targets by the
  `Running …` headers with stderr merged; doc-tests are excluded. A compile error maps
  to `not_collected`, matching gradle/xctest. Collection is `cargo test --tests --
  --list` with a per-file `--test <stem>` fallback; `tdd doctor`'s collectable gate is
  `cargo test --no-run`. Target lint requires the `::` separator.

## [0.9.0] - 2026-09-03

### Added

- **`tdd note` — an executor-narrative channel.** `tdd note "<text>"` attaches
  a phase-stamped note to the current cycle, or a run-level note once the run
  has ended (it falls back to the latest run, so no active run is required).
  Cycle notes render in the friction log as blockquote claims under their cycle;
  run-level notes render under a new `## Executor narrative` section, which is
  omitted when there are none. Envelopes that carry an integrity event now nudge
  for a note while the reason is fresh (silenced once the cycle has one), and
  the terminal `COMPLETE` envelope — via `advance` or a final-cycle skip — asks
  for a closing narrative before rendering. Stored in a new `note` table via a
  v7→v8 ledger migration (#77, #94).

- **Baseline sanity gate.** `run start` refuses a baseline whose failing ratio
  exceeds a threshold (default 0.5, suites under 10 collected tests exempt) with
  `reason: "baseline_implausible"`, on the grounds that a mostly-red suite means
  the environment is broken rather than the code. A per-project
  `baseline_max_failure_ratio` in `tdd.toml` overrides the default, and
  `--accept-baseline` bypasses the gate and logs a `baseline_accepted` integrity
  event (#67, #84).

- **Standing-failure delta.** A non-empty baseline is now compared against the
  previous run's baseline for the same worktree and a `baseline_standing_delta`
  event partitions the failing set into new versus inherited failures, so a
  pre-existing red test is distinguishable from one that broke since the last
  run (#67, #84).

- **Per-project `health_command`.** An optional command in `tdd.toml` that is
  probed before baseline capture; if it fails, `run start` refuses with
  `reason: "services_unreachable"` instead of recording a baseline against a
  down dependency (#67, #84).

- **Declared-target lint.** `plan register` and `run start` now lint every
  declared target against the adapter's id grammar (pytest `::`, vitest ` > `,
  gradle `Class/method`, xctest `Bundle/Class/testMethod`) and against project
  roots: a target path that duplicates a non-`.` project root prefix is refused
  unless the nested path genuinely exists in the worktree. Findings are returned
  under `reason: "target_lint"`; `run start` re-lints the stored contract
  against the current config before claiming a baseline (#71, #88).

- **Per-adapter sensitivity evidence line.** Each adapter now extracts a
  `target_evidence` line from a failing target — the first `E` line for pytest
  (skipping the xdist worker header), the first `: error:` line in the test's
  window for xctest, `failureMessages[0]` for vitest, the junit failure message
  for gradle, and the last non-empty output line for exec. The sensitivity check
  persists it as `sensitivity_check.evidence_line` (v6→v7 migration) and the
  friction log's observed snippet prefers it over the raw first line, rendering
  `<no assertion line captured>` when empty and keeping the tail of over-long
  lines. Legacy rows with no stored evidence keep the first-line fallback (#68,
  #90).

- **Diagnosable executor attribution.** `TDD_EXECUTOR_MODEL` lets a harness
  declare the executor identity (`source: declared`), taking precedence over
  transcript detection. When identity cannot be resolved, `Executor.reason`
  says why — session id unset, transcript not found, or transcript without a
  model record — and `run start` logs an `executor_unknown` event and surfaces
  `executor_warning` in its envelope. `tdd doctor` gains an informational
  executor-identity check (#74, #92).

### Changed

- **Target adoption is evaluated in the same `advance`.** When a cycle's
  declared target is missing and exactly one new test appears, `advance`
  adopts it (logging `declared_test_mismatch`) and judges RED — or drives the
  sensitivity check when it passed — from the suite run that already happened,
  instead of asking for a re-run. A declared id that differs
  from a single same-file candidate only by separator normalisation is
  disambiguated and adopted without asking; two same-file candidates still
  require an explicit `tdd target` (#72, #91).

- CI now tests on Python 3.11 and 3.14 only (#87).

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
