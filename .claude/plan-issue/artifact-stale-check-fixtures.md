- From #110 on, an artifact that is stale and unresolved (its `check` fails and there is no
  `regenerate` hook, or the hook commits nothing) refuses `tdd run start` with
  `reason: "stale_artifact"` and replies `fix_regression` at cycle close. A test that wants a run
  to open and then go stale must declare `check = "test ! -f <tmp_path>/marker"` and create the
  marker after `run start`. The marker sits outside the repo, so it changes no tree hash. A
  bare `check = "false"` now only reaches the refusal. Removing the marker is enough for the
  next `advance` to close the cycle. The unchanged-retry guard does not fire on it (probed for #110).
