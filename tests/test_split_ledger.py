"""Where the runner keeps its ledger, and who can open it."""

from __future__ import annotations

import stat

from conftest import run_cli


def _ledgers(directory) -> list[str]:
    return sorted(p.name for p in directory.glob("*.sqlite3")) if directory.is_dir() else []


def test_the_runner_ignores_the_callers_ledger_home(repo, ledger_home, split_runner):
    """`TDD_LEDGER_HOME` is the caller's to set, so the runner cannot follow it: that
    would put the ledger wherever the agent chose."""
    run_cli(repo, "doctor")

    found = (len(_ledgers(split_runner.ledger_home)), len(_ledgers(ledger_home)))
    assert found == (1, 0)


def test_the_runner_ledger_directory_is_mode_700(repo, split_runner):
    """Tightened on every open, not only on creation: an operator who made the
    directory by hand would otherwise leave it readable for good."""
    split_runner.ledger_home.mkdir(mode=0o755)

    run_cli(repo, "doctor")

    assert stat.S_IMODE(split_runner.ledger_home.stat().st_mode) == 0o700
