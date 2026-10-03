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
