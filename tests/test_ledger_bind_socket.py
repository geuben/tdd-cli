"""The bind socket: an operator's orchestrator binds or unbinds a source, and nothing else.

The admin socket stays the service account's alone. The bind socket is given to a group,
so a process that starts each guest can say which model the guest's next runs record
without being handed the rest of the operator's verbs.
"""

from __future__ import annotations

import contextlib
import grp
import os
import shutil
import stat
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from conftest import run_cli
from tddcli import service, wire


@contextlib.contextmanager
def started_bind_service(tmp_path, monkeypatch, group: str):
    """A ledger service with a bind socket given to `group`, in a thread of this process."""
    sockets = Path(tempfile.mkdtemp(dir="/tmp", prefix="tdd-"))
    cfg = tmp_path / "ledger.toml"
    cfg.write_text(
        f'[service]\nadmin_socket = "{sockets / "admin.sock"}"\n'
        f'home = "{tmp_path / "host-ledgers"}"\n'
        f'bind_socket = "{sockets / "bind.sock"}"\nbind_group = "{group}"\n'
    )
    monkeypatch.setenv("TDD_LEDGER_SERVICE_CONFIG", str(cfg))
    svc = service.Service(service.load_config(cfg))
    svc.start()
    try:
        yield SimpleNamespace(
            service=svc,
            dir=sockets,
            config=cfg,
            admin_socket=sockets / "admin.sock",
            bind_socket=sockets / "bind.sock",
        )
    finally:
        svc.stop()
        shutil.rmtree(sockets, ignore_errors=True)


@pytest.fixture
def bind_service(tmp_path, monkeypatch):
    with started_bind_service(tmp_path, monkeypatch, grp.getgrgid(os.getegid()).gr_name) as svc:
        yield svc


def answer(socket_path, method: str, *args) -> str:
    """How the service answered one request: `ok`, its refusal, or how it failed."""
    try:
        wire.call(socket_path, method, *args)
    except wire.LedgerRefused as exc:
        return exc.refusal
    except wire.LedgerUnreachable:
        return "unreachable"
    except RuntimeError:
        return "error"
    return "ok"


def test_the_bind_socket_binds_a_source(bind_service):
    vm1 = bind_service.dir / "vm-1.sock"
    bind_service.service.add_source("vm-1", vm1)
    answer(bind_service.bind_socket, "bind", "vm-1", "m")

    assert wire.call(vm1, "ping")["executor"] == "m"


def test_the_bind_socket_refuses_every_other_method(bind_service, tmp_path):
    bind_service.service.add_source("vm-1", bind_service.dir / "vm-1.sock")
    other = [
        ("ping", ()),
        ("sources", ()),
        ("add_source", ("vm-x", str(bind_service.dir / "vm-x.sock"))),
        ("remove_source", ("vm-1",)),
        ("import", (str(tmp_path / "x.sqlite3"), "legacy")),
        ("metrics", ()),
        ("fleet", ()),
        ("log", ("slug", 1)),
        ("open", (str(tmp_path),)),
        ("lease", ()),
        ("lease_snapshot", ()),
        ("run", (1,)),
    ]

    answers = {m: answer(bind_service.bind_socket, m, *a) for m, a in other}
    assert answers == {m: "method_not_allowed" for m, _ in other}


def test_the_bind_socket_unbinds_a_source(bind_service):
    vm1 = bind_service.dir / "vm-1.sock"
    bind_service.service.add_source("vm-1", vm1, executor="m")
    answer(bind_service.bind_socket, "unbind", "vm-1")

    assert wire.call(vm1, "ping")["executor"] is None


def test_the_bind_socket_keeps_the_admin_refusals(bind_service):
    bind_service.service.add_source("vm-1", bind_service.dir / "vm-1.sock")
    b = bind_service.bind_socket

    answers = [
        answer(b, "bind", "nope", "m"),
        answer(b, "unbind", "nope"),
        answer(b, "bind", "vm-1", ""),
    ]
    assert answers == ["unknown_source", "unknown_source", "bad_executor"]


def other_group() -> str:
    """A group this account is in, other than the one a new file in /tmp is given."""
    scratch = Path(tempfile.mkdtemp(dir="/tmp", prefix="tdd-"))
    try:
        probe = scratch / "probe"
        probe.touch()
        default = probe.stat().st_gid
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    for gid in sorted(set(os.getgroups()) | {os.getegid()}):
        if gid != default:
            return grp.getgrgid(gid).gr_name
    pytest.skip("needs a group other than the default for new files in /tmp")


def test_the_bind_socket_belongs_to_its_group(tmp_path, monkeypatch):
    group = other_group()
    with started_bind_service(tmp_path, monkeypatch, group) as svc:
        st = svc.bind_socket.stat()

    assert (stat.S_IMODE(st.st_mode), st.st_gid) == (0o660, grp.getgrnam(group).gr_gid)


def refused(tmp_path, body: str) -> bool:
    """Whether the service refuses a config with this added to its `[service]`."""
    path = Path(tempfile.mkdtemp(dir=tmp_path)) / "ledger.toml"
    path.write_text('[service]\nadmin_socket = "/tmp/tdd-179-admin.sock"\n' + body)
    try:
        service.load_config(path)
    except service.ServiceConfigError:
        return True
    return False


def test_a_half_or_clashing_bind_config_is_refused(tmp_path):
    g = grp.getgrgid(os.getegid()).gr_name
    cases = [
        'bind_socket = "/tmp/tdd-179-bind.sock"\n',
        f'bind_group = "{g}"\n',
        f'bind_socket = "/tmp/tdd-179-admin.sock"\nbind_group = "{g}"\n',
    ]

    assert [refused(tmp_path, body) for body in cases] == [True, True, True]


def test_a_bind_group_that_does_not_exist_is_refused(tmp_path):
    path = tmp_path / "ledger.toml"
    path.write_text(
        '[service]\nadmin_socket = "/tmp/tdd-179-admin.sock"\n'
        'bind_socket = "/tmp/tdd-179-bind.sock"\nbind_group = "no-such-group-179"\n'
    )

    with pytest.raises(service.ServiceConfigError, match="no-such-group-179"):
        service.load_config(path)


def test_bind_and_unbind_use_an_explicit_socket(repo, bind_service):
    bind_service.service.add_source("vm-1", bind_service.dir / "vm-1.sock")
    missing = bind_service.dir / "missing.sock"

    reasons = [
        run_cli(repo, "ledger", *verb, "--socket", str(missing))["result"].get("reason")
        for verb in (("bind", "vm-1", "--executor", "m"), ("unbind", "vm-1"))
    ]
    assert reasons == ["ledger_unreachable", "ledger_unreachable"]


@pytest.mark.skipif(os.geteuid() == 0, reason="root connects to a mode-000 socket")
def test_bind_and_unbind_fall_back_to_the_bind_socket(repo, bind_service):
    vm1 = bind_service.dir / "vm-1.sock"
    bind_service.service.add_source("vm-1", vm1)
    admin = bind_service.admin_socket
    readings = []

    admin.chmod(0)
    run_cli(repo, "ledger", "bind", "vm-1", "--executor", "m")
    readings.append(wire.call(vm1, "ping")["executor"])
    run_cli(repo, "ledger", "unbind", "vm-1")
    readings.append(wire.call(vm1, "ping")["executor"])
    admin.chmod(0o600)
    admin.rename(admin.with_name("admin.moved"))
    run_cli(repo, "ledger", "bind", "vm-1", "--executor", "m2")
    readings.append(wire.call(vm1, "ping")["executor"])

    assert readings == ["m", None, "m2"]
