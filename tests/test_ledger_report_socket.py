"""The ledger service's report socket (#185): `metrics`, `fleet` and `log`, read-only,
for an operator's dashboard that must never be handed the admin socket."""

from __future__ import annotations

import os
import shutil
import stat
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from conftest import run_cli
from tddcli import ledger as ledger_mod
from tddcli import service, wire


def _at(minute):
    return f"2026-09-01T10:{minute:02d}:00+00:00"


#: (started, ended, outcome), by minute: run 1 ended, run 2 live.
TWO_RUNS = [(0, 10, "complete"), (25, None, None)]


def host_ledger(home: Path, runs) -> None:
    """The host's ledger for `somerepo`, holding source vm-1's `runs`, one cycle each."""
    home.mkdir(parents=True, exist_ok=True)
    ledger = ledger_mod.Ledger(Path("/somerepo"), path=home / "somerepo.sqlite3", source="vm-1")
    try:
        contract = ledger.insert(
            "plan_contract",
            plan_path="tasks/p.md",
            status="declared",
            declared_cycles='[{"n": 1}]',
            annotation_keys="[]",
            registered_at=_at(0),
            source="vm-1",
        )
        for started, ended, outcome in runs:
            run_id = ledger.insert(
                "run",
                plan_contract_id=contract,
                executor_model="m",
                executor_source="declared",
                worktree_path="/wt",
                started_at=_at(started),
                ended_at=_at(ended) if ended is not None else None,
                outcome=outcome,
                preexisting_dirty="[]",
                source="vm-1",
            )
            cycle_id = ledger.insert(
                "cycle",
                run_id=run_id,
                ordinal=1,
                kind="standard",
                projects='["p"]',
                declared_tests="[]",
                target_tests="[]",
                phase="CLOSED",
                head_at_open="0" * 40,
                opened_at=_at(started),
                closed_at=_at(ended) if ended is not None else None,
            )
            ledger.insert(
                "invocation",
                run_id=run_id,
                cycle_id=cycle_id,
                phase_at="AWAITING_TEST",
                project="p",
                adapter="pytest",
                other_failures="[]",
                duration_ms=30000,
                started_at=_at(started),
            )
    finally:
        ledger.close()


@pytest.fixture
def report_service(tmp_path, monkeypatch):
    """A ledger service with a report socket beside its admin socket, under /tmp."""
    sockets = Path(tempfile.mkdtemp(dir="/tmp", prefix="tdd-"))
    home = tmp_path / "host-ledgers"
    cfg = tmp_path / "ledger.toml"
    cfg.write_text(
        f'[service]\nadmin_socket = "{sockets / "admin.sock"}"\nhome = "{home}"\n'
        f'report_socket = "{sockets / "report.sock"}"\n'
    )
    monkeypatch.setenv("TDD_LEDGER_SERVICE_CONFIG", str(cfg))
    svc = service.Service(service.load_config(cfg))
    svc.start()
    try:
        yield SimpleNamespace(
            service=svc,
            home=home,
            dir=sockets,
            config=cfg,
            admin=sockets / "admin.sock",
            report=sockets / "report.sock",
        )
    finally:
        svc.stop()
        shutil.rmtree(sockets, ignore_errors=True)


def answer(socket_path, method, *args, **kwargs):
    """One request's result; a refusal's code, or what went wrong, as a string."""
    try:
        return wire.call(socket_path, method, *args, **kwargs)
    except wire.LedgerRefused as exc:
        return exc.refusal
    except wire.LedgerUnreachable:
        return "unreachable"
    except RuntimeError:
        return "error"


def run_ids(result):
    """The ids of `somerepo`'s runs in a `metrics` result; a failed answer unchanged."""
    if isinstance(result, str):
        return result
    return [r["run"] for r in ((result.get("repos") or {}).get("somerepo") or {}).get("runs", [])]


def test_the_report_socket_answers_as_the_admin_socket_does(report_service):
    host_ledger(report_service.home, TWO_RUNS)

    def view(sock):
        m, f, log = (
            answer(sock, "metrics"),
            answer(sock, "fleet"),
            answer(sock, "log", "somerepo", 1),
        )
        if not isinstance(m, str):
            m = [(r["run"], r["source"], r["outcome"]) for r in m["repos"]["somerepo"]["runs"]]
        if not isinstance(f, str):
            f = [(r["repo"], r["run_id"], r["source"]) for r in f["runs"]]
        return m, f, log

    assert view(report_service.report) == view(report_service.admin)


def test_the_report_socket_refuses_every_other_method(report_service, tmp_path):
    other = [
        ("ping", ()),
        ("sources", ()),
        ("add_source", ("vm-x", str(report_service.dir / "vm-x.sock"))),
        ("remove_source", ("vm-1",)),
        ("bind", ("vm-1", "m")),
        ("import", (str(tmp_path / "x.sqlite3"), "legacy")),
        ("open", (str(tmp_path),)),
        ("lease", ()),
        ("lease_snapshot", ()),
        ("run", (1,)),
        ("start_run", ()),
        ("insert", ("run",)),
    ]

    answers = {m: answer(report_service.report, m, *a) for m, a in other}

    assert answers == {m: "method_not_allowed" for m, _ in other}


@pytest.mark.skipif(os.geteuid() == 0, reason="root writes a mode-0444 file")
def test_the_report_socket_reads_ledgers_it_cannot_write(report_service):
    host_ledger(report_service.home, TWO_RUNS)
    # Before anything opens it, and never restored: a failed writer leaves its -wal and
    # -shm files at this mode too.
    (report_service.home / "somerepo.sqlite3").chmod(0o444)

    reads = [
        isinstance(answer(report_service.report, m, *a), dict)
        for m, a in (("metrics", ()), ("fleet", ()), ("log", ("somerepo", 1)))
    ]

    assert reads == [True, True, True]


def test_the_report_socket_is_mode_660(report_service):
    assert stat.S_IMODE(report_service.report.stat().st_mode) == 0o660


def test_a_report_socket_on_the_admin_path_is_refused(tmp_path):
    path = tmp_path / "ledger.toml"
    path.write_text(
        '[service]\nadmin_socket = "/tmp/tdd-185-admin.sock"\n'
        'report_socket = "/tmp/tdd-185-admin.sock"\n'
    )

    with pytest.raises(service.ServiceConfigError, match="report_socket"):
        service.load_config(path)


@pytest.mark.skipif(os.geteuid() == 0, reason="root connects to a mode-000 socket")
def test_ledger_reads_fall_back_to_the_report_socket(repo, report_service, tmp_path):
    host_ledger(report_service.home, TWO_RUNS)
    # The dashboard's account: refused on connect to the admin socket.
    report_service.admin.chmod(0)

    outs = [
        run_cli(repo, "ledger", *v)
        for v in (
            ("metrics",),
            ("fleet",),
            ("log", "--repo", "somerepo", "--run", "1", "--out", str(tmp_path / "log.md")),
        )
    ]

    assert [o.get("ok") for o in outs] == [True, True, True]
