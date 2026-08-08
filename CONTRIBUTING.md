# Contributing

Thanks for your interest in tdd-cli.

## Development setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/geuben/tdd-cli
cd tdd-cli
uv sync
uv run pytest
```

## Ground rules

- The design is specified in [docs/PRD.md](docs/PRD.md). Requirement ids
  (`R9.14`, `§6.2`) in the source refer to that document. Changes that alter
  specified behaviour should update the PRD in the same PR.
- The core invariant is non-negotiable: **process state is derived from
  observed test execution, never asserted by the caller.** No command may
  accept a phase, and no file an agent edits may claim progress.
- Every behaviour change needs a test. The suite is fast; run all of it.
- Lint with `uv run ruff check src tests`.

## Pull requests

- Keep PRs focused — one concern per PR.
- Write commit messages that state the behaviour change, not the mechanics.
- CI must pass (tests on Python 3.11–3.13, lint, build + wheel smoke test).

## Reporting bugs

Open an issue with the command you ran, the JSON envelope it emitted, and
what you expected. `tdd status` output and the relevant ledger rows help.
