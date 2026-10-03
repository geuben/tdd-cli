"""`tdd ledger …`: the operator's verbs, answered on the host over the admin socket.

The operator adds a source per guest, binds the executor it runs, and reads every
source's history in one place. None of these verbs is ever forwarded to a runner.
"""

from __future__ import annotations

from conftest import run_cli


def test_ledger_verbs_are_never_forwarded_to_a_runner(repo, split_client, tmp_path, monkeypatch):
    monkeypatch.setenv("TDD_LEDGER_SERVICE_CONFIG", str(tmp_path / "no-service.toml"))

    out = run_cli(repo, "ledger", "sources")
    assert out.get("result", {}).get("reason") == "no_service"
