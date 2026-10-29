---
closes: 179
cycles:
  # -- Phase 1: unbind, on the admin socket ------------------------------------------------
  - n: 1
    project: tddcli
    title: "tdd ledger unbind returns a source's next runs to the guest's claim"
    test: "tests/test_ledger_service.py::test_unbind_returns_a_source_to_the_guests_claim"
    stub_expected: ["src/tddcli/cli.py"]
    files: ["src/tddcli/cli.py", "src/tddcli/service.py"]
    commit_red: "test: unbind returns a source to the guest's claim"
    commit_green: "feat: tdd ledger unbind clears a source's executor binding"
    commit_refactor: "refactor: tidy unbind"
  - n: 2
    project: tddcli
    title: "an unbinding survives a service restart"
    test: "tests/test_ledger_admin.py::test_an_unbinding_survives_a_service_restart"
    files: ["src/tddcli/service.py"]
    commit_red: "test: an unbinding survives a restart"
    commit_green: "feat: the service persists an unbinding"
    commit_refactor: "refactor: tidy unbind persistence"
  - n: 3
    project: tddcli
    title: "unbind refuses a source that does not exist"
    test: "tests/test_ledger_admin.py::test_unbind_refuses_an_unknown_source"
    files: ["src/tddcli/service.py"]
    commit_red: "test: unbind refuses an unknown source"
    commit_green: "feat: unbind refuses an unknown source"
    commit_refactor: "refactor: tidy unbind refusal"
  - n: 4
    project: tddcli
    title: "bind refuses an empty or blank executor"
    test: "tests/test_ledger_admin.py::test_bind_refuses_an_empty_executor"
    files: ["src/tddcli/service.py"]
    commit_red: "test: bind refuses an empty executor"
    commit_green: "fix: bind refuses an empty executor with bad_executor"
    commit_refactor: "refactor: tidy executor validation"
  # -- Phase 2: the bind socket --------------------------------------------------------------
  - n: 5
    project: tddcli
    title: "a configured bind socket answers bind"
    test: "tests/test_ledger_bind_socket.py::test_the_bind_socket_binds_a_source"
    files: ["src/tddcli/service.py"]
    commit_red: "test: the bind socket binds a source"
    commit_green: "feat: the ledger service listens on an optional bind socket"
    commit_refactor: "refactor: tidy the bind listener"
  - n: 6
    project: tddcli
    title: "the bind socket refuses every method but bind"
    test: "tests/test_ledger_bind_socket.py::test_the_bind_socket_refuses_every_other_method"
    files: ["src/tddcli/service.py"]
    commit_red: "test: the bind socket refuses every other method"
    commit_green: "feat: the bind socket answers bind alone"
    commit_refactor: "refactor: tidy bind socket dispatch"
  - n: 7
    project: tddcli
    title: "the bind socket answers unbind"
    test: "tests/test_ledger_bind_socket.py::test_the_bind_socket_unbinds_a_source"
    files: ["src/tddcli/service.py"]
    commit_red: "test: the bind socket unbinds a source"
    commit_green: "feat: the bind socket answers unbind"
    commit_refactor: "refactor: tidy bind socket methods"
  - n: 8
    project: tddcli
    pin_cycle: true
    title: "the bind socket keeps the admin socket's refusals for bind and unbind"
    test: "tests/test_ledger_bind_socket.py::test_the_bind_socket_keeps_the_admin_refusals"
    files: ["src/tddcli/service.py"]
    commit_red: "test: pin — the bind socket keeps unknown_source and bad_executor"
  - n: 9
    project: tddcli
    title: "the bind socket is mode 660 and belongs to bind_group"
    test: "tests/test_ledger_bind_socket.py::test_the_bind_socket_belongs_to_its_group"
    files: ["src/tddcli/service.py"]
    commit_red: "test: the bind socket belongs to its group"
    commit_green: "feat: the bind socket is mode 660, owned by bind_group"
    commit_refactor: "refactor: tidy socket modes"
  - n: 10
    project: tddcli
    title: "a half or clashing bind config is refused"
    test: "tests/test_ledger_bind_socket.py::test_a_half_or_clashing_bind_config_is_refused"
    files: ["src/tddcli/service.py"]
    commit_red: "test: a half or clashing bind config is refused"
    commit_green: "feat: bind_socket and bind_group go together, apart from admin_socket"
    commit_refactor: "refactor: tidy bind config checks"
  - n: 11
    project: tddcli
    title: "a bind_group that does not exist is refused when the config loads"
    test: "tests/test_ledger_bind_socket.py::test_a_bind_group_that_does_not_exist_is_refused"
    files: ["src/tddcli/service.py"]
    commit_red: "test: an unknown bind_group is refused"
    commit_green: "feat: the service config refuses an unknown bind_group"
    commit_refactor: "refactor: tidy bind_group lookup"
  # -- Phase 3: which socket the CLI uses ----------------------------------------------------
  - n: 12
    project: tddcli
    title: "bind and unbind use an explicit --socket"
    test: "tests/test_ledger_bind_socket.py::test_bind_and_unbind_use_an_explicit_socket"
    stub_expected: ["src/tddcli/cli.py"]
    files: ["src/tddcli/cli.py"]
    commit_red: "test: bind and unbind honour --socket"
    commit_green: "feat: tdd ledger bind and unbind take --socket"
    commit_refactor: "refactor: tidy socket choice"
  - n: 13
    project: tddcli
    pin_cycle: true
    title: "with no bind socket, an admin socket the caller cannot open is ledger_unreachable"
    test: "tests/test_ledger_admin.py::test_a_forbidden_admin_socket_with_no_bind_socket_is_unreachable"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: pin — a forbidden admin socket with no bind socket is ledger_unreachable"
  - n: 14
    project: tddcli
    title: "bind and unbind fall back to the bind socket when the admin socket cannot be opened"
    test: "tests/test_ledger_bind_socket.py::test_bind_and_unbind_fall_back_to_the_bind_socket"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: bind and unbind fall back to the bind socket"
    commit_green: "feat: bind and unbind fall back to the bind socket"
    commit_refactor: "refactor: tidy the bind socket fallback"
  # -- Phase 4: docs -------------------------------------------------------------------------
  - n: 15
    project: tddcli
    refactor_cycle: true
    title: "document the bind socket and unbind"
    files: ["docs/split-runner.md", "README.md", "CHANGELOG.md"]
    commit_refactor: "docs: the bind socket and tdd ledger unbind"
---

# Issue 179: a bind-only socket for the operator's orchestrator, and unbind

## Context

[#179](https://github.com/geuben/tdd-cli/issues/179) follows #169 (the ledger service). Today
`tdd ledger bind <source> --executor M` is the only way to say which model a source's runs
record, and it goes through the admin socket. `service.py` creates that socket at
`ADMIN_MODE = 0o600`, so only the account running `tdd ledger serve` can bind. The process that
knows the model is usually the orchestrator that starts each guest, running under its own
account. Giving it the admin socket would give it `add-source`, `remove-source`, `import` and
the host-wide `metrics`, `fleet` and `log` as well.

A binding also cannot be cleared. `Service.bind` overwrites `executors[name]`, and
`_Session._stamp_executor` stamps whatever is bound on every `start_run` and `abandon_run` as
`executor_source: "operator"`. So a run that has no known model is recorded with the previous
run's model, attested by the operator. The probe found a second form of the same problem:
`tdd ledger bind vm-1 --executor ""` succeeds today and binds the empty string, which
`_stamp_executor` then records as an operator-attested model (`binding is not None`).

The issue asks for:

1. **A bind socket.** Optional `[service] bind_socket` and `bind_group`. The socket is mode 660
   and belongs to the group, and it answers only `bind` and `unbind` for sources that already
   exist. Every other method is refused with `method_not_allowed`. `tdd ledger bind` uses it
   when the caller cannot open the admin socket, or when given `--socket`. The admin socket
   stays 600.
2. **`tdd ledger unbind <source>`.** It clears the binding, so the source's next runs fall back
   to the guest's claim (`claimed`), the way an unbound source behaves today. It works on both
   sockets.

Properties the issue wants: an account with only the bind socket can change the model a
source's next runs record, and nothing else; clearing a binding is as easy as setting one; and
neither socket takes an identity from the request.

## Design decisions (locked)

Each entry says what decided it. Executors do not re-open these.

1. **Config: `[service] bind_socket` and `bind_group`** (evidence: the issue's proposal, which
   names both keys). `ServiceConfig` gains `bind_socket: Path | None = None` and
   `bind_group: str | None = None`, defaulted, so today's configs load unchanged. With neither
   key set, the service behaves exactly as today (convention: a new knob defaults to today's
   behaviour).
2. **The two keys go together, and the bind socket is not the admin socket** (convention). A
   config that has one key without the other is refused with `ServiceConfigError`, and so is
   a `bind_socket` equal to `admin_socket`. The precedents: `load_config` already refuses a
   config without `admin_socket`, and `runner.load` refuses `ledger_socket` together with
   `ledger_home`. The reasons:
   - The issue says the socket's authority comes from its group. A bind socket with no group
     would fall back to the service's primary group, which split-runner.md gives to the guest
     forwarders ("give its group to whatever forwards it into the guest, and nothing else").
   - A `bind_group` alone is a leftover or a typo.
   - A `bind_socket` on the admin path would unlink the admin socket, because `_Listener`
     replaces any socket file already at its path.

   Cycle 10 pins the refusals, not their text. Word them
   `[service] bind_socket and bind_group go together` and
   `[service] bind_socket must not be admin_socket`.
3. **`bind_group` is checked when the config loads** (convention: config errors surface at
   load as `ServiceConfigError`, which `main` reports as a failure envelope). A group that
   does not exist (`grp.getgrnam` raises `KeyError`) is refused with a message naming it.
   Pinned by cycle 11.
4. **The bind socket is mode 660 and belongs to `bind_group`** (evidence: the issue). Add
   `BIND_MODE = 0o660` beside `ADMIN_MODE` and `GUEST_MODE`. The listener `chmod`s the socket
   and then gives it the group with `shutil.chown(path, group=bind_group)`. The service
   account must belong to `bind_group`. If it does not, the `chown` raises `PermissionError`
   and `tdd ledger serve` fails to start with that traceback, the same way it fails today
   when it cannot create its admin socket (convention). split-runner.md says so. Pinned by
   cycle 9.
5. **The bind socket answers `bind` and `unbind` and nothing else, not even `ping`**
   (evidence: the issue says "accepts only `bind` (and `unbind`) ... Every other method is
   refused with `method_not_allowed`").
   - Add `BIND_METHODS = frozenset({"bind", "unbind"})`.
   - A connection on the bind listener is checked **before** the `ping` branch in
     `_Session.answer`.
   - A method in `BIND_METHODS` is passed to `Service.admin` unchanged. Anything else is
     `_refusal("method_not_allowed", f"{method} is not answered on the bind socket")`.
   - Because both sockets go through the same `Service.admin` branches, the
     `unknown_source` and `bad_executor` refusals hold on both. Cycle 8 pins that.
   - The bind listener is kept as its own attribute (`Service.bind_listener`), not in
     `Service.listeners`, whose keys are source names. Its session is a
     `_Session(..., source=None, ..., bind_only=True)`. `Service.stop` closes it as well. No
     test asserts that: `serve` exits after `stop`. It is stated so the suite does not leak
     a listener thread per test.

   Pinned by cycles 5, 6 and 7.
6. **`tdd ledger unbind <name>` is a verb of its own** (evidence: the issue's proposal heading
   and its title name `unbind`. The parenthetical alternative, `bind --executor ""`, is ruled
   out because the empty string binds today, as probed).
   - `Service.unbind(name)` sets `executors[name] = None` and calls `_save()`.
   - The admin branch `"unbind"` takes `(name,)`. It refuses an unknown name with
     `unknown_source`, exactly like `"bind"`. No test reads its answer; make it
     `{"name": name, "executor": None}`, the shape of `bind`'s.
   - Nothing refuses a source that is already unbound, and none is to be built
     (convention: `bind` has no such refusal either).
   - `sources.json` already stores `"executor": null`, so its shape does not change.
   - The CLI handler's `next_action` detail (not asserted) reads: `Source <name>'s next runs
     record the guest's own claim.`
7. **`bind` refuses an empty or blank executor with `bad_executor`** (convention: the
   refusal is named like `bad_repo` and carried as `envelope.failure(..., reason=...)` under
   `result.reason`. It is needed because the issue names the empty value as an unbind
   spelling, and today that spelling records `""` as an operator-attested model).
   - In the `"bind"` admin branch, after the `unknown_source` check, an executor that is not
     a `str`, or is empty after `.strip()`, is
     `_refusal("bad_executor", "an executor names a model: `tdd ledger unbind` clears a binding")`.
   - Accepted: any string with a non-blank character, passed through unchanged (not
     stripped). Rejected: `""` and whitespace-only.
   - `add-source --executor` is unchanged: the issue does not ask about it.

   Pinned by cycle 4 (admin socket) and cycle 8 (bind socket).
8. **Which socket `tdd ledger bind` and `unbind` use** (evidence: the issue says "uses it
   when the caller can't open the admin socket, or with an explicit `--socket`").
   - **`--socket PATH` given:** that socket alone, with no fallback. Cycle 12 pins it.
   - **No `--socket`:** connect to `admin_socket`. If the *connect* fails for any reason
     (`wire.Connection` raises `LedgerUnreachable` from its constructor: `EACCES`, `ENOENT`,
     `ECONNREFUSED`) and `bind_socket` is configured, connect to `bind_socket` instead and
     send the request there. Cycle 14 pins `EACCES` and `ENOENT`.
   - **Connect fails and no `bind_socket` is configured:** the `LedgerUnreachable` propagates
     and the verb fails with `reason: "ledger_unreachable"`, as today. Cycle 13 pins it before
     cycle 14 changes the code next to it.
   - **The connection was made and then dropped:** this is never retried on the other
     socket. Fallback is decided at connect time only.
   - Implement it as one helper in `cli.py`, used by `_ledger_bind` and `_ledger_unbind`. It
     builds a `wire.Connection` itself, rather than calling `wire.call`, so that a failed
     connect can be told apart from a failed request. `wire.py` is unchanged.
   - Every other `tdd ledger` verb still talks only to the admin socket.
9. **Every `tdd ledger` verb still needs the service config, with its trust rule unchanged**
   (convention: #169 made every `tdd ledger` handler load the config first, through
   `_ledger_verb`. docs/split-runner.md holds `ledger.toml` to `runner.toml`'s trust rule,
   PRD §13.2 R13.10: owned by root or by the reading account, not group- or world-writable).
   So the orchestrator's account must be able to read `/etc/tdd-cli/ledger.toml`, and the
   file must be owned by root. A config owned by the service account is refused for every
   other account by `_require_trusted`. `--socket` does not skip the config: the verb still
   fails with `no_service` when the config is absent. split-runner.md says all of this.
10. **Tests.**
    - The bind socket's tests go in a new `tests/test_ledger_bind_socket.py`.
    - Admin-socket `unbind` and `bind` tests extend `tests/test_ledger_admin.py`.
    - The run-recording test sits beside the other executor-stamping tests in
      `tests/test_ledger_service.py`.
    - Sockets live under `tempfile.mkdtemp(dir="/tmp", prefix="tdd-")`, per the repo note
      on AF_UNIX path length.
    - A caller that cannot open the admin socket is stood in for by `chmod 0` on it. The
      probe showed that the owner then gets `PermissionError(13)` on connect, which is what
      another account gets on a 600 socket. Those tests are
      `@pytest.mark.skipif(os.geteuid() == 0, reason="root connects to a mode-000 socket")`,
      after the repo's own `"root reads a mode-000 file"` skips in
      `tests/test_split_runner.py`.

## Deliberate scope cuts (do not build)

- **Run-scoped binding** (the issue's "Open question"). **Premise: named by the issue as a
  separate issue.** The issue says "That may be a separate issue", under a heading of its
  own, outside the proposal. Building it would also change what PRD §8.3's `tdd run abandon`
  row specifies. The abandonment records *who abandoned* (reason, account, executor), and
  run-scoped binding would record the run's own model there instead. That is a PRD change,
  which this plan does not make. Until then, a binding belongs to the source: an
  abandonment is stamped with the source's binding at the moment of abandoning, as today.
  split-runner.md says so. If a reviewer wants it built now, close this PR unmerged. That
  sends #179 back to `needs-decision`.
- **Socket forwarding and group setup on a real host.** **Premise: unreachable.** No second
  account or second host is reachable from CI. The service side is built and tested in
  full: the mode, the group, the method refusals and the fallback. A different uid is stood
  in for by a mode-000 socket (decision 10).

## Fake and real divergence

| Seam | In the tests | In production | Ruling |
|---|---|---|---|
| A caller that cannot open the admin socket | the same uid, admin socket `chmod 0` → `PermissionError(13)` on connect | another uid, socket 600 → `EACCES` on connect | acceptable: the same errno reaches the same `wire.Connection` constructor |
| `bind_group` | a group the test user already belongs to, other than the socket's default gid | the operator's orchestrator group, of which the service account is a member | acceptable: `shutil.chown` takes the same path. The service account not being a member is a startup traceback (decision 4), and is documented, not tested |
| The service | `service.Service` in a thread of the test process, on real unix sockets | `tdd ledger serve` under its own account | acceptable: `test_ledger_serve_runs_until_terminated` already covers the process wrapper |

## Cycles

All tests call the CLI in-process through `conftest.run_cli`. A refusal's `reason` is read
as `out["result"].get("reason")`, never at the envelope's top level.

### Phase 1: unbind, on the admin socket

**Cycle 1: `tests/test_ledger_service.py::test_unbind_returns_a_source_to_the_guests_claim`.**
- Fixtures `repo`, `split_guest`, `ledger_service`. Use the existing helpers in that file:
  `start_run`, `host_run`, and `guest_config` and `current_user` from `conftest`.
- Setup:
  - `ledger_service.service.add_source("vm-b", ledger_service.dir / "vm-b.sock", executor="model-x")`;
  - `guest_config(split_guest.runner, ledger_service.dir / "vm-b.sock", extra=f'[executor]\n"{current_user()}" = "guest-says"\n')`;
  - `run_cli(repo, "ledger", "unbind", "vm-b")`;
  - then `run = host_run(ledger_service, repo, start_run(repo)["run"]["id"])`.
- Single assertion: `(run["executor_model"], run["executor_source"]) == ("guest-says", "claimed")`.
- `stub_expected: src/tddcli/cli.py`: an `unbind` subparser under `ledger`, with a `name`
  positional and `set_defaults(fn=_ledger_verb(_not_implemented))`. `_not_implemented` already
  exists. Without the stub, argparse exits 2 with empty stdout and the RED dies in
  `json.JSONDecodeError` (probed).
- GREEN: `Service.unbind`, the `"unbind"` admin branch, and `_ledger_unbind` in `cli.py`,
  which calls the admin socket.
- EXPECTED FAILURE (probed with the stub): `AssertionError: assert ('model-x', 'operator') == ('guest-says', 'claimed')`.

**Cycle 2: `tests/test_ledger_admin.py::test_an_unbinding_survives_a_service_restart`.**
- Setup:
  - `socket_path = ledger_service.dir / "vm-1.sock"`;
  - `ledger_service.service.add_source("vm-1", socket_path, executor="m")`;
  - `run_cli(repo, "ledger", "unbind", "vm-1")`;
  - then `ledger_service.service.stop()`, and a new
    `service.Service(service.load_config(ledger_service.config))`, started, with `ping` on
    `socket_path` through the file's `ping_or_unreachable` helper, stopped in a `finally`.
    Copy `test_sources_survive_a_service_restart`.
- Single assertion: `reply == {"source": "vm-1", "executor": None}`.
- EXPECTED FAILURE (reasoned from cycle 1's increment, which keeps the unbinding in memory):
  `AssertionError: assert {'executor': 'm', 'source': 'vm-1'} == {'executor': None, 'source': 'vm-1'}`.
  If cycle 1's GREEN already saved, this pre-passes and the tool runs the sensitivity check:
  let it.

**Cycle 3: `tests/test_ledger_admin.py::test_unbind_refuses_an_unknown_source`.**
- `out = run_cli(repo, "ledger", "unbind", "nope")`, with no source named `nope`.
- Single assertion: `out["result"].get("reason") == "unknown_source"`.
- EXPECTED FAILURE (reasoned): `AssertionError: assert 'ledger_unreachable' == 'unknown_source'`.
  The reason: once cycle 2 saves, `_save` raises `KeyError` on the phantom name (it looks
  up `self.listeners[name]`), the handler thread dies, and the client sees the connection
  close. If the unbinding is not saved, the reason is `None` instead.

**Cycle 4: `tests/test_ledger_admin.py::test_bind_refuses_an_empty_executor`.**
- `ledger_service.service.add_source("vm-1", ledger_service.dir / "vm-1.sock", executor="m")`,
  then `[run_cli(repo, "ledger", "bind", "vm-1", "--executor", e)["result"].get("reason") for e in ("", "   ")]`.
- Single assertion: the list `== ["bad_executor", "bad_executor"]`.
- EXPECTED FAILURE (probed: `bind --executor ""` answers `ok` and binds `""`):
  `AssertionError: assert [None, None] == ['bad_executor', 'bad_executor']`.

### Phase 2: the bind socket

New file `tests/test_ledger_bind_socket.py`. Its module-level helpers, written in cycle 5's
RED (cycles 9 to 14 reuse them):

- `started_bind_service(tmp_path, monkeypatch, group)`, a `contextlib.contextmanager`:
  - `sockets = Path(tempfile.mkdtemp(dir="/tmp", prefix="tdd-"))`;
  - writes `tmp_path / "ledger.toml"` as
    `[service]\nadmin_socket = "<sockets>/admin.sock"\nhome = "<tmp_path>/host-ledgers"\nbind_socket = "<sockets>/bind.sock"\nbind_group = "<group>"\n`;
  - `monkeypatch.setenv("TDD_LEDGER_SERVICE_CONFIG", ...)`;
  - starts `service.Service(service.load_config(cfg))`;
  - yields `SimpleNamespace(service=svc, dir=sockets, config=cfg, admin_socket=sockets / "admin.sock", bind_socket=sockets / "bind.sock")`;
  - finally `svc.stop()` and `shutil.rmtree(sockets, ignore_errors=True)`. Copy
    `conftest.ledger_service`.
- Fixture `bind_service(tmp_path, monkeypatch)`: `started_bind_service` with the caller's
  primary group, `grp.getgrgid(os.getegid()).gr_name`.
- `answer(socket_path, method, *args) -> str`, one call through `wire.call`:
  - `"ok"` on success;
  - `exc.refusal` on `wire.LedgerRefused`;
  - `"unreachable"` on `wire.LedgerUnreachable`;
  - `"error"` on `RuntimeError`.

  Catch `LedgerRefused` and `LedgerUnreachable` before `RuntimeError`, because both
  subclass it.

**Cycle 5: `test_the_bind_socket_binds_a_source`.**
- `vm1 = bind_service.dir / "vm-1.sock"`; `bind_service.service.add_source("vm-1", vm1)`;
  `answer(bind_service.bind_socket, "bind", "vm-1", "m")`.
- Single assertion: `wire.call(vm1, "ping")["executor"] == "m"`.
- GREEN:
  - `load_config` reads `bind_socket` and `bind_group` (no checks yet);
  - `Service.start` opens `self.bind_listener` when `bind_socket` is set, and `Service.stop`
    closes it;
  - its sessions hand every request to `Service.admin`.
- EXPECTED FAILURE (probed: `load_config` ignores both keys today, so there is no bind
  socket): `AssertionError: assert None == 'm'`.

**Cycle 6: `test_the_bind_socket_refuses_every_other_method`.**
- `bind_service.service.add_source("vm-1", bind_service.dir / "vm-1.sock")`. Then
  `{m: answer(bind_service.bind_socket, m, *a) for m, a in OTHER}`, where `OTHER` is, in
  order:
  - `("ping", ())`, `("sources", ())`;
  - `("add_source", ("vm-x", str(bind_service.dir / "vm-x.sock")))`, `("remove_source", ("vm-1",))`;
  - `("import", (str(tmp_path / "x.sqlite3"), "legacy"))`;
  - `("metrics", ())`, `("fleet", ())`, `("log", ("slug", 1))`;
  - `("open", (str(tmp_path),))`, `("lease", ())`, `("lease_snapshot", ())`, `("run", (1,))`.
- Single assertion: the dict `== {m: "method_not_allowed" for m, _ in OTHER}`.
- GREEN: the bind listener's sessions are `bind_only`, checked before `ping`. Only `"bind"`
  goes to `Service.admin`; everything else is refused with `method_not_allowed`.
- EXPECTED FAILURE (reasoned from cycle 5's increment): `AssertionError` on the dict:
  - `ping`, `sources`, `add_source`, `remove_source`, `metrics` and `fleet` answer `'ok'`;
  - `import` answers `'error'` or `'unreachable'`;
  - `log` answers `'unknown_repo'`.

  The guest methods are already `method_not_allowed`, through `Service.admin`'s fallthrough.

**Cycle 7: `test_the_bind_socket_unbinds_a_source`.**
- `add_source("vm-1", vm1, executor="m")`; `answer(bind_service.bind_socket, "unbind", "vm-1")`.
- Single assertion: `wire.call(vm1, "ping")["executor"] is None`.
- GREEN: `"unbind"` joins `"bind"` in `BIND_METHODS`.
- EXPECTED FAILURE (reasoned: cycle 6 refuses `unbind`): `AssertionError: assert 'm' is None`.

**Cycle 8 (pin): `test_the_bind_socket_keeps_the_admin_refusals`.**
- `add_source("vm-1", vm1)`. Then
  `[answer(b, "bind", "nope", "m"), answer(b, "unbind", "nope"), answer(b, "bind", "vm-1", "")]`,
  with `b = bind_service.bind_socket`.
- Single assertion: the list `== ["unknown_source", "unknown_source", "bad_executor"]`.
- **Must pass on arrival.** Decision 5 routes bind-socket requests through the same
  `Service.admin` branches that cycles 3 and 4 already guard. If it fails on arrival, the
  bind socket has its own `bind`/`unbind` code, against decision 5. Raise
  `tdd blocker --kind plan_defect`; do not add a second copy of the checks.

**Cycle 9: `test_the_bind_socket_belongs_to_its_group`.**
- Helper `other_group() -> str`:
  - make a file in a fresh `tempfile.mkdtemp(dir="/tmp", prefix="tdd-")`, read its `st_gid`
    (the default gid of a new file there), and remove both;
  - return the name of the first gid in `sorted(set(os.getgroups()) | {os.getegid()})`
    that differs from the default;
  - if there is none, `pytest.skip("needs a group other than the default for new files in /tmp")`.

  Probed: on Linux the default is the egid (here 1200), and this account also has 111. On
  macOS the default is `/private/tmp`'s group, `wheel`, which differs from the user's
  primary group.
- `with started_bind_service(tmp_path, monkeypatch, other_group()) as svc: st = svc.bind_socket.stat()`.
  Stat inside the `with`: `stop()` unlinks the socket.
- Single assertion: `(stat.S_IMODE(st.st_mode), st.st_gid) == (0o660, grp.getgrnam(group).gr_gid)`.
- GREEN: `BIND_MODE`, and `shutil.chown(path, group=...)` in `_Listener`. Look the group up
  by name at listener start; cycle 11 moves the lookup to config load.
- EXPECTED FAILURE: `AssertionError` with `0o600` (384) and the default gid on the left, for
  example `assert (384, 1200) == (432, 111)` on the planning host. Probed after the change: a unix socket here, `chmod 0o660` and
  `shutil.chown(group=<gid 111's name>)`, reads `(0o660, 111)`.

**Cycle 10: `test_a_half_or_clashing_bind_config_is_refused`.**
- Helper `refused(tmp_path, body) -> bool`: write
  `[service]\nadmin_socket = "/tmp/tdd-179-admin.sock"\n` + `body` to a fresh file under
  `tmp_path`, call `service.load_config(path)`, and return whether it raised
  `service.ServiceConfigError`. Let `g` be the primary group's name. The cases:
  - socket only: `bind_socket = "/tmp/tdd-179-bind.sock"\n`;
  - group only: `bind_group = "<g>"\n`;
  - clash: `bind_socket = "/tmp/tdd-179-admin.sock"\nbind_group = "<g>"\n`.
- Single assertion: `[refused(...) for each case] == [True, True, True]`.
- EXPECTED FAILURE (probed: both half configs load today; the clash loads because nothing
  compares the paths): `AssertionError: assert [False, False, False] == [True, True, True]`.

**Cycle 11: `test_a_bind_group_that_does_not_exist_is_refused`.**
- A config with `bind_socket = "/tmp/tdd-179-bind.sock"` and `bind_group = "no-such-group-179"`.
- Single assertion: `with pytest.raises(service.ServiceConfigError, match="no-such-group-179"): service.load_config(path)`.
- GREEN: `load_config` calls `grp.getgrnam` and turns `KeyError` into `ServiceConfigError`.
- EXPECTED FAILURE (cycle 9 looks the group up only at listener start; probed:
  `shutil.chown` raises `LookupError("no such group: ...")` only then):
  `Failed: DID NOT RAISE <class 'tddcli.service.ServiceConfigError'>`.

### Phase 3: which socket the CLI uses

**Cycle 12: `tests/test_ledger_bind_socket.py::test_bind_and_unbind_use_an_explicit_socket`.**
- `bind_service`, `add_source("vm-1", vm1)`, and `missing = bind_service.dir / "missing.sock"`.
  Then `[run_cli(repo, "ledger", *verb, "--socket", str(missing))["result"].get("reason") for verb in (("bind", "vm-1", "--executor", "m"), ("unbind", "vm-1"))]`.
- Single assertion: the list `== ["ledger_unreachable", "ledger_unreachable"]`.
- `stub_expected: src/tddcli/cli.py`: `s.add_argument("--socket")` on the `bind` and `unbind`
  subparsers, read by nothing. Without it argparse exits 2 and the RED dies in
  `json.JSONDecodeError` (probed: `unrecognized arguments: --socket`).
- GREEN: `_ledger_bind` and `_ledger_unbind` call `args.socket` when given, and the admin
  socket otherwise.
- EXPECTED FAILURE (probed with the stub: the flag is ignored and the admin socket answers):
  `AssertionError: assert [None, None] == ['ledger_unreachable', 'ledger_unreachable']`.

**Cycle 13 (pin): `tests/test_ledger_admin.py::test_a_forbidden_admin_socket_with_no_bind_socket_is_unreachable`.**
- `@pytest.mark.skipif(os.geteuid() == 0, reason="root connects to a mode-000 socket")`; add
  `import pytest` to the file.
- `ledger_service` (no bind socket): `add_source("vm-1", ...)`;
  `(ledger_service.dir / "admin.sock").chmod(0)`;
  `out = run_cli(repo, "ledger", "bind", "vm-1", "--executor", "m")`.
- Single assertion: `out["result"].get("reason") == "ledger_unreachable"`.
- **Must pass on arrival.** Probed: today it answers `ledger_unreachable`, and the error
  reads `... is unreachable: Permission denied`. It guards decision 8's third case before
  cycle 14 adds the fallback beside it.

**Cycle 14: `tests/test_ledger_bind_socket.py::test_bind_and_unbind_fall_back_to_the_bind_socket`.**
- The same `skipif` as cycle 13.
- `bind_service`, `add_source("vm-1", vm1)`, `admin = bind_service.admin_socket`. Then:
  1. `admin.chmod(0)`; `run_cli(repo, "ledger", "bind", "vm-1", "--executor", "m")`; read
     `wire.call(vm1, "ping")["executor"]`;
  2. `run_cli(repo, "ledger", "unbind", "vm-1")`; read `ping` again;
  3. `admin.chmod(0o600)`; `admin.rename(admin.with_name("admin.moved"))`;
     `run_cli(repo, "ledger", "bind", "vm-1", "--executor", "m2")`; read `ping` again.

  Probed: the fixture's teardown is clean after the rename.
- Single assertion: the three readings `== ["m", None, "m2"]`.
- GREEN: decision 8's helper. A failed connect to the admin socket falls back to
  `cfg.bind_socket` when it is set, and re-raises when it is not.
- EXPECTED FAILURE (probed: a forbidden admin socket and a missing admin socket both answer
  `ledger_unreachable` today): `AssertionError: assert [None, None, None] == ['m', None, 'm2']`.

### Phase 4: docs

**Cycle 15 (refactor): docs.**
- `docs/split-runner.md`:
  - under "One source per guest", add `tdd ledger unbind vm-1   # its next runs record the
    guest's claim again`;
  - add a new subsection, "A bind-only socket for an orchestrator". It covers:
    - the two `[service]` keys, and that they go together;
    - mode 660 and the group, and that the service account must be a member;
    - that the socket answers only `bind` and `unbind`, for existing sources, and refuses
      everything else with `method_not_allowed`, `ping` included;
    - the CLI's socket choice (decision 8);
    - that the orchestrator's account needs to read a root-owned `ledger.toml`
      (decision 9);
    - that a binding belongs to the source, so an abandonment is stamped with the binding
      in force when it is abandoned.
  - The "Executor identity is set on the host" paragraph gains one sentence on `unbind` and
    `bad_executor`.
- `README.md`: the VM-boundary bullet under split mode adds that the operator binds or
  unbinds each source's model, and can give an orchestrator a socket that does only that.
- `CHANGELOG.md` under `## [Unreleased]`:
  - `### Added`: the bind socket (`bind_socket`, `bind_group`, `--socket`, the fallback) and
    `tdd ledger unbind` (#179);
  - `### Fixed`: `tdd ledger bind --executor ""` bound an empty model, and is now refused
    with `reason: "bad_executor"` (#179).
- `tdd docs split` already serves `docs/split-runner.md`, so no new docs topic is needed.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-179-bind-socket-and-unbind   # first, before anything else
    tdd doctor                                  # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-179-bind-socket-and-unbind.md   # captures baselines, opens cycle 1

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
- Cycles 13 and 14 skip as root. Run as a normal account. Cycle 9 needs the account to belong
  to a group other than the default for new files in `/tmp`; the slot account at planning
  did (`docker`). If cycle 9's test skips instead of failing in RED, raise
  `tdd blocker --kind environment --detail 'cycle 9 needs a second group'`.
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`.
  - `create_stub`: cycles 1 and 12 declare stubs, both in `src/tddcli/cli.py`. Any other
    request means an undeclared import.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`: pins 8 and 13, and any
    cycle that pre-passes (cycle 2 may).
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|environment> --detail '...'`.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.
  - This plan declares no annotation keys, so `annotate_cycle` should not appear.
- Cycle 15 is docs only. A refactor phase never carries a behaviour change: if one seems
  needed, raise `plan_defect`.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- cycle 1: `Service.unbind` sets `executors[name] = None` in memory. Add the `"unbind"` admin
  branch with no `unknown_source` check, and `_ledger_unbind` on the admin socket. No `_save`.
- cycle 2: `Service.unbind` calls `_save()`.
- cycle 3: the `"unbind"` branch refuses an unknown name with `unknown_source`.
- cycle 4: the `"bind"` branch refuses an empty or blank executor with `bad_executor`.
- cycle 5: `ServiceConfig.bind_socket` and `bind_group`, read with no checks. The bind
  listener is started and stopped, and hands every request to `Service.admin`. No method
  filter and no group; its mode is whatever `_Listener` gives a `source=None` listener.
- cycle 6: `bind_only` sessions, checked before `ping`, with `BIND_METHODS = {"bind"}`.
- cycle 7: `"unbind"` joins `BIND_METHODS`.
- cycle 8: nothing (a pin).
- cycle 9: `BIND_MODE` and `shutil.chown` by group name, in `_Listener`.
- cycle 10: `load_config` refuses half configs and `bind_socket == admin_socket`.
- cycle 11: `load_config` looks up `bind_group` with `grp.getgrnam`.
- cycle 12: `--socket` is honoured by `bind` and `unbind`, with no fallback.
- cycle 13: nothing (a pin).
- cycle 14: the connect-time fallback to `bind_socket`.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-179-bind-socket-and-unbind-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-179-bind-socket-and-unbind-friction.md
    git commit -m "docs: friction log for issue-179-bind-socket-and-unbind"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #179`.

Docs are deliverables, not hopes. Cycle 15 owns them:

- `git diff --stat origin/main -- docs/split-runner.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- README.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.

What a user sees changes only in JSON envelopes, one new operator verb and one new flag, so
no demo recording is required. Instead, quote in the PR body the envelope of a
`tdd ledger unbind` and of a `bind` refused with `bad_executor`. A real second account and
socket forwarding cannot run in CI. The PR body says so and names the scope cut.
