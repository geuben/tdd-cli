"""`tdd runner import`: bringing a single-user ledger under the runner.

Its history was written while the agent could reach it, so it arrives marked: the
runner keeps the record and says plainly which part of it nobody can vouch for.
"""

from __future__ import annotations

import json
import os
import sqlite3

import pytest

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


def test_import_refuses_to_overwrite_an_existing_ledger(
    repo, ledger_home, tmp_path, monkeypatch, sudo_shim
):
    """The runner's copy may have grown since: a second import would erase runs that
    were recorded out of the agent's reach, in favour of ones that were not."""
    legacy = _legacy_ledger(repo, ledger_home)
    _become_the_runner(tmp_path, monkeypatch, sudo_shim, called_by=None)
    run_cli(repo, "runner", "import", str(legacy))

    again = run_cli(repo, "runner", "import", str(legacy))

    assert (again["ok"], again["result"].get("reason")) == (False, "ledger_exists")


@pytest.mark.skipif(os.geteuid() == 0, reason="root is an operator, not an agent")
def test_import_is_refused_for_an_agent_caller(repo, ledger_home, tmp_path, monkeypatch, sudo_shim):
    """An agent reaches the runner through sudo like everyone else. If it could import,
    it could hand the runner a history it wrote itself."""
    legacy = _legacy_ledger(repo, ledger_home)
    home = _become_the_runner(tmp_path, monkeypatch, sudo_shim, called_by=str(os.geteuid()))

    out = run_cli(repo, "runner", "import", str(legacy))

    refused = (out["result"].get("reason"), (home / legacy.name).exists())
    assert refused == ("operator_only", False)


def test_import_is_refused_in_single_mode(repo, ledger_home, tmp_path):
    """With no runner there is nowhere out of reach to import into: the copy would land
    back in the caller's own ledger home and claim a protection nobody has."""
    legacy = _legacy_ledger(repo, ledger_home)
    elsewhere = tmp_path / "copied-aside.sqlite3"
    elsewhere.write_bytes(legacy.read_bytes())

    out = run_cli(repo, "runner", "import", str(elsewhere))

    refused = (out["result"].get("reason"), (ledger_home / elsewhere.name).exists())
    assert refused == ("not_split", False)


def test_metrics_reports_the_pre_split_marker(repo, ledger_home, tmp_path, monkeypatch, sudo_shim):
    """The marker is only worth writing if whoever compares runs is told about it."""
    legacy = _legacy_ledger(repo, ledger_home)
    _become_the_runner(tmp_path, monkeypatch, sudo_shim, called_by=None)
    run_cli(repo, "runner", "import", str(legacy))
    monkeypatch.setenv("SUDO_USER", current_user())  # an agent asks, as it would

    out = run_cli(repo, "metrics")

    assert out["result"]["pre_split_import"]["last_run_id"] == 1


def test_root_may_import_and_is_told_what_was_marked(
    repo, ledger_home, tmp_path, monkeypatch, sudo_shim
):
    """The documented way in: `sudo -u <runner> tdd runner import` from a root shell,
    where sudo reports uid 0. The operator sees which runs were marked without opening
    the ledger."""
    legacy = _legacy_ledger(repo, ledger_home)
    _become_the_runner(tmp_path, monkeypatch, sudo_shim, called_by="0")

    out = run_cli(repo, "runner", "import", str(legacy))

    told = (out["ok"], out["result"]["pre_split_import"]["last_run_id"])
    assert told == (True, 1)
