- The referee reads this repo's `tdd.toml` on every command, so a plan that adds a gate
  (`lint`, `typecheck`) to it mid-run turns that gate on from the next close sweep. Add it in the
  plan's last cycle, after the code passes it, or every earlier close sweep fails. Editing
  `tdd.toml` mid-run also records one `config_changed` integrity event per new hash
  (`advance._check_config_drift`). Name it in the Execution section as expected (#210).
