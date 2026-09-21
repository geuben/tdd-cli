# plan-issue notes for tdd-cli

- One project, `tddcli`, root `.`. Test ids are `tests/<file>.py::<test>`. Because the root is
  the repository, `README.md`, `docs/`, `SECURITY.md`, `CHANGELOG.md` and `pyproject.toml` are
  in-project: list them in a cycle's `files`, not in `ancillary_files`.
- The referee is the released `tdd` on `PATH`, never an editable install of the working tree
  (see the note at the top of `tdd.toml`). A plan that raises `SCHEMA_VERSION` needs the frozen
  snapshot referee described in `tasks/issue-129-gates-before-suite.md`'s Execution section.
- Tests drive the CLI in-process through `conftest.run_cli`, which does `json.loads` on stdout.
  A verb or flag argparse does not know yet exits 2 with empty stdout, so the RED dies in
  `json.JSONDecodeError`, not an assertion. A cycle that adds a verb lists `src/tddcli/cli.py`
  in `stub_expected` and stubs the subparser with a `failure(..., reason="not_implemented")`
  handler.
- Because the CLI runs in-process, anything `main` installs process-wide (the actor, from
  issue 142) leaks between tests. Reset it in an autouse fixture.
- A new `tdd docs` topic needs three things that move together: the `Topic` in
  `src/tddcli/docs.py`, the `force-include` line in `pyproject.toml`, and the file. Tests in
  `tests/test_docs_command.py` enforce the first two.
- `CHANGELOG.md` is hand-edited under `## [Unreleased]` (see `RELEASING.md`).
- There is no `docs/INVARIANTS.md` and no `perturb/` ledger in this repo.
