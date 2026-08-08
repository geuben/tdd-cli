# Security

## Trust model

**Running `tdd` against a repository executes that repository's declared
commands.** `tdd.toml` declares shell commands — `test_command`, `lint`,
`typecheck`, artifact `regenerate`/`check` — and tdd-cli runs them with your
privileges, exactly as `make`, `npm test`, or a pre-commit hook would. Review
`tdd.toml` (and the test suite it points at) before running tdd-cli against a
repository you did not write. There is no sandbox; sandboxing belongs to the
agent harness, not this tool.

Other properties worth knowing:

- The ledger lives outside the worktree (`~/.local/share/tdd-cli/`) and is
  plain SQLite. It records test ids, file paths, diffs (for sensitivity
  checks), and executor identity — treat it with the same sensitivity as the
  repository itself.
- `tdd fleet` opens the ledger read-only and never writes.
- Worker leases live in `~/.cache/tdd-cli/leases` and contain hostnames and
  pids, nothing else.
- tdd-cli makes no network calls.

## Reporting a vulnerability

Report privately via GitHub's
[private vulnerability reporting](https://github.com/geuben/tdd-cli/security/advisories/new)
rather than a public issue. Reports are acknowledged on a best-effort basis;
this is a solo-maintained project.
