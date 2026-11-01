- A close that ends the run `blocked` without calling `close_cycle` leaves the cycle open in
  `AWAITING_REFACTOR`. `resume --unblock` reopens the run at that cycle, and the next `advance`
  re-enters `_handle_refactor` from the top: annotations, REFACTOR commit, artifacts, sweep, then
  the gate again. So a hold needs no "already blocked" state to re-check, and the re-run sweep is
  usually the §6.1 skip. A hold at the *last* cycle is different: today's run-close gate closes the
  cycle first, so an unblock replies `complete` and leaves the run's `outcome` NULL (`reopen_run`
  clears it and nothing ends the run again). Probed for #234.
