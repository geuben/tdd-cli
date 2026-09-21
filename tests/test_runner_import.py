"""`tdd runner import`: bringing a single-user ledger under the runner.

Its history was written while the agent could reach it, so it arrives marked: the
runner keeps the record and says plainly which part of it nobody can vouch for.
"""

from __future__ import annotations

import json
import sqlite3

from conftest import current_user, run_cli, write_plan

MINIMAL_PLAN = """\
---
cycles:
  - n: 1
    project: backend
    title: "placeholder"
    test: "tests/test_smoke.py::test_smoke"
    commit_red: "test: placeholder"
    commit_green: "feat: placeholder"
---
# Minimal plan for runner-import tests
"""


def _legacy_ledger(repo, ledger_home):
    """A single-user ledger holding one run, as a machine has before it is split."""
    plan = write_plan(repo, MINIMAL_PLAN)
    run_cli(repo, "plan", "register", plan)
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]
    (path,) = ledger_home.glob("*.sqlite3")
    return path


def _become_the_runner(tmp_path, monkeypatch, sudo_shim, *, called_by: str | None):
    """Split the machine under the test. `called_by` is the uid sudo reports; None is an
    operator logged in as the runner, with no sudo in between."""
    home = tmp_path / "runner-ledgers"
    cfg = tmp_path / "runner.toml"
    cfg.write_text(
        f'[runner]\nuser = "{current_user()}"\ncommand = "tdd"\n'
        f'sudo = "{sudo_shim.path}"\nledger_home = "{home}"\n'
    )
    monkeypatch.setenv("TDD_RUNNER_CONFIG", str(cfg))
    if called_by is not None:
        monkeypatch.setenv("SUDO_USER", current_user())
        monkeypatch.setenv("SUDO_UID", called_by)
    return home


def _runs(path) -> list[int]:
    with sqlite3.connect(path) as db:
        return [row[0] for row in db.execute("SELECT id FROM run ORDER BY id")]


def _marker(path) -> dict:
    with sqlite3.connect(path) as db:
        row = db.execute("SELECT value FROM meta WHERE key = 'pre_split_import'").fetchone()
    return json.loads(row[0]) if row else {}


def test_import_copies_the_ledger_and_marks_it_pre_split(
    repo, ledger_home, tmp_path, monkeypatch, sudo_shim
):
    legacy = _legacy_ledger(repo, ledger_home)
    home = _become_the_runner(tmp_path, monkeypatch, sudo_shim, called_by=None)

    out = run_cli(repo, "runner", "import", str(legacy))

    copy = home / legacy.name
    imported = (
        out["ok"],
        _runs(copy) if copy.is_file() else None,
        _marker(copy).get("last_run_id") if copy.is_file() else None,
    )
    assert imported == (True, [1], 1)
