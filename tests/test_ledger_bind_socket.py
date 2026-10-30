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
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

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
