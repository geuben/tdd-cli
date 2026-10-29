- Host-ledger fixtures for the ledger service (#185). Build them by hand in the service's
  `home` (`Ledger(Path("/<slug>"), path=home / "<slug>.sqlite3", source="vm-1")` + `insert`):
  the slug is the file's stem. `Ledger.insert` does not stamp the ledger's `source`: pass
  `source=` on `run` and `plan_contract` rows yourself, or they are recorded as `local`.
  `fleet` answers carry clock-moving fields (`last_activity_age_s`, `elapsed_s`) and a live
  run's `metrics` wall clock grows, so compare two answers through a projection, never whole.
  To show a path needs no write access, `chmod 0o444` the ledger before anything opens it and
  never restore it: a failed read-write open leaves `-wal`/`-shm` at 0444, and writers keep
  failing (`attempt to write a readonly database`) after the file's mode is put back.
  `Ledger(...)` writes on every open (it upserts `schema_version`); `open_readonly` does not.
