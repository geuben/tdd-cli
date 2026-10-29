---
closes: 185
cycles:
  # -- Phase 1: the report socket, on the service ------------------------------------------
  - n: 1
    project: tddcli
    title: "the report socket answers metrics, fleet and log as the admin socket does"
    test: "tests/test_ledger_report_socket.py::test_the_report_socket_answers_as_the_admin_socket_does"
    files: ["src/tddcli/service.py"]
    commit_red: "test: the report socket answers metrics, fleet and log"
    commit_green: "feat: the ledger service listens on an optional report socket"
    commit_refactor: "refactor: tidy the report listener"
  - n: 2
    project: tddcli
    title: "the report socket refuses every other method"
    test: "tests/test_ledger_report_socket.py::test_the_report_socket_refuses_every_other_method"
    files: ["src/tddcli/service.py"]
    commit_red: "test: the report socket refuses every other method"
    commit_green: "feat: the report socket answers metrics, fleet and log alone"
    commit_refactor: "refactor: tidy report socket dispatch"
  - n: 3
    project: tddcli
    title: "the report socket reads ledgers it could not write"
    test: "tests/test_ledger_report_socket.py::test_the_report_socket_reads_ledgers_it_cannot_write"
    files: ["src/tddcli/service.py"]
    commit_red: "test: the report socket reads a ledger it cannot write"
    commit_green: "feat: the report socket opens ledgers read-only"
    commit_refactor: "refactor: tidy read-only views"
  - n: 4
    project: tddcli
    title: "the report socket is mode 660"
    test: "tests/test_ledger_report_socket.py::test_the_report_socket_is_mode_660"
    files: ["src/tddcli/service.py"]
    commit_red: "test: the report socket is mode 660"
    commit_green: "feat: the report socket is mode 660, like a source's"
    commit_refactor: "refactor: tidy socket modes"
  - n: 5
    project: tddcli
    title: "a report socket on the admin socket's path is refused"
    test: "tests/test_ledger_report_socket.py::test_a_report_socket_on_the_admin_path_is_refused"
    files: ["src/tddcli/service.py"]
    commit_red: "test: a report socket on the admin path is refused"
    commit_green: "feat: report_socket must not be admin_socket"
    commit_refactor: "refactor: tidy report config checks"
  # -- Phase 2: which socket the CLI reads from --------------------------------------------
  - n: 6
    project: tddcli
    pin_cycle: true
    title: "with no report socket, a forbidden admin socket is ledger_unreachable for every read"
    test: "tests/test_ledger_admin.py::test_a_forbidden_admin_socket_with_no_report_socket_is_unreachable"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: pin — a forbidden admin socket with no report socket is ledger_unreachable"
  - n: 7
    project: tddcli
    title: "tdd ledger metrics, fleet and log fall back to the report socket"
    test: "tests/test_ledger_report_socket.py::test_ledger_reads_fall_back_to_the_report_socket"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: ledger reads fall back to the report socket"
    commit_green: "feat: tdd ledger metrics, fleet and log fall back to the report socket"
    commit_refactor: "refactor: tidy the report socket fallback"
  # -- Phase 3: trend tracking -------------------------------------------------------------
  - n: 8
    project: tddcli
    title: "metrics reports each cycle's time"
    test: "tests/test_time_report.py::test_metrics_reports_each_cycles_time"
    files: ["src/tddcli/render.py"]
    modifies_tests: ["tests/test_time_report.py::test_metrics_reports_suite_time_by_phase_and_the_wall_clock"]
    commit_red: "test: metrics reports each cycle's time"
    commit_green: "feat: tdd metrics reports a per-cycle time table"
    commit_refactor: "refactor: tidy the per-cycle time table"
  - n: 9
    project: tddcli
    title: "metrics --since keeps the runs still open or ended since then, on both sockets"
    test: "tests/test_ledger_report_socket.py::test_metrics_since_keeps_runs_open_or_ended_since_then"
    stub_expected: ["src/tddcli/cli.py"]
    files: ["src/tddcli/cli.py", "src/tddcli/service.py", "src/tddcli/render.py"]
    commit_red: "test: metrics --since keeps runs open or ended since then"
    commit_green: "feat: tdd ledger metrics --since"
    commit_refactor: "refactor: tidy the since filter"
  - n: 10
    project: tddcli
    title: "metrics --since refuses a time with no UTC offset"
    test: "tests/test_ledger_report_socket.py::test_metrics_since_refuses_a_time_with_no_offset"
    files: ["src/tddcli/service.py"]
    commit_red: "test: metrics --since refuses a time with no offset"
    commit_green: "feat: metrics refuses a bad since with bad_since"
    commit_refactor: "refactor: tidy since parsing"
  # -- Phase 4: docs -----------------------------------------------------------------------
  - n: 11
    project: tddcli
    refactor_cycle: true
    title: "document the report socket, --since and the per-cycle table"
    files: ["docs/split-runner.md", "README.md", "CHANGELOG.md"]
    commit_refactor: "docs: the report socket, tdd ledger metrics --since and per-cycle times"
---

# Issue 185: a read-only report socket for the operator's dashboards

## Context

[#185](https://github.com/geuben/tdd-cli/issues/185) follows #169 (the ledger service) and #147
(the time report). The service answers host-wide `metrics`, `fleet` and `log` only on its admin
socket. `service.py` creates that socket at `ADMIN_MODE = 0o600`, so a dashboard that wants
host-wide timing must be given the whole admin surface: `add-source`, `remove-source`, `import`
and `bind`. On geuben/machine, dispatch-console (account `orchestrator`) needs to read the
ledger and nothing else. #179 describes the same problem for `bind`, and its plan is open as
PR #196.

The issue asks for:

1. **An optional `[service] report_socket`.** It answers `metrics`, `fleet` and `log` only, with
   the same results the admin socket gives. Any other method is `method_not_allowed`. It opens
   ledgers read-only (`open_readonly`), so a client can never write. Its mode and directory
   follow the source sockets (660), so the operator lets one account in with an inherited ACL
   on the directory. With no setting there is no socket, and nothing changes.
2. **For trend tracking** (the issue: "nice to have, can be a follow-up"):
   `metrics --since <ts>`, so a poller does not re-read every run, and a per-cycle time table
   in `metrics`' JSON (cycle `opened_at`/`closed_at`, suite runs and `suite_s` per cycle).

Done when: with `report_socket` set, a client on it gets `metrics`, `fleet` and `log`, and is
refused every admin verb and every ledger write. Without it, nothing changes.
`docs/split-runner.md` documents the socket and whose it is.

## Design decisions (locked)

Each entry says what decided it. Executors do not re-open these.

1. **Build the trend-tracking items now** (evidence: `/plan-issue`'s scope policy). The issue
   allows them to be a follow-up, but it does not call them a non-goal, and both can be
   built now. The per-cycle table is computed already: `render._time_summary` builds a
   `cycles` list, and `render._time_json` drops it. PRD §11.1 already says `tdd metrics`
   reports suite time "per cycle". Cycles 8 to 10.
2. **Config: `[service] report_socket`** (evidence: the issue names the key).
   - `ServiceConfig` gains `report_socket: Path | None = None`, with a default, so today's
     configs load unchanged.
   - With the key absent the service opens no report socket, and nothing changes
     (convention: a new knob defaults to today's behaviour).
   - There is **no `report_group` key** (evidence: the issue says the socket follows the
     source sockets, and the operator admits one account with an inherited ACL on the
     socket's directory). The socket gets whatever group a new file gets, as a source's socket
     does. docs/split-runner.md says the directory is what keeps it to one account (cycle 11).
3. **`report_socket` must not be `admin_socket`** (convention: `load_config` already refuses a
   config without `admin_socket`, and `runner.load` refuses `ledger_socket` together with
   `ledger_home`). The two paths are compared as `Path` values. A report socket on the admin
   path would unlink the admin socket, because `_Listener` replaces any socket file already at
   its path. The operator would lose the admin socket without any error. The check is
   `ServiceConfigError("[service] report_socket must not be admin_socket")`. Cycle 5 pins the
   refusal and that its message names `report_socket`.
4. **The report socket answers `metrics`, `fleet` and `log`, and nothing else, not even `ping`**
   (evidence: the issue says "answers `metrics`, `fleet` and `log` only ... Any other method is
   `method_not_allowed`").
   - Add `REPORT_METHODS = frozenset({"metrics", "fleet", "log"})`.
   - The service keeps the listener as its own attribute, `Service.report_listener`, not in
     `Service.listeners`, whose keys are source names. `Service.start` opens it when
     `report_socket` is set, and `Service.stop` closes it. No test asserts the close: `serve`
     exits after `stop`. It is stated so that the suite does not leak a listener thread per
     test.
   - A connection on the report listener is a `_Session` with `source=None` and
     `report_only=True`. `_Session.answer` checks `report_only` **before** the `ping` branch
     and hands the request to `Service.report(method, args, kwargs)`.
   - `Service.report` refuses a method outside `REPORT_METHODS` with
     `_refusal("method_not_allowed", f"{method} is not answered on the report socket")`.
   - `Service.report` answers `metrics`, `fleet` and `log` by calling the same `Service.metrics`,
     `Service.fleet` and `Service.log` that `Service.admin` calls. So the two sockets cannot
     disagree, except for the read-only open (decision 5). Cycle 1 is the parity check.
   - If #179 (PR #196) has landed when this runs, it will have added a bind listener and a
     `bind_only` session flag the same way. Follow that shape, and keep the two flags separate.
5. **Report-socket reads open ledgers read-only; admin-socket reads do not change** (evidence:
   the issue says "It opens ledgers read-only (`open_readonly`)" and "Without it, nothing
   changes").
   - `Service.metrics(repo=None, *, since=None, readonly=False)` and
     `Service.log(repo, run_id, *, readonly=False)`. With `readonly=True` they open each ledger
     with `ledger_mod.open_readonly(path, source=None)` instead of `ledger_mod.Ledger(...)`,
     and skip a path for which it returns `None`, as `Service.fleet` already does.
   - `Service.fleet` already reads through `open_readonly` and is unchanged.
   - `Service.report` passes `readonly=True`. `Service.admin` keeps the default, so the admin
     socket still opens `Ledger(...)`, which migrates an old ledger on open.
   - Probed: `open_readonly` on a mode-0444 ledger renders both `render.metrics` and
     `render.friction_log`. `Ledger(...)` on that file fails with
     `sqlite3.OperationalError: attempt to write a readonly database`, because it upserts
     `schema_version` on every open.
6. **Mode 660** (evidence: the issue says the socket follows "the source sockets (660)"). The
   report listener `chmod`s its socket to `GUEST_MODE`. `_Listener` today picks
   `ADMIN_MODE if source is None else GUEST_MODE`, and a report listener has `source=None`. So
   `_Listener` takes the mode, or a role, explicitly. Do not give the report listener a fake
   source name. Pinned by cycle 4.
7. **`tdd ledger metrics`, `fleet` and `log` fall back to the report socket** (evidence: PRD
   §13.4 R13.8 makes the command surface the interface, and `tdd ledger` is the only client of
   the service that tdd-cli ships. Without a fallback, the dashboard's account gets
   `ledger_unreachable` from all three verbs (probed). Convention: #179's proposal, and its
   plan's decision 8, fall back the same way for `bind`).
   - The helper lives in `cli.py`. It connects to `cfg.admin_socket`. If the connect fails
     (`wire.Connection`'s constructor raises `LedgerUnreachable`) and `cfg.report_socket` is
     set, it connects to `cfg.report_socket` and sends the request there instead. If no report
     socket is configured, the `LedgerUnreachable` propagates, so the verb fails with
     `reason: "ledger_unreachable"`, as today (cycle 6).
   - A connection that was made and then dropped is never retried on the other socket.
   - Build the `wire.Connection` in the helper rather than calling `wire.call`, so that a failed
     connect can be told apart from a failed request. `wire.py` is unchanged.
   - Only `_ledger_metrics`, `_ledger_fleet` and `_ledger_log` use the helper. Every other
     `tdd ledger` verb still talks only to the admin socket. There is no `--socket` flag: the
     issue asks for none, and the fallback is enough for the dashboard.
   - If #179's connect-time fallback helper is already in `cli.py` when this runs, give it the
     fallback socket as a parameter and use it for these three verbs. Do not write a second
     copy. The cycle 7 test is the same either way.
   - The dashboard's account must still be able to read `/etc/tdd-cli/ledger.toml`, and that
     file must be owned by root (convention: #169's `_ledger_verb` loads the config, held to
     `runner.toml`'s trust rule, PRD §13.2 R13.10). docs/split-runner.md says so.
8. **A per-cycle time table: `time.cycles` in each run of `metrics`** (evidence: the issue names
   the fields; convention: `render._time_summary` already builds `cycles`, and `_time_json` is
   `tdd metrics`' view of that summary).
   - Each entry is
     `{"ordinal", "opened_at", "closed_at", "wall_clock_s", "suite_s", "runs"}`, in ordinal
     order. `opened_at` and `closed_at` are the ledger's own strings. `closed_at` and
     `wall_clock_s` are `None` while the cycle is open. Seconds are rounded to one decimal, like
     the rest of `_time_json`.
   - `_time_summary`'s `cycles` entries gain `opened_at` and `closed_at` (`cycle_times` already
     selects both). The friction log's `## Time` table reads only the keys it reads today, and
     does not change.
   - This reaches every `metrics`: `tdd metrics`, a guest's `tdd metrics`, `tdd ledger metrics`,
     and both sockets. They all go through `render.metrics`. Additive: no existing key changes.
9. **`--since` keeps a run when it is still open or ended at or after the given time**
   (evidence: the issue says "so a poller doesn't re-read every run each time").
   - A poller needs every run whose figures could have changed since its last poll. Those are
     the runs that are still open (`ended_at IS NULL`) and the runs that ended since then.
   - Filtering on `started_at` instead would drop a run that was in flight at the last poll and
     finished afterwards: the completed runs a cycle-time chart exists to show.
   - `run resume` clears `ended_at` and `run abandon` sets it again (`Ledger.end_run`,
     `reopen_run`, `abandon_run`). So a resumed or abandoned run comes back.
   - The boundary is inclusive (`ended_at >= since`), so a run that ended at the very instant
     of the last poll is read again rather than lost.
   - The filter lives in `render.metrics(ledger, worktree, since=None)`, over `runs_in`. It
     compares **parsed** datetimes, `datetime.fromisoformat(run["ended_at"]) >= since`, never
     strings. Mechanism trap: a text comparison is wrong across offsets (`+01:00`) and
     fractional seconds.
   - Where it is offered (evidence: the issue puts it in the service's `metrics`, for the
     dashboard's poller):
     - the `metrics` wire method takes a `since` keyword on both sockets;
     - `tdd ledger metrics` takes `--since TIME` and passes it on verbatim as `since=` (and
       `since=None` when the flag is absent);
     - `tdd metrics` (single machine or guest) does not get the flag (No future-proofing).
   - `Service.admin`'s and `Service.report`'s `metrics` branches read `kwargs.get("since")`.
     They never splat `**kwargs` into `Service.metrics`.
10. **Which `since` values are accepted** (convention: the ledger writes every timestamp as a
    UTC-offset ISO 8601 string, `ledger.now()`; a refusal is `_refusal(code, ...)` and reaches
    the envelope as `result.reason`).
    - Parse with `datetime.fromisoformat`. `requires-python >= 3.11`, so `Z` parses.
    - **Accepted**: a string that `fromisoformat` parses **and** that carries an offset. Two
      spellings that name the same instant are equivalent: `2026-09-01T10:20:00+00:00`,
      `2026-09-01T10:20:00Z`, `2026-09-01T11:20:00+01:00` and
      `2026-09-01T10:20:00.000000+00:00`. Cycle 9 pins the whole set.
    - **Rejected**, with `_refusal("bad_since", ...)`:
      - a time with no offset (`2026-09-01T10:20:00`), and a bare date (`2026-09-01`), which
        `fromisoformat` returns as a naive datetime;
      - anything that does not parse (`yesterday`, `""`);
      - a non-string over the wire (`5`).

      A naive time is refused rather than taken as UTC, because the host's local offset would
      shift it silently. Comparing it with the ledger's aware times would also raise
      `TypeError` in the handler thread. Cycle 10 pins every rejected form.
    - The service validates, so wire clients get the same refusal as the CLI. The CLI does
      not pre-check. `_ledger_verb` already turns `LedgerRefused` into
      `failure(..., reason=refusal)`.
    - Message (not asserted): `since takes an ISO 8601 time with a UTC offset, such as
      2026-09-01T10:20:00+00:00: <value>`.
11. **Tests.**
    - The report socket's tests go in a new `tests/test_ledger_report_socket.py`, with its own
      service fixture (below), because `conftest.ledger_service` writes a config with no
      `report_socket`.
    - The pin in cycle 6 extends `tests/test_ledger_admin.py`, which uses `ledger_service`.
    - The per-cycle table test extends `tests/test_time_report.py`, against its `_ledger`
      fixture.
    - Sockets live under `tempfile.mkdtemp(dir="/tmp", prefix="tdd-")` (repo note: AF_UNIX path
      length).
    - A caller that cannot open the admin socket is stood in for by `chmod 0` on it. Its owner
      then gets `PermissionError(13)` on connect, as another account does on a 600 socket. A
      client that cannot write the ledger is stood in for by `chmod 0o444` on the ledger
      file. Both are `@pytest.mark.skipif(os.geteuid() == 0, reason=...)`, after
      `tests/test_split_runner.py`'s `"root reads a mode-000 file"`.

## Deliberate scope cuts (do not build)

- **A real second account, the directory ACL, and forwarding to a dashboard.** **Premise:
  unreachable.** No second account and no ACL-capable setup can be reached from CI. The service
  side is built and tested in full: the methods, the refusals, read-only opening, the mode, the
  config check and the CLI fallback. A different uid is stood in for by mode-000 and mode-0444
  files (decision 11). docs/split-runner.md describes the ACL setup.
- **Refusing a `report_socket` equal to #179's `bind_socket`.** **Premise: blocked.** `bind_socket`
  exists only in #179's unmerged plan (PR #196). Re-evaluation trigger: if `ServiceConfig` has a
  `bind_socket` field when this run starts, do not extend cycle 5. Record it with `tdd note`
  and name it in the PR body, so that it is added as its own change.

Not part of this issue, and so not built (these are not scope cuts): refusing a source whose
socket path is the report socket's. `add-source` already replaces any socket file at its path,
the admin socket's included, and that is unchanged.

## Fake and real divergence

| Seam | In the tests | In production | Ruling |
|---|---|---|---|
| A caller that cannot open the admin socket | the same uid, admin socket `chmod 0` → `PermissionError(13)` on connect | another uid, socket 600 → `EACCES` on connect | acceptable: the same errno reaches the same `wire.Connection` constructor |
| A report client that must never write | the service's own uid, with the ledger file `chmod 0o444`, so any write fails | the service's uid owning a writable file, read through SQLite's `mode=ro` URI | acceptable: the test shows the report path needs no write access to the file. The production guarantee is structural (`open_readonly`) |
| The dashboard's account, let in by a directory ACL | not tested | `setfacl` on the socket's directory | unreachable (scope cut). Documented in cycle 11 |
| A host ledger at an older schema version | not tested | the report socket reads it as is, with no migration | acceptable: `fleet` has done the same since #169. A guest's next open, or an admin read, migrates it |
| The service | `service.Service` in a thread of the test process, on real unix sockets | `tdd ledger serve` under its own account | acceptable: `test_ledger_serve_runs_until_terminated` covers the process wrapper |

## Cycles

All tests call the CLI in-process through `conftest.run_cli`. A refusal's `reason` is read as
`out["result"].get("reason")`, never at the envelope's top level.

### The new test file's helpers

`tests/test_ledger_report_socket.py` is written in cycle 1's RED. Cycles 2 to 5, 7, 9 and 10
reuse its helpers. Imports: `os`, `shutil`, `stat`, `tempfile`, `Path`, `SimpleNamespace`,
`pytest`, `from conftest import run_cli`, `from tddcli import service, wire`, and
`from tddcli import ledger as ledger_mod`.

- `_at(minute) -> str`: `f"2026-09-01T10:{minute:02d}:00+00:00"`, as in `tests/test_time_report.py`.
- `host_ledger(home, runs) -> None`. It writes `home / "somerepo.sqlite3"` (slug `somerepo`) with
  `ledger_mod.Ledger(Path("/somerepo"), path=home / "somerepo.sqlite3", source="vm-1")`, after
  `home.mkdir(parents=True, exist_ok=True)`, and closes it.
  - One `plan_contract` row: `plan_path="tasks/p.md", status="declared",
    declared_cycles='[{"n": 1}]', annotation_keys="[]", registered_at=_at(0), source="vm-1"`.
  - For each `(started, ended, outcome)` in `runs`, in order:
    - a `run` row: `plan_contract_id=<contract>, executor_model="m",
      executor_source="declared", worktree_path="/wt", started_at=_at(started),
      ended_at=_at(ended) or None, outcome=outcome, preexisting_dirty="[]", source="vm-1"`;
    - one `cycle` row: `ordinal=1, kind="standard", projects='["p"]', declared_tests="[]",
      target_tests="[]", phase="CLOSED", head_at_open="0" * 40, opened_at=_at(started),
      closed_at=_at(ended) or None`;
    - one `invocation` row: `phase_at="AWAITING_TEST", project="p", adapter="pytest",
      other_failures="[]", duration_ms=30000, started_at=_at(started)`.

  **Pass `source="vm-1"` on the run and contract rows explicitly.** Probed: `Ledger.insert` does
  not stamp the ledger's source, and a run inserted without it is recorded as `local`. Run
  ids are 1, 2, … in order.
- `TWO_RUNS = [(0, 10, "complete"), (25, None, None)]`: run 1 ended, run 2 live.
- `SINCE_RUNS = [(0, 10, "complete"), (0, 30, "complete"), (25, None, None), (5, 20, "abandoned")]`.
  With since 10:20:
  - run 1 (ended 10:10) is out;
  - run 2 (started before, ended 10:30) is in;
  - run 3 (live) is in;
  - run 4 (ended exactly 10:20) is in.

  The expected ids are `[2, 3, 4]`.
- Fixture `report_service(tmp_path, monkeypatch)`, copied from `conftest.ledger_service`:
  - `sockets = Path(tempfile.mkdtemp(dir="/tmp", prefix="tdd-"))`, and
    `home = tmp_path / "host-ledgers"`;
  - writes `tmp_path / "ledger.toml"` as
    `[service]\nadmin_socket = "<sockets>/admin.sock"\nhome = "<home>"\nreport_socket = "<sockets>/report.sock"\n`;
  - `monkeypatch.setenv("TDD_LEDGER_SERVICE_CONFIG", ...)`, then starts
    `service.Service(service.load_config(cfg))`;
  - yields `SimpleNamespace(service=svc, home=home, dir=sockets, config=cfg, admin=sockets / "admin.sock", report=sockets / "report.sock")`;
  - finally `svc.stop()` and `shutil.rmtree(sockets, ignore_errors=True)`.
- `answer(socket_path, method, *args, **kwargs)`: one `wire.call`, returning its decoded result.
  It returns `exc.refusal` on `wire.LedgerRefused`, `"unreachable"` on
  `wire.LedgerUnreachable`, and `"error"` on `RuntimeError`. Catch `LedgerRefused` and
  `LedgerUnreachable` before `RuntimeError`: both subclass it.
- `run_ids(result) -> list | str`. Given a `metrics` result, it returns
  `[r["run"] for r in ((result.get("repos") or {}).get("somerepo") or {}).get("runs", [])]`.
  Given a string (an `answer` failure), it returns the string unchanged.

### Phase 1: the report socket, on the service

**Cycle 1: `test_the_report_socket_answers_as_the_admin_socket_does`.**
- `host_ledger(report_service.home, TWO_RUNS)`.
- A local helper, `view(socket_path)`, returns a tuple of three items. Strings from `answer`
  pass through unchanged. These projections drop the fields that move with the clock (a live
  run's `wall_clock_s`, `fleet`'s `last_activity_age_s`):
  - `metrics` → `[(r["run"], r["source"], r["outcome"]) for r in m["repos"]["somerepo"]["runs"]]`;
  - `fleet` → `[(r["repo"], r["run_id"], r["source"]) for r in f["runs"]]`;
  - `log`, called as `answer(sock, "log", "somerepo", 1)` → the whole answer.
- Single assertion: `view(report_service.report) == view(report_service.admin)`.
- The admin side is the existing, tested path. Probed on today's tree, its view has
  `[(1, "vm-1", "complete"), (2, "vm-1", None)]` for `metrics`,
  `[("somerepo", 2, "vm-1")]` for `fleet`, and `{"text": "# Implementation Friction Log: tasks/p.md\n…", "source": "vm-1"}`
  for `log`. So the comparison is not vacuous.
- GREEN: `ServiceConfig.report_socket`, read by `load_config` with no checks. `Service.start`
  opens `self.report_listener` when it is set, and `Service.stop` closes it. Its sessions hand
  every request to the existing dispatch.
- EXPECTED FAILURE (probed: `load_config` ignores the key today, so nothing listens):
  `AssertionError: assert ('unreachable', 'unreachable', 'unreachable') == ([(1, 'vm-1', 'complete'), (2, 'vm-1', None)], [('somerepo', 2, 'vm-1')], {...})`.

**Cycle 2: `test_the_report_socket_refuses_every_other_method`.**
- `{m: answer(report_service.report, m, *a) for m, a in OTHER}`, with no sources added. `OTHER`
  is, in order:
  - `("ping", ())`, `("sources", ())`;
  - `("add_source", ("vm-x", str(report_service.dir / "vm-x.sock")))`,
    `("remove_source", ("vm-1",))`, `("bind", ("vm-1", "m"))`;
  - `("import", (str(tmp_path / "x.sqlite3"), "legacy"))`;
  - `("open", (str(tmp_path),))`, `("lease", ())`, `("lease_snapshot", ())`;
  - `("run", (1,))`, `("start_run", ())`, `("insert", ("run",))`.
- Single assertion: the dict `== {m: "method_not_allowed" for m, _ in OTHER}`.
- GREEN: `report_only` sessions, checked before `ping`, and `Service.report` with
  `REPORT_METHODS`. Answer the three methods through the same `Service.metrics`, `fleet` and
  `log` calls the admin socket makes. Do not add read-only opening yet.
- EXPECTED FAILURE (probed on the admin socket, which cycle 1's sessions behave as):
  - `ping` answers `{'source': None, 'executor': None}`, `sources` answers `[]`, and
    `add_source` answers a dict;
  - `remove_source` and `bind` answer `'unknown_source'`, and `import` answers `'unreachable'`;
  - the guest methods are already `'method_not_allowed'`.

  The dict comparison fails on those keys.

**Cycle 3: `test_the_report_socket_reads_ledgers_it_cannot_write`.**
- `@pytest.mark.skipif(os.geteuid() == 0, reason="root writes a mode-0444 file")`.
- `host_ledger(report_service.home, TWO_RUNS)`, then
  `(report_service.home / "somerepo.sqlite3").chmod(0o444)`. Do this **before** anything opens
  the ledger. Do not restore the mode, and do not ask the admin socket anything in this test.
  Probed: a failed read-write open leaves `-wal` and `-shm` files at 0444, which keep failing
  writers after the mode is restored. `tmp_path` is discarded anyway.
- `[isinstance(answer(report_service.report, m, *a), dict) for m, a in (("metrics", ()), ("fleet", ()), ("log", ("somerepo", 1)))]`.
- Single assertion: the list `== [True, True, True]`.
- GREEN: decision 5. `Service.metrics` and `Service.log` take `readonly`, and `Service.report`
  passes `True`.
- EXPECTED FAILURE (probed on today's admin path, which cycle 2's `Service.report` calls): the
  handler thread dies on `sqlite3.OperationalError: attempt to write a readonly database` for
  `metrics` and `log`, and the client sees the connection close. `fleet` already reads
  read-only. So `AssertionError: assert [False, True, False] == [True, True, True]`.
  Probed after the change: `open_readonly` on a clean mode-0444 ledger renders `render.metrics`
  and `render.friction_log`.

**Cycle 4: `test_the_report_socket_is_mode_660`.**
- Single assertion: `stat.S_IMODE(report_service.report.stat().st_mode) == 0o660`.
- GREEN: decision 6.
- EXPECTED FAILURE (reasoned: cycle 1's listener has `source=None`, which `_Listener` gives
  `ADMIN_MODE`): `AssertionError: assert 384 == 432`.

**Cycle 5: `test_a_report_socket_on_the_admin_path_is_refused`.**
- No fixture besides `tmp_path`. Write `tmp_path / "ledger.toml"` as
  `[service]\nadmin_socket = "/tmp/tdd-185-admin.sock"\nreport_socket = "/tmp/tdd-185-admin.sock"\n`.
- Single assertion: `with pytest.raises(service.ServiceConfigError, match="report_socket"): service.load_config(path)`.
- EXPECTED FAILURE (probed: the config loads today, and nothing compares the paths):
  `Failed: DID NOT RAISE <class 'tddcli.service.ServiceConfigError'>`.

### Phase 2: which socket the CLI reads from

**Cycle 6 (pin): `tests/test_ledger_admin.py::test_a_forbidden_admin_socket_with_no_report_socket_is_unreachable`.**
- Decorate with `@pytest.mark.skipif(os.geteuid() == 0, reason="root connects to a mode-000 socket")`.
  Add `import pytest` to the file. It has none today.
- Fixtures `repo`, `ledger_service` (no report socket) and `tmp_path`. Run
  `(ledger_service.dir / "admin.sock").chmod(0)`. Then:
  `outs = [run_cli(repo, "ledger", *v) for v in (("metrics",), ("fleet",), ("log", "--repo", "somerepo", "--run", "1", "--out", str(tmp_path / "log.md")))]`.
- Single assertion: `[o["result"].get("reason") for o in outs] == ["ledger_unreachable"] * 3`.
- **Must pass on arrival.** Probed: today all three answer `ledger_unreachable`. It guards
  decision 7's no-report-socket case before cycle 7 adds the fallback beside it.

**Cycle 7: `test_ledger_reads_fall_back_to_the_report_socket`.**
- The same `skipif` as cycle 6.
- `host_ledger(report_service.home, TWO_RUNS)`, then `report_service.admin.chmod(0)`. Then
  `outs`, built from the same three verbs as cycle 6 (`log` with `--out str(tmp_path / "log.md")`).
- Single assertion: `[o.get("ok") for o in outs] == [True, True, True]`.
- GREEN: decision 7's helper, used by `_ledger_metrics`, `_ledger_fleet` and `_ledger_log`.
- EXPECTED FAILURE (probed: with the admin socket forbidden, each verb answers
  `ledger_unreachable` today): `AssertionError: assert [False, False, False] == [True, True, True]`.

### Phase 3: trend tracking

**Cycle 8: `tests/test_time_report.py::test_metrics_reports_each_cycles_time`.**
- `ledger, _ = _ledger(tmp_path)`, using the file's existing fixture and the `ledger_home`
  fixture. `m = render.metrics(ledger, "/wt")["runs"][0]`.
- Single assertion: `m["time"].get("cycles") == CYCLES`, where `CYCLES` is a module constant:

      [
          {"ordinal": 1, "opened_at": "2026-09-01T10:00:00+00:00",
           "closed_at": "2026-09-01T10:04:00+00:00", "wall_clock_s": 240.0,
           "suite_s": 90.0, "runs": 3},
          {"ordinal": 2, "opened_at": "2026-09-01T10:04:00+00:00",
           "closed_at": None, "wall_clock_s": None, "suite_s": 132.0, "runs": 4},
      ]

  The fixture's numbers are chosen by hand, independently of the code:
  - cycle 1 runs 10:00 to 10:04 with three 30 s suite runs;
  - cycle 2 is open, with suite runs of 30, 42, 30 and 30 s.

  A scratch implementation of decision 8 produced exactly this list.
- **Test-side blast radius** (found by running the whole suite against that scratch change in
  a throwaway worktree: 1 failed, 721 passed):
  `test_metrics_reports_suite_time_by_phase_and_the_wall_clock` asserts the whole `time` dict.
  In GREEN, its expected dict gains `"cycles": CYCLES`. That is declared in `modifies_tests`.
  Do not relax it to a subset of keys.
- GREEN: decision 8.
- EXPECTED FAILURE (probed: `_time_json` has no `cycles` key today): `AssertionError: assert None == [{'ordinal': 1, ...}, ...]`.

**Cycle 9: `test_metrics_since_keeps_runs_open_or_ended_since_then`.**
- `ACCEPTED = ["2026-09-01T10:20:00+00:00", "2026-09-01T10:20:00Z", "2026-09-01T11:20:00+01:00", "2026-09-01T10:20:00.000000+00:00"]`.
- `host_ledger(report_service.home, SINCE_RUNS)`. Then:
  - `by_form = {ts: run_ids(run_cli(repo, "ledger", "metrics", "--since", ts)["result"]) for ts in ACCEPTED}`
    (through the admin socket, which is reachable here);
  - `on_report = run_ids(answer(report_service.report, "metrics", None, since=ACCEPTED[0]))`.
- Single assertion: `(by_form, on_report) == ({ts: [2, 3, 4] for ts in ACCEPTED}, [2, 3, 4])`.
- `stub_expected: src/tddcli/cli.py`: `s.add_argument("--since", help=...)` on the
  `ledger metrics` subparser, read by nothing. Without it argparse exits 2 with empty stdout,
  and the RED dies in `json.JSONDecodeError` (probed).
- GREEN:
  - `render.metrics(..., since=None)` filters as decision 9 says;
  - `Service.metrics` passes `since` through;
  - `Service.admin`'s and `Service.report`'s `metrics` branches parse `kwargs.get("since")` with
    `datetime.fromisoformat` (`None` stays `None`);
  - `_ledger_metrics` sends `since=args.since`.

  Refusals are cycle 10's.
- EXPECTED FAILURE (with the stub; reasoned from today's `Service.admin`, which calls
  `self.metrics(*args)` and drops kwargs. Probed: all four runs come back with no filter):
  `AssertionError: assert ({'2026-09-01T10:20:00+00:00': [1, 2, 3, 4], ...}, [1, 2, 3, 4]) == ({...: [2, 3, 4], ...}, [2, 3, 4])`.

**Cycle 10: `test_metrics_since_refuses_a_time_with_no_offset`.**
- `host_ledger(report_service.home, SINCE_RUNS)`. Then:
  - `REJECTED = ["2026-09-01T10:20:00", "2026-09-01", "yesterday", ""]`;
  - `reasons = [run_cli(repo, "ledger", "metrics", "--since", ts)["result"].get("reason") for ts in REJECTED]`;
  - `on_report = [answer(report_service.report, "metrics", None, since=v) for v in (5, "2026-09-01T10:20:00")]`.
- Single assertion: `reasons + on_report == ["bad_since"] * 6`.
- GREEN: decision 10. One helper in `service.py` turns the raw value into a datetime or `None`,
  and raises `ValueError` for a rejected one. Both `metrics` branches return
  `_refusal("bad_since", ...)` on that error.
- EXPECTED FAILURE (reasoned from cycle 9's increment): `fromisoformat` raises `ValueError` on
  `"yesterday"` and `""` and `TypeError` on `5`, and a naive time raises `TypeError` against the
  ledger's aware times. Each kills the handler thread, so the list holds
  `'ledger_unreachable'` (CLI) and `'unreachable'` (wire), and no `'bad_since'`. If cycle 9's
  GREEN read a naive time as UTC, those entries are `None` instead. Either way the assertion
  fails.

### Phase 4: docs

**Cycle 11 (refactor): docs.**
- `docs/split-runner.md`:
  - Under "One history per host", the command list gains `[--since <time>]` on
    `tdd ledger metrics`, with one sentence on decision 9's rule and decision 10's forms.
    It also says that every run in `metrics` carries `time.cycles`.
  - A new subsection, "A read-only report socket for dashboards". It covers:
    - the `report_socket` key, its default (no socket), and that it must differ from
      `admin_socket`;
    - that it answers `metrics`, `fleet` and `log` only, with the admin socket's results, and
      refuses everything else, `ping` included, with `method_not_allowed`;
    - that it opens ledgers read-only;
    - mode 660, with the group a new file gets. **Whose it is**: put it in a directory of its
      own that only the service account and the dashboard's account can traverse, and admit
      that one account with an inherited (default) ACL on the directory. Example:
      `setfacl -m u:orchestrator:rx,d:u:orchestrator:rw <dir>`. The socket's group alone does
      not limit it to one account: the unit's `Group=` is the guests' group;
    - that `tdd ledger metrics`, `fleet` and `log` fall back to it when the admin socket cannot
      be opened, and that the dashboard's account must be able to read a root-owned
      `ledger.toml`;
    - for a client that speaks the wire itself, the three requests:
      `{"method": "metrics", "args": [<slug or null>], "kwargs": {"since": <time>}}`,
      `{"method": "fleet"}`, and `{"method": "log", "args": [<slug>, <run id>]}`. One JSON line
      each.
- `README.md`: the VM-boundary bullet under split mode adds that a read-only report socket
  gives a dashboard every source's metrics, fleet and logs, and nothing else.
- `CHANGELOG.md` under `## [Unreleased]`, `### Added`:
  - the report socket (`report_socket`, and the fallback in `tdd ledger metrics|fleet|log`) (#185);
  - `tdd ledger metrics --since` (#185);
  - `time.cycles` in every run of `tdd metrics` and `tdd ledger metrics` (#185).
- `tdd docs split` already serves `docs/split-runner.md`, so no new docs topic is needed.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-185-report-socket     # first, before anything else
    tdd doctor                                  # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-185-report-socket.md   # captures baselines, opens cycle 1

`tdd doctor` checks every project; `tdd run start` probes only the ones the plan declares and
those downstream of them through an `[artifact]`. A failing check on a project outside that set
does not stop the run: note it and go on. Any other failing check stops it.

`tdd` is the released tool on `PATH` (0.15.0 at planning), never `uv run tdd` from this tree:
see the note at the top of `tdd.toml`. This plan changes no ledger table, so it needs no frozen
referee.

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is green
  at the plan's base (a fresh worktree of `origin/main` with `uv run pytest -n auto`:
  `722 passed`). Expect `baselines: {tddcli: 0}` and no standing failures.
- Cycles 3, 6 and 7 skip as root. Run as a normal account. If one of them skips instead of
  failing in RED, raise `tdd blocker --kind environment --detail 'cycles 3, 6 and 7 need a non-root account'`.
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`.
  - `create_stub`: only cycle 9 declares a stub (`src/tddcli/cli.py`). Any other request means
    an undeclared import.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`: for pin 6, and any cycle that
    pre-passes.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|environment> --detail '...'`.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.
  - This plan declares no annotation keys, so `annotate_cycle` should not appear.
- Cycle 11 is docs only. A refactor phase never carries a behaviour change: if one seems
  needed, raise `plan_defect`.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- cycle 1: `ServiceConfig.report_socket`, read with no checks. `Service.report_listener` is
  started and stopped, and its sessions are answered exactly as admin sessions are. No method
  filter, no read-only opening, and its mode is whatever `_Listener` gives a `source=None`
  listener.
- cycle 2: `report_only` sessions, checked before `ping`, and `Service.report` with
  `REPORT_METHODS`, calling the same `metrics`, `fleet` and `log` as `Service.admin`.
- cycle 3: `readonly=` on `Service.metrics` and `Service.log`, passed as `True` by
  `Service.report`.
- cycle 4: the report listener's socket is `GUEST_MODE`.
- cycle 5: `load_config` refuses `report_socket == admin_socket`.
- cycle 6: nothing (a pin).
- cycle 7: the connect-time fallback helper in `cli.py`, for `metrics`, `fleet` and `log`.
- cycle 8: `time.cycles` in `_time_json`, with `opened_at` and `closed_at` added to
  `_time_summary`'s entries. The existing exact-dict test gains `"cycles"`.
- cycle 9: `--since`, carried from the CLI through both `metrics` branches to `render.metrics`'
  filter. No `bad_since`.
- cycle 10: the `bad_since` refusal for every rejected form.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-185-report-socket-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-185-report-socket-friction.md
    git commit -m "docs: friction log for issue-185-report-socket"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #185`.

Docs are deliverables, not hopes. Cycle 11 owns them:

- `git diff --stat origin/main -- docs/split-runner.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- README.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.

What a user sees changes only in JSON envelopes, one new `[service]` key and one new flag, so no
demo recording is required. Instead, quote in the PR body the envelope of a `tdd ledger metrics`
answered through the report socket, and of one refused with `bad_since`. A real second account
and its directory ACL cannot be set up in CI. The PR body says so and names the scope cut.
