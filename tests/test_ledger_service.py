"""The ledger service: the host owns the ledger, and each guest reaches it over a socket.

A guest's runner keeps running suites, gates and git as the agent, but keeps no ledger
of its own. It reads and writes the host's through a unix socket, and the source its
runs are recorded under is the socket they arrived on, never anything it says.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from conftest import current_user, guest_config, run_cli, run_cli_text, write_plan
from tddcli import gitutil, service, wire
from tddcli import ledger as ledger_mod

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
# Minimal plan for ledger service tests
"""


def start_run(repo) -> dict:
    plan = write_plan(repo, MINIMAL_PLAN)
    run_cli(repo, "plan", "register", plan)
    return run_cli(repo, "run", "start", "--plan", plan)


def host_file(ledger_service, repo) -> Path:
    """Where the host keeps this repository's ledger."""
    return ledger_service.home / f"{ledger_mod.slug(gitutil.repo_identity(repo))}.sqlite3"


def test_a_source_socket_answers_ping_with_its_name(tmp_path):
    # Under /tmp, not tmp_path: a socket path under tmp_path is longer than AF_UNIX allows.
    sockets = Path(tempfile.mkdtemp(dir="/tmp", prefix="tdd-"))
    config = tmp_path / "ledger.toml"
    config.write_text(
        f'[service]\nadmin_socket = "{sockets / "admin.sock"}"\n'
        f'home = "{tmp_path / "host-ledgers"}"\n'
    )
    svc = service.Service(service.load_config(config))
    try:
        svc.start()
        svc.add_source("vm-1", sockets / "vm-1.sock", executor=None)
        reply = wire.call(sockets / "vm-1.sock", "ping")
    finally:
        svc.stop()
        shutil.rmtree(sockets, ignore_errors=True)
    assert reply == {"source": "vm-1", "executor": None}


def test_a_guest_run_lands_in_the_host_ledger_under_its_source(repo, split_guest, ledger_service):
    start_run(repo)

    reader = ledger_mod.open_readonly(host_file(ledger_service, repo), source=None)
    assert reader is not None and [r["source"] for r in reader.active_runs()] == ["vm-1"]


def test_a_guest_renders_its_own_friction_log(repo, split_guest):
    start_run(repo)

    assert "tasks/plan.md" in run_cli_text(repo, "log", "render")


def test_a_blocked_guest_run_can_be_unblocked(repo, split_guest):
    start_run(repo)
    run_cli(repo, "blocker", "--kind", "plan_defect", "--detail", "x")

    out = run_cli(repo, "resume", "--unblock", "--note", "fixed")
    assert out["result"].get("resumed") is True


def test_an_unreachable_socket_refuses_the_verb(repo, split_guest, ledger_service):
    guest_config(split_guest.runner, ledger_service.dir / "absent.sock")

    out = start_run(repo)
    local = sorted(str(p) for p in split_guest.guest_home.rglob("*.sqlite3"))
    assert {"reason": out["result"].get("reason"), "local_ledgers": local} == {
        "reason": "ledger_unreachable",
        "local_ledgers": [],
    }


def test_a_guest_naming_another_sources_run_is_refused(repo, split_guest, ledger_service):
    ledger_service.service.add_source("vm-2", ledger_service.dir / "vm-2.sock", executor=None)
    run_id = start_run(repo)["run"]["id"]
    guest_config(split_guest.runner, ledger_service.dir / "vm-2.sock")

    out = run_cli(repo, "run", "abandon", "--run", str(run_id), "--reason", "x")
    assert {k: out["result"].get(k) for k in ("reason", "refusal")} == {
        "reason": "ledger_refused",
        "refusal": "foreign_run",
    }


def test_a_guest_naming_another_sources_cycle_is_refused(repo, split_guest, ledger_service):
    ledger_service.service.add_source("vm-2", ledger_service.dir / "vm-2.sock", executor=None)
    start_run(repo)
    host = ledger_mod.open_readonly(host_file(ledger_service, repo), source=None)
    cycle_id = host.open_cycle(host.active_runs()[0]["id"])["id"]

    conn = wire.Connection(ledger_service.dir / "vm-2.sock")
    try:
        conn.request("open", str(gitutil.repo_identity(repo)))
        with pytest.raises(wire.LedgerRefused) as refused:
            conn.request("cycle", cycle_id)
    finally:
        conn.close()
    assert refused.value.refusal == "foreign_run"


def refusal_of(socket_path, repo_path: str, method: str, *args, **kwargs) -> str:
    """What the service says to `method` on a fresh connection: its refusal, or accepted."""
    conn = wire.Connection(socket_path)
    try:
        conn.request("open", repo_path)
        conn.request(method, *args, **kwargs)
    except wire.LedgerRefused as exc:
        return exc.refusal
    finally:
        conn.close()
    return "accepted"


def test_a_guest_cannot_call_a_host_only_method(repo, split_guest):
    refusal = refusal_of(
        split_guest.socket, str(gitutil.repo_identity(repo)), "insert", "meta", key="k", value="v"
    )
    assert refusal == "method_not_allowed"


def open_refusal(socket_path, repo_path: str) -> str:
    """What the service says to `open`: its refusal, or accepted."""
    try:
        conn = wire.Connection(socket_path)
    except wire.LedgerUnreachable:
        return "unreachable"
    try:
        conn.request("open", repo_path)
    except wire.LedgerRefused as exc:
        return exc.refusal
    except wire.LedgerUnreachable:
        return "unreachable"
    finally:
        conn.close()
    return "accepted"


def test_a_malformed_repo_path_is_refused(split_guest):
    malformed = ["relative/repo", "", "/a\x00b", "/a\nb"]

    assert [open_refusal(split_guest.socket, p) for p in malformed] == ["bad_repo"] * 4


def complete_on_host(ledger_service, repo) -> int:
    """Start a guest run, then mark it complete through the host's unscoped view."""
    run_id = start_run(repo)["run"]["id"]
    host = ledger_mod.Ledger(repo, source=None, path=host_file(ledger_service, repo))
    host.update("run", run_id, ended_at=ledger_mod.now(), outcome="complete")
    host.close()
    return run_id


def test_a_guest_cannot_write_to_a_completed_run(repo, split_guest, ledger_service):
    run_id = complete_on_host(ledger_service, repo)

    refusal = refusal_of(
        split_guest.socket, str(gitutil.repo_identity(repo)), "event", run_id, None, "x", ""
    )
    assert refusal == "run_closed"


def test_a_guest_may_still_note_a_completed_run(repo, split_guest, ledger_service):
    complete_on_host(ledger_service, repo)

    out = run_cli(repo, "note", "after the fact")
    assert out["result"].get("noted") is True


def host_run(ledger_service, repo, run_id: int):
    return ledger_mod.open_readonly(host_file(ledger_service, repo), source=None).run(run_id)


def test_a_bound_source_records_the_operator_assigned_executor(repo, split_guest, ledger_service):
    ledger_service.service.add_source("vm-b", ledger_service.dir / "vm-b.sock", executor="model-x")
    guest_config(split_guest.runner, ledger_service.dir / "vm-b.sock")

    run = host_run(ledger_service, repo, start_run(repo)["run"]["id"])
    assert (run["executor_model"], run["executor_source"]) == ("model-x", "operator")


def test_an_unbound_source_downgrades_a_guest_operator_claim(repo, split_guest, ledger_service):
    guest_config(
        split_guest.runner,
        split_guest.socket,
        extra=f'[executor]\n"{current_user()}" = "guest-says"\n',
    )

    run = host_run(ledger_service, repo, start_run(repo)["run"]["id"])
    assert (run["executor_model"], run["executor_source"]) == ("guest-says", "claimed")
