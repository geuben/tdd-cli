- Socket permissions in tests (#179). An account that cannot open a unix socket is stood in
  for by `chmod 0` on it: its owner then gets `PermissionError(13)` on connect, and
  `wire.Connection` raises `LedgerUnreachable` with that as `__cause__`. Skip such a test as
  root (`skipif(os.geteuid() == 0, ...)`), as `tests/test_split_runner.py` does. A socket's
  group cannot be asserted with the caller's primary group: on Linux a new file's gid is
  already the egid, so the test passes without any `chown`. On macOS it is the parent
  directory's (`/private/tmp` is `wheel`). Pick a group the caller belongs to that differs
  from the gid a fresh file in `/tmp` gets, and skip only when there is none.
