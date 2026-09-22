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
- **On a single-user install the ledger is writable by the account that runs
  the agent.** It has no triggers, hash chain or signature: an agent that looks
  for it can edit it, and nothing records that it did. `tdd doctor` reports
  this as `mode: single`. Where the record has to hold against the agent
  itself, use split mode (`tdd docs split`): a separate runner account owns the
  ledger, reached through one `sudoers` rule, and runs the agent's commands as
  the agent. Split mode adds a privilege boundary to your machine; review the
  two sudoers lines it needs as you would any other.
- Split mode does not make a test report trustworthy. Suites run as the agent,
  and the runner parses what they write as data.
- `tdd fleet` opens the ledger read-only and never writes.
- Worker leases live in `~/.cache/tdd-cli/leases` and contain hostnames and
  pids, nothing else.
- tdd-cli makes no network calls.

## Reporting a vulnerability

Report privately via GitHub's
[private vulnerability reporting](https://github.com/geuben/tdd-cli/security/advisories/new)
rather than a public issue. Reports are acknowledged on a best-effort basis;
this is a solo-maintained project.
