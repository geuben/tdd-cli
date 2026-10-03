"""`tdd ledger …`: the operator's verbs, answered on the host over the admin socket.

The operator adds a source per guest, binds the executor it runs, and reads every
source's history in one place. None of these verbs is ever forwarded to a runner.
"""

from __future__ import annotations

from conftest import run_cli
from tddcli import wire


def test_ledger_verbs_are_never_forwarded_to_a_runner(repo, split_client, tmp_path, monkeypatch):
    monkeypatch.setenv("TDD_LEDGER_SERVICE_CONFIG", str(tmp_path / "no-service.toml"))

    out = run_cli(repo, "ledger", "sources")
    assert out.get("result", {}).get("reason") == "no_service"


def test_add_source_opens_a_guest_socket(repo, ledger_service):
    socket_path = ledger_service.dir / "vm-2.sock"
    run_cli(repo, "ledger", "add-source", "vm-2", "--socket", str(socket_path))

    assert wire.call(socket_path, "ping") == {"source": "vm-2", "executor": None}


def test_sources_lists_each_source_and_its_binding(repo, ledger_service):
    svc, sockets = ledger_service.service, ledger_service.dir
    svc.add_source("vm-2", sockets / "vm-2.sock", executor="m")
    svc.add_source("vm-1", sockets / "vm-1.sock", executor=None)

    out = run_cli(repo, "ledger", "sources")
    assert out["result"].get("sources") == [
        {"name": "vm-1", "socket": str(sockets / "vm-1.sock"), "executor": None},
        {"name": "vm-2", "socket": str(sockets / "vm-2.sock"), "executor": "m"},
    ]


def test_bind_changes_the_executor_for_the_next_run(repo, ledger_service):
    socket_path = ledger_service.dir / "vm-1.sock"
    ledger_service.service.add_source("vm-1", socket_path, executor=None)

    run_cli(repo, "ledger", "bind", "vm-1", "--executor", "m2")
    assert wire.call(socket_path, "ping")["executor"] == "m2"


def unreachable(socket_path) -> bool:
    try:
        wire.call(socket_path, "ping")
    except wire.LedgerUnreachable:
        return True
    return False


def test_remove_source_closes_its_socket(repo, ledger_service):
    socket_path = ledger_service.dir / "vm-1.sock"
    ledger_service.service.add_source("vm-1", socket_path, executor=None)

    run_cli(repo, "ledger", "remove-source", "vm-1")
    assert (socket_path.exists(), unreachable(socket_path)) == (False, True)
