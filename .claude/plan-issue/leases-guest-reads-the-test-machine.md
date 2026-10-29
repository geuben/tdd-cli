- In `tests/test_remote_leases.py` the ledger service runs in the test process, so the guest and
  the "host" share `os`. The service's budget is pinned by `TDD_CORE_BUDGET=12`, but anything the
  guest reads from the machine (`os.sched_getaffinity`, `os.cpu_count`) is the CI box's. A
  guest-side cap made `== 12` / `== 6` assertions depend on the test machine's core count (#190:
  2 failures on a 6-core host, 3 on a 4-core one). Pin the guest's reading in that file's autouse
  fixture (`monkeypatch.setattr(os, "sched_getaffinity", ..., raising=False)`, so it also works
  on macOS, which lacks it) and never patch `leases._total_cores`, which is the host's.
