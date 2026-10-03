"""One worker budget for every guest on a host.

Each guest's suites share the host's cores, so a socket-mode runner takes its worker
lease from the ledger service, which counts leases across every source. A lease ends
when its connection closes, which is also what a guest that dies does.
"""

from __future__ import annotations

import pytest

from conftest import guest_config, run_cli
from tddcli import leases


@pytest.fixture(autouse=True)
def _twelve_cores(monkeypatch):
    # The service runs in this process, so it sees the same budget.
    monkeypatch.setenv("TDD_CORE_BUDGET", "12")


def as_second_guest(split_guest, ledger_service, monkeypatch, tmp_path) -> None:
    """Become guest `vm-2`, which shares no filesystem with `vm-1`: not even leases."""
    socket_path = ledger_service.dir / "vm-2.sock"
    if "vm-2" not in ledger_service.service.executors:
        ledger_service.service.add_source("vm-2", socket_path, executor=None)
    guest_config(split_guest.runner, socket_path)
    monkeypatch.setenv("TDD_LEASE_DIR", str(tmp_path / "vm-2-leases"))


def test_the_service_counts_leases_across_sources(
    split_guest, ledger_service, monkeypatch, tmp_path
):
    with leases.worker_lease():
        as_second_guest(split_guest, ledger_service, monkeypatch, tmp_path)
        with leases.worker_lease() as workers:
            second = workers

    assert second == 6


def test_a_lease_ends_when_its_connection_closes(
    split_guest, ledger_service, monkeypatch, tmp_path
):
    with leases.worker_lease():
        pass
    as_second_guest(split_guest, ledger_service, monkeypatch, tmp_path)

    with leases.worker_lease() as workers:
        assert workers == 12


def test_a_stale_lease_is_not_counted(split_guest, ledger_service, monkeypatch, tmp_path):
    with leases.worker_lease():
        monkeypatch.setattr(leases, "STALE_AFTER_S", 0)
        as_second_guest(split_guest, ledger_service, monkeypatch, tmp_path)
        with leases.worker_lease() as workers:
            second = workers

    assert second == 12


def test_guest_fleet_reports_the_hosts_lease_count(
    repo, split_guest, ledger_service, monkeypatch, tmp_path
):
    as_second_guest(split_guest, ledger_service, monkeypatch, tmp_path)
    with leases.worker_lease():
        guest_config(split_guest.runner, split_guest.socket)
        monkeypatch.setenv("TDD_LEASE_DIR", str(tmp_path / "vm-1-leases"))
        out = run_cli(repo, "fleet", "--json")

    assert out["result"]["suites"]["active"] == 1
