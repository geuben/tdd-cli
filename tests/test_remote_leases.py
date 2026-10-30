"""One worker budget for every guest on a host.

Each guest's suites share the host's cores, so a socket-mode runner takes its worker
lease from the ledger service, which counts leases across every source. A lease ends
when its connection closes, which is also what a guest that dies does.
"""

from __future__ import annotations

import os

import pytest

from conftest import guest_config, run_cli
from tddcli import leases


@pytest.fixture(autouse=True)
def _twelve_cores(monkeypatch):
    # The service runs in this process, so it sees the same budget.
    monkeypatch.setenv("TDD_CORE_BUDGET", "12")
    # A guest caps the service's share at the CPUs it may use; make that no cap at all.
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: set(range(64)), raising=False)


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


def test_core_budget_does_not_cap_a_runner_that_keeps_its_own_ledger(
    split_runner, monkeypatch, tmp_path
):
    monkeypatch.setenv("TDD_LEASE_DIR", str(tmp_path / "leases"))
    split_runner.config.write_text(split_runner.config.read_text() + "core_budget = 2\n")

    with leases.worker_lease() as workers:
        assert workers == 12


def test_a_guest_caps_its_lease_at_the_cpus_it_may_use(split_guest, monkeypatch):
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: {0, 1, 2}, raising=False)

    with leases.worker_lease() as workers:
        assert workers == 3


def test_core_budget_is_the_guests_own_budget(split_guest, monkeypatch):
    got = {}
    for budget, cpus in ((4, 64), (64, 64), (10, 3)):
        monkeypatch.setattr(
            os, "sched_getaffinity", lambda _pid, n=cpus: set(range(n)), raising=False
        )
        guest_config(split_guest.runner, split_guest.socket, f"core_budget = {budget}\n")
        with leases.worker_lease() as workers:
            got[budget] = workers

    assert got == {4: 4, 64: 12, 10: 10}
