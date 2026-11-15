- Without `-z`, `git status --porcelain=v1` prints a rename or copy as `old -> new` (either
  column: `R `, `RM`, ` R` for an intent-to-add file, `C ` under `status.renames=copies`) and
  C-quotes a path with a space or a non-ASCII character; `git diff --name-only` quotes non-ASCII
  only. A quoted path matches no project root, so `staging.classify` calls it `outside`, flags it
  and never stages it: no crash, just a silently dropped file. Once #258 lands
  (`tasks/issue-258-git-status-renames-and-quoting.md`), `status_porcelain` and `staged_paths`
  read `--no-renames -z`. Any new git call that lists paths takes `-z`, and `--no-renames` where
  git can detect renames (probed on git 2.43). `git status --no-renames` needs git 2.18+.
