# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `env` on `[project.<name>]`: environment for the default suite's runs and
  collection, with the same semantics as an override's `env` (`${VAR}` expands
  from the environment at invocation). An override's `env` layers on top for
  its own suite. Previously only override suites could declare environment,
  leaving a default suite that reads an endpoint from a variable with no
  registry-level way to receive it (#16).

### Fixed

- `tdd target` refuses a name that is not a collected test in the cycle's
  projects, suggesting the closest collected ids — previously any string was
  recorded as the target and failed later, misattributed, as `not_found` (#15).

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
