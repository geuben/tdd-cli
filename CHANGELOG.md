# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

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
