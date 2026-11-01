- `render.friction_log` never prints a run-level integrity event (`cycle_id` NULL): it prints
  events only inside each cycle's block (`events.get(cycle["id"])`). `undeclared_file_dropped`
  appears nowhere in the friction log. Run-level kinds are counted only in `tdd metrics`
  (`integrity_events`) and on `tdd progress`' summary line (`kind×n`). A plan that wants a
  run-level event *seen* in the friction log must render it itself, from
  `ledger.event_details(run_id, kind)` (#232). #98's plan said they render as header counts;
  that is `tdd progress`, not the friction log.
- A write at run close must come before the run ends (`close_cycle` on the last cycle,
  `ledger.end_run` in `cmd_cycle_skip`). On a split-runner guest, `service._Session._closed`
  refuses a write to an ended run with `run_closed`; `add_note` is its only exemption.
