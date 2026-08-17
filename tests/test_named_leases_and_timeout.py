"""Named exclusive leases and per-project suite timeouts (issue #35).

Named leases give at-most-one machine-wide exclusion for suites that contend
over a shared resource (a device, a port-bound service). Per-project timeouts
let expensive suites declare a larger budget than the 1800 s default; doctor
warns when the configured timeout is smaller than a known baseline duration.
"""

from __future__ import annotations

import json
import os
import time

import pytest

from tddcli import config as config_mod
from tddcli import leases
from tddcli.adapters import base as adapters_base
from tddcli.adapters.pytest_adapter import PytestAdapter
from tddcli.config import Project

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def lease_dir(tmp_path, monkeypatch):
    d = tmp_path / "leases"
    monkeypatch.setenv("TDD_LEASE_DIR", str(d))
    monkeypatch.setenv("TDD_CORE_BUDGET", "8")
    return d


# ---------------------------------------------------------------------------
# named_lease — acquisition and release
# ---------------------------------------------------------------------------


def test_named_lease_creates_lock_file(lease_dir):
    with leases.named_lease("device-a"):
        lock = lease_dir / "named-device-a.lock"
        assert lock.exists()


def test_named_lease_removes_lock_file_on_exit(lease_dir):
    with leases.named_lease("device-a"):
        pass
    lock = lease_dir / "named-device-a.lock"
    assert not lock.exists()


def test_named_lease_removes_lock_on_exception(lease_dir):
    with pytest.raises(RuntimeError):
        with leases.named_lease("device-a"):
            raise RuntimeError("suite crashed")
    assert not (lease_dir / "named-device-a.lock").exists()


def test_named_lease_lock_file_contains_pid(lease_dir):
    with leases.named_lease("device-a"):
        payload = json.loads((lease_dir / "named-device-a.lock").read_text())
        assert payload["pid"] == os.getpid()


def test_named_lease_yields_none(lease_dir):
    with leases.named_lease("device-a") as result:
        assert result is None


def test_named_lease_distinct_names_do_not_contend(lease_dir):
    with leases.named_lease("device-a"):
        # device-b is a separate lock — acquiring it must not block
        with leases.named_lease("device-b"):
            assert (lease_dir / "named-device-a.lock").exists()
            assert (lease_dir / "named-device-b.lock").exists()


# ---------------------------------------------------------------------------
# named_lease — stale sweeping
# ---------------------------------------------------------------------------


def test_named_lease_sweeps_stale_lock_by_age(lease_dir):
    lease_dir.mkdir(parents=True, exist_ok=True)
    lock = lease_dir / "named-device-a.lock"
    lock.write_text(json.dumps({"pid": os.getpid(), "started_at": time.time()}))
    old = time.time() - leases.STALE_AFTER_S - 60
    os.utime(lock, (old, old))
    # Should not block — stale lock is swept immediately
    with leases.named_lease("device-a"):
        pass


def test_named_lease_sweeps_dead_pid_lock(lease_dir):
    import subprocess

    proc = subprocess.Popen(["true"])
    proc.wait()  # pid is now dead

    lease_dir.mkdir(parents=True, exist_ok=True)
    lock = lease_dir / "named-device-a.lock"
    lock.write_text(json.dumps({"pid": proc.pid, "started_at": time.time()}))

    with leases.named_lease("device-a"):
        pass  # swept and acquired without waiting


# ---------------------------------------------------------------------------
# named_lease — heartbeat while waiting
# ---------------------------------------------------------------------------


def test_named_lease_emits_heartbeat_while_waiting(lease_dir, monkeypatch):
    """When the lock is held by another live process, a heartbeat fires each poll."""
    lease_dir.mkdir(parents=True, exist_ok=True)
    lock = lease_dir / "named-device-a.lock"
    lock.write_text(json.dumps({"pid": os.getpid(), "started_at": time.time()}))

    attempt_count = 0

    def fake_sleep(n):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count >= 1:
            # Release the lock so the next iteration can acquire it
            lock.unlink()

    emitted = []

    def fake_heartbeat(**kwargs):
        emitted.append(kwargs)

    monkeypatch.setattr(leases, "heartbeat", fake_heartbeat)
    monkeypatch.setattr(leases.time, "sleep", fake_sleep)

    with leases.named_lease("device-a"):
        pass

    assert any(e.get("event") == "lease_waiting" and e.get("lease") == "device-a" for e in emitted)


# ---------------------------------------------------------------------------
# per-project timeout flows through to run_command
# ---------------------------------------------------------------------------


@pytest.fixture
def recorded_calls(monkeypatch):
    calls = []

    def stub(command, cwd, timeout=1800, extra_env=None, label=None):
        calls.append({"command": command, "timeout": timeout, "extra_env": extra_env})
        return 0, "", ""

    monkeypatch.setattr(adapters_base, "run_command", stub)
    return calls


def _make_adapter(tmp_path, timeout=None, lease=None):
    project = Project(
        name="native-ios",
        root="native-ios",
        adapter="pytest",
        test_paths=["tests/"],
        test_command="pytest",
        timeout=timeout,
        lease=lease,
    )
    (tmp_path / "native-ios").mkdir(exist_ok=True)
    return PytestAdapter(project, tmp_path)


def test_default_timeout_is_1800(lease_dir, recorded_calls, tmp_path):
    adapter = _make_adapter(tmp_path)
    adapter._run_suite("pytest")
    assert recorded_calls[0]["timeout"] == 1800


def test_project_timeout_overrides_default(lease_dir, recorded_calls, tmp_path):
    adapter = _make_adapter(tmp_path, timeout=7200)
    adapter._run_suite("pytest")
    assert recorded_calls[0]["timeout"] == 7200


def test_explicit_timeout_arg_overrides_project(lease_dir, recorded_calls, tmp_path):
    adapter = _make_adapter(tmp_path, timeout=7200)
    adapter._run_suite("pytest", timeout=300)
    assert recorded_calls[0]["timeout"] == 300


# ---------------------------------------------------------------------------
# project.lease causes named_lease to be acquired
# ---------------------------------------------------------------------------


def test_project_with_lease_acquires_named_lock(lease_dir, recorded_calls, tmp_path):
    adapter = _make_adapter(tmp_path, lease="device-ios")
    adapter._run_suite("pytest")
    lock = lease_dir / "named-device-ios.lock"
    # Lock is released after the suite run
    assert not lock.exists()
    # But the suite did run
    assert len(recorded_calls) == 1


def test_project_without_lease_does_not_create_named_lock(lease_dir, recorded_calls, tmp_path):
    adapter = _make_adapter(tmp_path)
    adapter._run_suite("pytest")
    named_locks = list(lease_dir.glob("named-*.lock")) if lease_dir.exists() else []
    assert named_locks == []


# ---------------------------------------------------------------------------
# Config parsing — lease and timeout on Project and Override
# ---------------------------------------------------------------------------


def test_config_parses_project_lease_and_timeout(tmp_path):
    (tmp_path / "tdd.toml").write_text("""
[project.native-ios]
root         = "native-ios"
adapter      = "xctest"
test_paths   = ["Tests/"]
test_command = "xcodebuild test"
lease        = "device-ios"
timeout      = 3600
""")
    (tmp_path / "native-ios").mkdir()
    cfg = config_mod.load(tmp_path)
    p = cfg.project("native-ios")
    assert p.lease == "device-ios"
    assert p.timeout == 3600


def test_config_project_defaults_to_no_lease_and_no_timeout(tmp_path):
    (tmp_path / "tdd.toml").write_text("""
[project.backend]
root      = "backend"
adapter   = "pytest"
test_paths = ["tests/"]
""")
    (tmp_path / "backend").mkdir()
    cfg = config_mod.load(tmp_path)
    p = cfg.project("backend")
    assert p.lease is None
    assert p.timeout is None


def test_config_parses_override_lease_and_timeout(tmp_path):
    (tmp_path / "tdd.toml").write_text("""
[project.backend]
root      = "backend"
adapter   = "pytest"
test_paths = ["tests/"]

[[project.backend.override]]
pattern      = "e2e/"
test_command = "pytest e2e/"
lease        = "staging-db"
timeout      = 900
""")
    (tmp_path / "backend").mkdir()
    cfg = config_mod.load(tmp_path)
    ov = cfg.project("backend").overrides[0]
    assert ov.lease == "staging-db"
    assert ov.timeout == 900


def test_config_rejects_non_integer_timeout(tmp_path):
    (tmp_path / "tdd.toml").write_text("""
[project.backend]
root      = "backend"
adapter   = "pytest"
test_paths = ["tests/"]
timeout   = "not-an-int"
""")
    (tmp_path / "backend").mkdir()
    with pytest.raises(config_mod.ConfigError, match="timeout must be an integer"):
        config_mod.load(tmp_path)


def test_config_rejects_non_integer_override_timeout(tmp_path):
    (tmp_path / "tdd.toml").write_text("""
[project.backend]
root      = "backend"
adapter   = "pytest"
test_paths = ["tests/"]

[[project.backend.override]]
pattern      = "e2e/"
test_command = "pytest e2e/"
timeout      = "oops"
""")
    (tmp_path / "backend").mkdir()
    with pytest.raises(config_mod.ConfigError, match="timeout must be an integer"):
        config_mod.load(tmp_path)


# ---------------------------------------------------------------------------
# Ledger — max_suite_duration_ms
# ---------------------------------------------------------------------------


def test_max_suite_duration_returns_none_with_no_invocations(tmp_path, ledger_home):
    from tddcli.ledger import Ledger

    ledger = Ledger(tmp_path)
    assert ledger.max_suite_duration_ms("backend") is None


def _insert_invocation(ledger, project: str, duration_ms: int, target_test=None):
    """Insert a fake full-suite invocation, bypassing FK checks."""
    ledger.db.execute("PRAGMA foreign_keys=OFF")
    cols = {
        "run_id": 1,
        "phase_at": "RED",
        "project": project,
        "adapter": "pytest",
        "total_passed": 1,
        "total_failed": 0,
        "other_failures": "[]",
        "duration_ms": duration_ms,
        "started_at": "2026-01-01",
    }
    if target_test is not None:
        cols["target_test"] = target_test
    ledger.insert("invocation", **cols)
    ledger.db.commit()
    ledger.db.execute("PRAGMA foreign_keys=ON")


def test_max_suite_duration_returns_max_from_invocations(tmp_path, ledger_home):
    from tddcli.ledger import Ledger

    ledger = Ledger(tmp_path)
    _insert_invocation(ledger, "backend", 45000)
    _insert_invocation(ledger, "backend", 30000)
    # Targeted invocation — must be excluded from the max
    _insert_invocation(
        ledger, "backend", 999999, target_test="backend::tests/test_foo.py::test_bar"
    )

    assert ledger.max_suite_duration_ms("backend") == 45000


def test_max_suite_duration_excludes_other_projects(tmp_path, ledger_home):
    from tddcli.ledger import Ledger

    ledger = Ledger(tmp_path)
    _insert_invocation(ledger, "frontend", 99000)

    assert ledger.max_suite_duration_ms("backend") is None


# ---------------------------------------------------------------------------
# Doctor — timeout check
# ---------------------------------------------------------------------------


TOML_WITH_TIMEOUT = """
[project.backend]
root       = "backend"
adapter    = "pytest"
test_paths = ["tests/"]
timeout    = 60
"""


def test_doctor_timeout_check_fails_when_baseline_exceeds_it(repo, ledger_home):
    """When a known run exceeded the configured timeout, doctor fails the check."""
    import subprocess

    from conftest import run_cli
    from tddcli.ledger import Ledger

    def git(cwd, *args):
        subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True)

    # Add a timeout that is shorter than we will inject into the ledger
    (repo / "tdd.toml").write_text(
        "[project.backend]\n"
        'root       = "backend"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "timeout    = 60\n"  # 60 s
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "add timeout")

    # Insert a full-suite invocation that took 90 s (exceeds 60 s)
    ledger = Ledger(repo)
    _insert_invocation(ledger, "backend", 90000)

    out = run_cli(repo, "doctor")
    timeout_checks = [
        c for c in out["result"]["checks"] if c["check"] == "timeout exceeds known baseline"
    ]
    assert len(timeout_checks) == 1
    assert timeout_checks[0]["ok"] is False
    assert "90" in timeout_checks[0]["detail"] or "60" in timeout_checks[0]["detail"]


def test_doctor_timeout_check_passes_when_timeout_is_sufficient(repo, ledger_home):
    """Doctor passes the timeout check when configured timeout exceeds baseline."""
    import subprocess

    from conftest import run_cli
    from tddcli.ledger import Ledger

    def git(cwd, *args):
        subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True)

    (repo / "tdd.toml").write_text(
        "[project.backend]\n"
        'root       = "backend"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "timeout    = 3600\n"  # 3600 s >> 30 s invocation
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "add timeout")

    ledger = Ledger(repo)
    _insert_invocation(ledger, "backend", 30000)

    out = run_cli(repo, "doctor")
    timeout_checks = [
        c for c in out["result"]["checks"] if c["check"] == "timeout exceeds known baseline"
    ]
    assert len(timeout_checks) == 1
    assert timeout_checks[0]["ok"] is True


def test_doctor_skips_timeout_check_when_no_timeout_configured(repo, ledger_home):
    """When no timeout is configured the check does not appear."""
    from conftest import run_cli

    out = run_cli(repo, "doctor")
    timeout_checks = [
        c for c in out["result"]["checks"] if c["check"] == "timeout exceeds known baseline"
    ]
    assert timeout_checks == []


def test_doctor_passes_timeout_check_with_no_history(repo, ledger_home):
    """When there are no invocations yet, the check does not fail."""
    import subprocess

    from conftest import run_cli

    def git(cwd, *args):
        subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True)

    (repo / "tdd.toml").write_text(
        "[project.backend]\n"
        'root       = "backend"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "timeout    = 60\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "add timeout")

    out = run_cli(repo, "doctor")
    timeout_checks = [
        c for c in out["result"]["checks"] if c["check"] == "timeout exceeds known baseline"
    ]
    # No prior invocations → check is present but passes
    assert all(c["ok"] is True for c in timeout_checks)
