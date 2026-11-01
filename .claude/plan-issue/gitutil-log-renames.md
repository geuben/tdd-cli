- `git log --name-only` (and `git diff --name-only`) detect renames by default, so a rename is
  named only by its **new** path and the old one never appears. A set of "paths a commit range
  touched" needs `--no-renames`, which names both. A removal is always named. Probed on git
  2.43 (#232). `git check-ignore --no-index` matches a path that does not exist on disk.
