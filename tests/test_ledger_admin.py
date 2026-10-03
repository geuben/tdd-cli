"""`tdd ledger …`: the operator's verbs, answered on the host over the admin socket.

The operator adds a source per guest, binds the executor it runs, and reads every
source's history in one place. None of these verbs is ever forwarded to a runner.
"""

from __future__ import annotations

import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from conftest import run_cli
from tddcli import service, wire


def test_ledger_verbs_are_never_forwarded_to_a_runner(repo, split_client, tmp_path, monkeypatch):
    monkeypatch.setenv("TDD_LEDGER_SERVICE_CONFIG", str(tmp_path / "no-service.toml"))

    out = run_cli(repo, "ledger", "sources")
    assert out.get("result", {}).get("reason") == "no_service"


def test_add_source_opens_a_guest_socket(repo, ledger_service):
    socket_path = ledger_service.dir / "vm-2.sock"
    run_cli(repo, "ledger", "add-source", "vm-2", "--socket", str(socket_path))

    assert wire.call(socket_path, "ping") == {"source": "vm-2", "executor": None}


def test_sources_lists_each_source_and_its_binding(repo, ledger_service):
    svc, sockets = ledger_service.service, ledger_service.dir
    svc.add_source("vm-2", sockets / "vm-2.sock", executor="m")
    svc.add_source("vm-1", sockets / "vm-1.sock", executor=None)

    out = run_cli(repo, "ledger", "sources")
    assert out["result"].get("sources") == [
        {"name": "vm-1", "socket": str(sockets / "vm-1.sock"), "executor": None},
        {"name": "vm-2", "socket": str(sockets / "vm-2.sock"), "executor": "m"},
    ]


def test_bind_changes_the_executor_for_the_next_run(repo, ledger_service):
    socket_path = ledger_service.dir / "vm-1.sock"
    ledger_service.service.add_source("vm-1", socket_path, executor=None)

    run_cli(repo, "ledger", "bind", "vm-1", "--executor", "m2")
    assert wire.call(socket_path, "ping")["executor"] == "m2"


def unreachable(socket_path) -> bool:
    try:
        wire.call(socket_path, "ping")
    except wire.LedgerUnreachable:
        return True
    return False


def test_remove_source_closes_its_socket(repo, ledger_service):
    socket_path = ledger_service.dir / "vm-1.sock"
    ledger_service.service.add_source("vm-1", socket_path, executor=None)

    run_cli(repo, "ledger", "remove-source", "vm-1")
    assert (socket_path.exists(), unreachable(socket_path)) == (False, True)


def ping_or_unreachable(socket_path):
    try:
        return wire.call(socket_path, "ping")
    except wire.LedgerUnreachable:
        return "unreachable"


def test_sources_survive_a_service_restart(ledger_service):
    socket_path = ledger_service.dir / "vm-1.sock"
    ledger_service.service.add_source("vm-1", socket_path, executor="m")
    ledger_service.service.stop()

    restarted = service.Service(service.load_config(ledger_service.config))
    restarted.start()
    try:
        reply = ping_or_unreachable(socket_path)
    finally:
        restarted.stop()
    assert reply == {"source": "vm-1", "executor": "m"}


def test_socket_modes(ledger_service):
    guest = ledger_service.dir / "vm-1.sock"
    ledger_service.service.add_source("vm-1", guest, executor=None)

    modes = {
        "admin": stat.S_IMODE((ledger_service.dir / "admin.sock").stat().st_mode),
        "vm-1": stat.S_IMODE(guest.stat().st_mode),
    }
    assert modes == {"admin": 0o600, "vm-1": 0o660}


def test_ledger_serve_runs_until_terminated(tmp_path):
    sockets = Path(tempfile.mkdtemp(dir="/tmp", prefix="tdd-"))
    cfg = tmp_path / "ledger.toml"
    cfg.write_text(
        f'[service]\nadmin_socket = "{sockets / "admin.sock"}"\nhome = "{tmp_path / "host"}"\n'
    )
    # No `python -m tddcli` entry point: call `main` as the installed script does.
    entry = "import sys; from tddcli.cli import main; sys.exit(main(sys.argv[1:]))"
    proc = subprocess.Popen(
        [sys.executable, "-c", entry, "ledger", "serve"],
        env={**os.environ, "TDD_LEDGER_SERVICE_CONFIG": str(cfg)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    answered = False
    try:
        deadline = time.monotonic() + 10
        while not answered and proc.poll() is None and time.monotonic() < deadline:
            answered = ping_or_unreachable(sockets / "admin.sock") != "unreachable"
            time.sleep(0.1)
        proc.send_signal(signal.SIGTERM)
        code = proc.wait(timeout=10)
    finally:
        if proc.poll() is None:
            proc.kill()
        shutil.rmtree(sockets, ignore_errors=True)
    assert (answered, code) == (True, 0)
