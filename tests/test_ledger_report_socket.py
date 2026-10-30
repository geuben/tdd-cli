"""The ledger service's report socket (#185): `metrics`, `fleet` and `log`, read-only,
for an operator's dashboard that must never be handed the admin socket."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

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
