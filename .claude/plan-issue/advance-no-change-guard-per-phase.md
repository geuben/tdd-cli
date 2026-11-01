- `advance`'s `no_change_since_last_run` guard compares the tree with the last invocation **of
  the same phase**. The first GREEN after RED therefore runs on an unchanged tree. With a flaky
  target (an execution counter outside the repo) GREEN is confirmed with nothing staged and
  `commit: null`. Any GREEN-side rule over the staged set must say what an empty set does (#235).
