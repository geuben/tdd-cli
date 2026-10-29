- A flaky test is a pytest test that counts its own executions in a file **outside the
  repository** (`tmp_path / "count"`, its absolute path written into the test source) and fails on
  chosen ones. A counter inside the repo changes the content tree hash and dirties the worktree.
  In the `repo` fixture, probed for #73: `run start`'s baseline is execution 1. RED and GREEN's
  target-only first run never execute it. GREEN's whole-suite run is 2, and a close sweep after a
  content edit is 3. Collection does not execute tests.
- To run one end-to-end setup per case in a single table-driven test, copy the fixture with
  `shutil.copytree(repo, tmp_path / name)` before any run starts. The ledger is keyed by the
  repository path (`gitutil.repo_identity`), so each copy is an independent repo and ledger.
