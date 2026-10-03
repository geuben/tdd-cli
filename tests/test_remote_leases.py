"""One worker budget for every guest on a host.

Each guest's suites share the host's cores, so a socket-mode runner takes its worker
lease from the ledger service, which counts leases across every source. A lease ends
when its connection closes, which is also what a guest that dies does.
"""

from __future__ import annotations

import pytest

from conftest import guest_config
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
