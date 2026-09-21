"""Where the runner keeps its ledger, and who can open it."""

from __future__ import annotations

from conftest import run_cli


def _ledgers(directory) -> list[str]:
    return sorted(p.name for p in directory.glob("*.sqlite3")) if directory.is_dir() else []


def test_the_runner_ignores_the_callers_ledger_home(repo, ledger_home, split_runner):
    """`TDD_LEDGER_HOME` is the caller's to set, so the runner cannot follow it: that
    would put the ledger wherever the agent chose."""
    run_cli(repo, "doctor")

    found = (len(_ledgers(split_runner.ledger_home)), len(_ledgers(ledger_home)))
    assert found == (1, 0)
