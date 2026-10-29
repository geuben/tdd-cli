- pytest-json-report puts a failure on the phase that failed, and a test whose `call` passed but
  whose `teardown` raised is `outcome: "error"` with only `teardown` carrying `longrepr`/`crash`.
  A `session`-scoped fixture's teardown error lands on the **last test that ran** (on that xdist
  worker), even a static one. The adapter's target lookup `hit.get("call") or hit.get("setup")`
  never reads `teardown`, and a passed `call` is a truthy dict, so it returns an empty longrepr.
  `XPASS(strict)` has no `crash` at all (`longrepr` is `[XPASS(strict)]`), and under xdist every
  `longrepr` starts with a `[gw0] linux -- Python …` header line, so "first line" of a longrepr is
  never the message. Probed 2026-10-29 for #105.
