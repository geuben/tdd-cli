- A new `Ledger` read that `render.py` calls (`_time_summary`, `friction_log`, `metrics`) runs on
  a split-runner guest too, through the socket. Classify it in `GUEST_READS`, and give it a
  `run_id`/`cycle_id` parameter. `tests/test_ledger_service.py::test_a_guest_renders_its_own_friction_log`
  fails with `method_not_allowed` if it is `HOST_ONLY`. The CHANGELOG entry carries the usual
  "upgrade the host with or before its guests" line, because an older host refuses the new
  read (#249; precedents: `delivered_run` in 0.17.0, `reference_paths` in 0.18.0).
