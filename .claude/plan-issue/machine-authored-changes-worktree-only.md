- `Engine.authored_changes` is `git status` less pre-existing dirt: uncommitted changes only.
  A path can reach `HEAD` after `run.start_sha` without passing through it: a manual commit,
  and `run start`'s own artifact regeneration (`check_artifacts(None)` runs after the run row,
  so a regenerate-only artifact commits `chore(<name>): regenerate` after `start_sha`). To
  regenerate at a close instead, use the marker `check` from `artifact-stale-check-fixtures.md`,
  with a `regenerate` that also removes the marker (#235, probed).
