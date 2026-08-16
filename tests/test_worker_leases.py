"""Machine-wide worker leases (§10.7).

Concurrent agents on one machine each pinned `-n 1` to avoid oversubscribing the
box, which serialised every suite. The lease mechanism lets each in-flight suite
invocation claim an even share of the machine's cores instead.
"""

from __future__ import annotations

import json
import os
import subprocess
import time

import pytest

from tddcli import leases
from tddcli.adapters import base as adapters_base
from tddcli.adapters.pytest_adapter import PytestAdapter
from tddcli.adapters.vitest_adapter import VitestAdapter
from tddcli.config import Project


@pytest.fixture
def lease_dir(tmp_path, monkeypatch):
    d = tmp_path / "leases"
    monkeypatch.setenv("TDD_LEASE_DIR", str(d))
    monkeypatch.setenv("TDD_CORE_BUDGET", "8")
    return d


# -- budget arithmetic ---------------------------------------------------


def test_solo_agent_gets_every_core(lease_dir):
    with leases.worker_lease() as workers:
        assert workers == 8


def test_concurrent_agents_split_cores_evenly(lease_dir):
    with leases.worker_lease() as first:
        assert first == 8
        with leases.worker_lease() as second:
            assert second == 4


def test_worker_floor_is_one(lease_dir, monkeypatch):
    monkeypatch.setenv("TDD_CORE_BUDGET", "2")
    with leases.worker_lease():
        with leases.worker_lease():
            with leases.worker_lease() as third:
                assert third == 1


def test_explicit_total_overrides_environment(lease_dir):
    with leases.worker_lease(total_cores=12) as workers:
        assert workers == 12


def test_zero_budget_falls_back_to_cpu_count(lease_dir, monkeypatch):
    monkeypatch.setenv("TDD_CORE_BUDGET", "0")
    with leases.worker_lease() as workers:
        assert workers == (os.cpu_count() or 1)


# -- lease lifecycle -----------------------------------------------------


def test_lease_released_on_exit(lease_dir):
    with leases.worker_lease():
        assert len(list(lease_dir.iterdir())) == 1
    assert list(lease_dir.iterdir()) == []


def test_lease_released_on_exception(lease_dir):
    with pytest.raises(RuntimeError):
        with leases.worker_lease():
            raise RuntimeError("suite blew up")
    assert list(lease_dir.iterdir()) == []


def test_dead_pid_lease_is_swept(lease_dir):
    proc = subprocess.Popen(["true"])
    proc.wait()
    lease_dir.mkdir(parents=True)
    (lease_dir / f"{proc.pid}-dead.json").write_text(
        json.dumps({"pid": proc.pid, "started_at": time.time()})
    )
    with leases.worker_lease() as workers:
        assert workers == 8
    assert list(lease_dir.iterdir()) == []


def test_expired_lease_is_swept_even_if_pid_alive(lease_dir):
    lease_dir.mkdir(parents=True)
    stale = lease_dir / f"{os.getpid()}-old.json"
    stale.write_text(json.dumps({"pid": os.getpid(), "started_at": time.time()}))
    old = time.time() - leases.STALE_AFTER_S - 60
    os.utime(stale, (old, old))
    with leases.worker_lease() as workers:
        assert workers == 8
    assert list(lease_dir.iterdir()) == []


def test_unparsable_lease_is_swept(lease_dir):
    lease_dir.mkdir(parents=True)
    (lease_dir / "garbage.json").write_text("not json at all")
    with leases.worker_lease() as workers:
        assert workers == 8
    assert list(lease_dir.iterdir()) == []


def test_live_foreign_lease_counts(lease_dir):
    """A lease from another live process on this machine halves the budget."""
    lease_dir.mkdir(parents=True)
    (lease_dir / "999999999-other.json").write_text(
        json.dumps({"pid": os.getpid(), "started_at": time.time()})
    )
    with leases.worker_lease() as workers:
        assert workers == 4


# -- adapter integration -------------------------------------------------


@pytest.fixture
def recorded(monkeypatch):
    calls: list[dict] = []

    def stub(command, cwd, timeout=1800, extra_env=None, label=None):
        calls.append({"command": command, "cwd": cwd, "extra_env": extra_env})
        return 1, "", ""

    monkeypatch.setattr(adapters_base, "run_command", stub)
    return calls


def _pytest_adapter(tmp_path, test_command):
    project = Project(
        name="backend", root="backend", adapter="pytest",
        test_paths=["tests/"], test_command=test_command,
    )
    (tmp_path / "backend").mkdir(exist_ok=True)
    return PytestAdapter(project, tmp_path)


def test_pytest_adapter_substitutes_workers_placeholder(lease_dir, recorded, tmp_path):
    adapter = _pytest_adapter(tmp_path, "pytest -n {workers}")
    adapter.run(None)
    assert "pytest -n 8 " in recorded[0]["command"] + " "
    assert recorded[0]["extra_env"]["TDD_WORKERS"] == "8"


def test_pytest_adapter_leaves_declared_command_alone(lease_dir, recorded, tmp_path):
    adapter = _pytest_adapter(tmp_path, "pytest -n 1")
    adapter.run(None)
    assert recorded[0]["command"].startswith("pytest -n 1 ")
    assert recorded[0]["extra_env"]["TDD_WORKERS"] == "8"


def test_pytest_adapter_releases_lease_after_run(lease_dir, recorded, tmp_path):
    adapter = _pytest_adapter(tmp_path, "pytest -n {workers}")
    adapter.run(None)
    assert not lease_dir.is_dir() or list(lease_dir.iterdir()) == []


def test_vitest_adapter_substitutes_workers_placeholder(lease_dir, recorded, tmp_path):
    project = Project(
        name="frontend", root="frontend", adapter="vitest",
        test_paths=["**/*.test.ts"],
        test_command="npx vitest run --maxWorkers={workers}",
    )
    (tmp_path / "frontend").mkdir()
    adapter = VitestAdapter(project, tmp_path)
    adapter.run(None)
    assert "--maxWorkers=8" in recorded[0]["command"]
    assert recorded[0]["extra_env"]["TDD_WORKERS"] == "8"


def test_run_command_passes_extra_env(tmp_path):
    code, out, err = adapters_base.run_command(
        'echo "w=$TDD_WORKERS"', tmp_path, extra_env={"TDD_WORKERS": "6"}
    )
    assert code == 0
    assert out.strip() == "w=6"
