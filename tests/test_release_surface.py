"""The public surface added for the first release: --version, envelope versioning,
the Windows refusal, ledger schema-version gating, and adapter plugins."""

from __future__ import annotations

import os
import sqlite3
from types import SimpleNamespace

import pytest

from conftest import run_cli, run_cli_text
from tddcli import __version__, adapters
from tddcli.envelope import ENVELOPE_VERSION
from tddcli.ledger import SCHEMA_VERSION, Ledger, LedgerVersionError

# -- --version -------------------------------------------------------------


def test_version_flag_reports_the_package_version(repo):
    out = run_cli_text(repo, "--version")
    assert out.strip() == f"tdd-cli {__version__}"


# -- envelope_version ------------------------------------------------------


def test_every_envelope_carries_its_shape_version(repo):
    envelope = run_cli(repo, "status")
    assert envelope["envelope_version"] == ENVELOPE_VERSION


def test_failure_envelopes_carry_the_shape_version_too(repo):
    envelope = run_cli(repo, "advance")  # no active run
    assert envelope["ok"] is False
    assert envelope["envelope_version"] == ENVELOPE_VERSION


# -- Windows refusal -------------------------------------------------------


def test_windows_is_refused_loudly(repo, monkeypatch):
    monkeypatch.setattr(os, "name", "nt")
    envelope = run_cli(repo, "status")
    assert envelope["ok"] is False
    assert envelope["result"]["reason"] == "unsupported_platform"
    assert "Windows" in envelope["error"]


# -- ledger schema versioning ----------------------------------------------


def test_fresh_ledger_records_the_current_schema_version(repo, tmp_path):
    ledger = Ledger(tmp_path / "somerepo")
    row = ledger.one("SELECT value FROM meta WHERE key = 'schema_version'")
    assert int(row["value"]) == SCHEMA_VERSION


def test_older_ledger_is_migrated_forward(tmp_path, ledger_home):
    ledger = Ledger(tmp_path / "somerepo")
    ledger._write("UPDATE meta SET value = '1' WHERE key = 'schema_version'", ())
    ledger.db.close()

    reopened = Ledger(tmp_path / "somerepo")
    row = reopened.one("SELECT value FROM meta WHERE key = 'schema_version'")
    assert int(row["value"]) == SCHEMA_VERSION


def test_newer_ledger_is_refused_not_downgraded(tmp_path, ledger_home):
    ledger = Ledger(tmp_path / "somerepo")
    future = SCHEMA_VERSION + 7
    ledger._write("UPDATE meta SET value = ? WHERE key = 'schema_version'", (str(future),))
    marker = ledger.insert(
        "plan_contract", plan_path="p.md", status="undeclared",
        declared_cycles="[]", annotation_keys="[]", registered_at="t",
    )
    ledger.db.close()

    with pytest.raises(LedgerVersionError) as exc:
        Ledger(tmp_path / "somerepo")
    assert "newer tdd-cli" in str(exc.value)

    # Refusal must not have touched the database: version and rows survive.
    db = sqlite3.connect(str(ledger.path))
    assert db.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0] == str(future)
    assert db.execute("SELECT id FROM plan_contract").fetchone()[0] == marker
    db.close()


def test_newer_ledger_surfaces_as_a_failure_envelope_not_a_traceback(repo, ledger_home):
    from tddcli import gitutil

    ledger = Ledger(gitutil.repo_identity(repo))
    ledger._write(
        "UPDATE meta SET value = ? WHERE key = 'schema_version'",
        (str(SCHEMA_VERSION + 1),),
    )
    ledger.db.close()

    envelope = run_cli(repo, "status")
    assert envelope["ok"] is False
    assert "newer tdd-cli" in envelope["error"]


# -- adapter plugins -------------------------------------------------------


class FakeAdapter:
    def __init__(self, project, worktree):
        self.project, self.worktree = project, worktree


def _fake_entry_point(name, cls):
    return SimpleNamespace(name=name, load=lambda: cls)


def test_plugin_adapter_resolves_via_entry_point(monkeypatch, tmp_path):
    monkeypatch.setattr(
        adapters, "_entry_points", lambda: [_fake_entry_point("fake", FakeAdapter)]
    )
    project = SimpleNamespace(adapter="fake")
    built = adapters.build(project, tmp_path)
    assert isinstance(built, FakeAdapter)
    assert "fake" in adapters.available()


def test_builtin_adapter_cannot_be_shadowed_by_a_plugin(monkeypatch, tmp_path):
    monkeypatch.setattr(
        adapters, "_entry_points", lambda: [_fake_entry_point("pytest", FakeAdapter)]
    )
    project = SimpleNamespace(
        adapter="pytest", root=".", test_paths=["tests/"], test_command=None,
        lint=[], typecheck=[],
    )
    built = adapters.build(project, tmp_path)
    assert not isinstance(built, FakeAdapter)


def test_unknown_adapter_lists_plugins_in_the_error(monkeypatch, tmp_path):
    monkeypatch.setattr(
        adapters, "_entry_points", lambda: [_fake_entry_point("fake", FakeAdapter)]
    )
    with pytest.raises(RuntimeError) as exc:
        adapters.build(SimpleNamespace(adapter="nope"), tmp_path)
    assert "'nope'" in str(exc.value)
    assert "fake" in str(exc.value)
