- From #110 on, an artifact that still records `stale_artifact` (its `check` fails and there is
  no `regenerate` hook, or the hook commits nothing) refuses `tdd run start` with
  `reason: "stale_artifact"` and replies `fix_regression` at cycle close. An inherited artifact
  outside the run's reachable set (`artifact_stale_inherited`, #99) does not. A test that wants
  a run to open and then go stale must declare `check = "test ! -f <tmp_path>/marker"` on an
  artifact the plan's own project produces, and create the marker after `run start`. The marker
  sits outside the repo, so it changes no tree hash. A bare `check = "false"` on such an
  artifact now only reaches the refusal. Removing the marker is enough for the next `advance` to
  close the cycle; the unchanged-retry guard does not fire on it (probed for #110).
- #99 and #110 both rewrite `Engine.check_artifacts`'s `if not resolved:` branch. #110 is
  planned on top of #99 and must land after it.
