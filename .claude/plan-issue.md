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
- A refusal's `reason` is under `result.reason`, never at the envelope's top level
  (`envelope.failure(error, **result)`). Say so in any cycle that asserts one.
- A static guard test that greps the source must be run against the design it guards, not
  only against today's tree. Issue 142's write guard matched `.unlink(`, `mkdtemp(` and
  `rmtree(`, which were also the method names the plan gave the new seam, so every migrated
  call site still matched. Its spawn guard matched the word "subprocess" in two comments.
  Probe the regex on a scratch copy of the *after* state, and match code, not prose.
- Moving a call between modules breaks tests that patch through the old module
  (`monkeypatch.setattr(adapters.pytest_adapter.tempfile, ...)`). Grep `tests/` for
  `<module>.<name>` before declaring a move, and list the hits in `modifies_tests`.
- Anything that spawns a process belongs in `src/tddcli/actor.py`: `tests/test_actor_seams.py`
  fails a spawn or a worktree write anywhere else. A cycle that adds one names `actor.py` in
  `files`.
- Split mode (issue 142) is tested through `conftest.sudo_shim`, a stand-in for sudo that does
  not change uid. `split_runner` and `split_client` put the in-process CLI in either role.
- `CHANGELOG.md` is hand-edited under `## [Unreleased]` (see `RELEASING.md`).
- There is no `docs/INVARIANTS.md` and no `perturb/` ledger in this repo.
- `gitutil.tree_hash` is a content hash from #146 on (throwaway index + `git add -A`): staging or
  committing alone is not a change. A test that closes a cycle with no refactor edit and expects
  the cycle's own close-sweep suite to run must make a content edit first, or the §6.1 skip fires.
- A plan that makes a dead condition live must probe what its consequent skips. #146's
  `skip_own` had never fired, and it silently dropped the cycle's lint/typecheck gates as well.
- To find the test blast radius of a change to what a phase runs, simulate the whole change
  with a quick hack in a scratch `git worktree` and run the suite there. For #148 it found
  exactly 6 breaking tests, 3 of them in adoption (`tests/test_advance_adoption.py`), which
  reads the adopted target's outcome from the verdicts the run already produced.
- Narrowing a suite to one test: appending a pytest node id to a **path-scoped**
  `test_command` (`pytest tests/`) still runs the whole path. Narrow with the owning suite's
  collect command (`PytestAdapter._collect_cmd_for`). vitest's `-t` is an unanchored regex over
  the space-joined `fullName`. Anchor it and escape only the JavaScript metacharacters.
- exec ids are file paths, so the `_disambiguate`-resolved adoption branch cannot be reached
  from an exec end-to-end test. Only a single-candidate adoption can.
