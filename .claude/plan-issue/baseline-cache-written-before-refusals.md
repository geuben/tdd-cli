- `_probe_projects` (serial path) writes the `--reuse-baselines` cache before `cmd_run_start`
  runs any refusal check, and a reused probe skips R9.5a's checks (`if name in reused: continue`).
  A new baseline refusal is therefore undone by a retry with `--reuse-baselines` on the same tree,
  unless the cache write is guarded too. Plan a cycle that runs `run start --reuse-baselines` twice
  and asserts that both are refused (#99, probed).
