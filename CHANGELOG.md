# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- Artifact regeneration now stages the artifact's own path — and the paths of
  its upstream artifact chain — in the `chore(<name>): regenerate` commit, not
  only `generated = true` paths. Previously a regenerate hook that rewrote an
  upstream spec (e.g. `schema/openapi.json`) left it dirty for the whole run:
  it was never committed, CI compared a stale committed spec against a fresh
  committed client and reported drift, and every phase commit re-flagged the
  file as `undeclared_file_touched`.

## [0.1.0] - Unreleased

Initial release.

- `tdd --version`; every JSON envelope carries `envelope_version`.
- Ledger schema versioning: older ledgers are migrated forward on open; a
  ledger written by a newer tdd-cli is refused with a clear error.
- Third-party adapters via the `tddcli.adapters` entry-point group
  (built-in names cannot be shadowed).
- Windows is refused at startup (`reason: "unsupported_platform"`); use WSL.
- Example Claude Code hooks (Stop + PreToolUse) in `examples/claude-code-hooks/`.
- SECURITY.md documenting the command-execution trust model.
- Ledger-backed TDD process controller: phase is derived from observed test
  execution, never asserted by the caller.
- Plan contracts in YAML front-matter, hashed at the committed blob.
- Standard, pin, and contract cycle kinds.
- pytest and vitest adapters.
- Phase-derived staging and committing; artifact regeneration in separate commits.
- Machine-wide worker leases so concurrent agents share cores.
- `tdd fleet`: read-only view of every agent's run on a repository.
- Fidelity metrics, typed blockers, friction-log rendering.
