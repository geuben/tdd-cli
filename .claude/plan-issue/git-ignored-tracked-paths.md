- `git status` (so `gitutil.changed_paths`, `authored_changes`, `classify`) never lists an
  untracked ignored file. A path the ignore rules match reaches tdd-cli only when it is
  **tracked** at HEAD. `git check-ignore` skips tracked paths unless given `--no-index`, and
  exits 1 when nothing matches. `git add -- <tracked file under an ignored directory>` stages it
  but exits 1, so `gitutil.add` raises. Probe with a tracked ignored file (`git add -f`), not an
  untracked one, or the bug will not reproduce (#98).
