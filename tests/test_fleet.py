"""`tdd fleet` — every agent's progress on this repository, in one view.

Safety contract: the command runs against a ledger that live agents are writing.
It must open the database read-only (`mode=ro`) so it is structurally incapable
of creating, migrating, or mutating it — and must not require an active run,
a registered plan, or even an existing ledger in the worktree it runs from.
"""

from __future__ import annotations

import json
import os
import socket
import sqlite3
import subprocess
import time

from conftest import run_cli, write_plan
from tddcli import fleet, leases
from tddcli.ledger import Ledger, ledger_path

PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
  - n: 2
    project: backend
    title: "subtracting"
    test: "tests/test_sub.py::test_subtract"
---

# Plan
"""


def start_run(repo):
    plan = write_plan(repo, PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    started = run_cli(repo, "run", "start", "--plan", plan)
    assert started["ok"], started
    return started


# -- command surface -----------------------------------------------------


def test_fleet_with_no_ledger_reports_no_runs(repo):
    out = run_cli(repo, "fleet", "--json")
    assert out["ok"] is True
    assert out["result"]["runs"] == []


def test_fleet_does_not_create_a_ledger(repo, ledger_home):
    run_cli(repo, "fleet", "--json")
    assert list(ledger_home.glob("*.sqlite3")) == []


def test_fleet_lists_an_active_run(repo):
    start_run(repo)
    out = run_cli(repo, "fleet", "--json")
    assert out["ok"] is True
    (row,) = out["result"]["runs"]
    assert row["worktree"] == str(repo)
    assert row["plan"] == "tasks/plan.md"
    assert row["cycle"] == 1
    assert row["of"] == 2
    assert row["phase"] == "AWAITING_TEST"
    assert row["last_activity_age_s"] is not None


def test_fleet_shows_runs_from_other_worktrees(repo):
    """The ledger is one per repository; a run claimed by any worktree appears."""
    start_run(repo)
    ledger = Ledger(repo)
    ledger.db.execute("UPDATE run SET worktree_path = ? WHERE 1", ("/somewhere/else/wt-2",))
    ledger.db.commit()
    out = run_cli(repo, "fleet", "--json")
    (row,) = out["result"]["runs"]
    assert row["worktree"] == "/somewhere/else/wt-2"


def test_fleet_excludes_ended_runs(repo):
    start_run(repo)
    ledger = Ledger(repo)
    ledger.db.execute("UPDATE run SET ended_at = 'x', outcome = 'complete' WHERE 1")
    ledger.db.commit()
    out = run_cli(repo, "fleet", "--json")
    assert out["result"]["runs"] == []


def test_fleet_reports_inflight_baseline_claims(repo):
    ledger = Ledger(repo)
    ledger.claim(str(repo), "host-1", os.getpid(), projects_total=3)
    ledger.update_claim(str(repo), projects_done=1, current_project="backend")
    out = run_cli(repo, "fleet", "--json")
    (claim,) = out["result"]["collecting"]
    assert claim["worktree"] == str(repo)
    assert claim["projects_done"] == 1
    assert claim["projects_total"] == 3
    assert claim["current_project"] == "backend"


def test_fleet_reports_live_worker_leases(repo, tmp_path, monkeypatch):
    monkeypatch.setenv("TDD_CORE_BUDGET", "8")
    with leases.worker_lease():
        out = run_cli(repo, "fleet", "--json")
    suites = out["result"]["suites"]
    assert suites["active"] == 1
    assert suites["total_cores"] == 8
    assert suites["workers_each"] == 8


def test_fleet_human_output_renders_one_line_per_run(repo):
    start_run(repo)
    from conftest import run_cli_text

    text = run_cli_text(repo, "fleet")
    assert str(repo) in text
    assert "cycle 1/2" in text
    assert "AWAITING_TEST" in text


# -- read-only guarantee -------------------------------------------------


def test_open_readonly_cannot_write(repo, ledger_home):
    Ledger(repo)  # create the db
    conn = fleet.open_readonly(ledger_path(repo))
    try:
        conn.execute("INSERT INTO meta(key, value) VALUES ('x', 'y')")
        raise AssertionError("write succeeded on a read-only connection")
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()


def test_open_readonly_returns_none_for_missing_db(tmp_path):
    assert fleet.open_readonly(tmp_path / "absent.sqlite3") is None


# -- lease snapshot ------------------------------------------------------


def test_lease_snapshot_counts_only_live_leases(tmp_path, monkeypatch):
    monkeypatch.setenv("TDD_CORE_BUDGET", "8")
    d = leases.lease_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / "1-stale.json").write_text(json.dumps({"pid": 1, "started_at": 0}))
    old = time.time() - leases.STALE_AFTER_S - 60
    os.utime(d / "1-stale.json", (old, old))
    with leases.worker_lease():
        snap = leases.snapshot()
    assert snap["active"] == 1
    assert snap["total_cores"] == 8
    assert snap["workers_each"] == 8


def test_lease_snapshot_with_no_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("TDD_LEASE_DIR", str(tmp_path / "never-created"))
    snap = leases.snapshot()
    assert snap["active"] == 0


# -- claim liveness ----------------------------------------------------------


def test_render_lists_advance_claims_and_marks_a_dead_holder():
    summary = {
        "runs": [],
        "collecting": [],
        "suites": {"active": 0, "total_cores": 8, "workers_each": 8},
        "advancing": [
            {"worktree": "/wt-1", "hostname": "h", "pid": 4242, "stale": True, "elapsed_s": 91.0},
            {"worktree": "/wt-2", "hostname": "h", "pid": 4243, "stale": False, "elapsed_s": 2.0},
        ],
    }
    expected = (
        "/wt-1  advance in flight — 91.0s elapsed — holder (pid 4242) is dead\n"
        "/wt-2  advance in flight — 2.0s elapsed\n"
        "suites executing now: 0 — 8 worker(s) each of 8 cores\n"
    )
    assert fleet.render(summary) == expected


def test_fleet_lists_advance_claims_with_holder_liveness(repo):
    proc = subprocess.Popen(["true"])
    proc.wait()
    dead_pid = proc.pid
    live_pid = os.getpid()
    dead_wt = str(repo)
    live_wt = str(repo) + "-wt2"
    hostname = socket.gethostname()

    ledger = Ledger(repo)
    ledger.claim_advance(dead_wt, hostname, dead_pid)
    ledger.claim_advance(live_wt, hostname, live_pid)

    out = run_cli(repo, "fleet", "--json")
    rows = {r["worktree"]: (r.get("stale"), r.get("pid")) for r in out["result"].get("advancing") or []}
    assert rows == {dead_wt: (True, dead_pid), live_wt: (False, live_pid)}


def test_fleet_and_progress_agree_on_a_dead_collector(repo):
    proc = subprocess.Popen(["true"])
    proc.wait()
    dead_pid = proc.pid
    hostname = socket.gethostname()

    ledger = Ledger(repo)
    ledger.claim(str(repo), hostname, dead_pid, projects_total=2)

    fleet_out = run_cli(repo, "fleet", "--json")
    progress_out = run_cli(repo, "progress", "--json")

    (fleet_row,) = fleet_out["result"]["collecting"]
    progress_result = progress_out["result"]
    assert (fleet_row["stale"], fleet_row["pid"]) == (progress_result["stale"], progress_result["pid"])


def test_render_marks_a_dead_collector_and_leaves_a_live_one_alone():
    summary = {
        "runs": [],
        "advancing": [],
        "collecting": [
            {"worktree": "/wt-1", "hostname": "h", "projects_done": 1, "projects_total": 3,
             "current_project": "backend", "elapsed_s": 12.4, "pid": 4242, "stale": True},
            {"worktree": "/wt-2", "hostname": "h", "projects_done": 0, "projects_total": 2,
             "current_project": None, "elapsed_s": 3.0, "pid": 4243, "stale": False},
        ],
        "suites": {"active": 0, "total_cores": 8, "workers_each": 8},
    }
    expected = (
        "/wt-1  collecting baseline 1/3 (current: backend) — 12.4s elapsed — collector (pid 4242) is dead\n"
        "/wt-2  collecting baseline 0/2 (current: -) — 3.0s elapsed\n"
        "suites executing now: 0 — 8 worker(s) each of 8 cores\n"
    )
    assert fleet.render(summary) == expected


def test_fleet_claim_rows_report_collector_liveness(repo):
    proc = subprocess.Popen(["true"])
    proc.wait()
    dead_pid = proc.pid
    live_pid = os.getpid()
    dead_wt = str(repo)
    live_wt = str(repo) + "-wt2"

    hostname = socket.gethostname()
    ledger = Ledger(repo)
    ledger.claim(dead_wt, hostname, dead_pid, projects_total=3)
    ledger.claim(live_wt, hostname, live_pid, projects_total=2)

    out = run_cli(repo, "fleet", "--json")
    rows = {r["worktree"]: (r.get("stale"), r.get("pid")) for r in out["result"]["collecting"]}
    assert rows == {dead_wt: (True, dead_pid), live_wt: (False, live_pid)}
