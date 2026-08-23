import argparse
import os
import socket
import subprocess

import pytest

from conftest import run_cli, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger

TWO_CYCLE_PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "cycle one"
    test: "tests/test_a.py::test_a"
    commit_red: "test: a"
    commit_green: "feat: a"
  - n: 2
    project: backend
    title: "cycle two"
    test: "tests/test_b.py::test_b"
    commit_red: "test: b"
    commit_green: "feat: b"
---
"""


def test_close_cycle_is_idempotent_when_the_row_is_already_closed(repo):
    from tddcli import config as config_mod
    from tddcli.machine import Engine

    plan = write_plan(repo, TWO_CYCLE_PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out

    run_id = out["run"]["id"]
    ledger = Ledger(gitutil.repo_identity(repo))
    run_row = ledger.one("SELECT * FROM run WHERE id = ?", (run_id,))
    cycle_row = ledger.one(
        "SELECT * FROM cycle WHERE run_id = ? ORDER BY id ASC LIMIT 1", (run_id,)
    )
    cfg = config_mod.load(repo)
    engine = Engine(ledger, cfg, repo, run_row)

    engine.close_cycle(cycle_row)

    closed_at_after_first = ledger.one(
        "SELECT closed_at FROM cycle WHERE id = ?", (cycle_row["id"],)
    )["closed_at"]

    engine.close_cycle(cycle_row)

    open_rows = ledger.all(
        "SELECT * FROM cycle WHERE run_id = ? AND closed_at IS NULL", (run_id,)
    )
    assert len(open_rows) == 1

    transitions = ledger.all(
        "SELECT * FROM transition WHERE cycle_id = ? AND to_phase = 'CLOSED'",
        (cycle_row["id"],),
    )
    assert len(transitions) == 1

    ordinal_2_rows = ledger.all(
        "SELECT * FROM cycle WHERE run_id = ? AND ordinal = 2", (run_id,)
    )
    assert len(ordinal_2_rows) == 1

    closed_at_after_second = ledger.one(
        "SELECT closed_at FROM cycle WHERE id = ?", (cycle_row["id"],)
    )["closed_at"]
    assert closed_at_after_second == closed_at_after_first


def test_open_cycle_returns_the_existing_open_row_for_an_ordinal(repo):
    from tddcli import config as config_mod
    from tddcli.machine import Engine

    plan = write_plan(repo, TWO_CYCLE_PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out

    run_id = out["run"]["id"]
    ledger = Ledger(gitutil.repo_identity(repo))
    run_row = ledger.one("SELECT * FROM run WHERE id = ?", (run_id,))
    cfg = config_mod.load(repo)
    engine = Engine(ledger, cfg, repo, run_row)

    a = engine.open_cycle(2)
    b = engine.open_cycle(2)

    assert a["id"] == b["id"]

    ordinal_2_rows = ledger.all(
        "SELECT * FROM cycle WHERE run_id = ? AND ordinal = 2", (run_id,)
    )
    assert len(ordinal_2_rows) == 1


def test_advance_is_rejected_while_another_advance_is_in_flight(repo):
    plan = write_plan(repo, TWO_CYCLE_PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out

    led = Ledger(gitutil.repo_identity(repo))
    led.claim_advance(str(repo), hostname=socket.gethostname(), pid=os.getpid())

    out = run_cli(repo, "advance")
    assert out["ok"] is False
    assert out["result"]["reason"] == "advance_in_flight"


def test_advance_in_flight_directs_the_agent_to_wait(repo):
    plan = write_plan(repo, TWO_CYCLE_PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out

    led = Ledger(gitutil.repo_identity(repo))
    led.claim_advance(str(repo), hostname=socket.gethostname(), pid=os.getpid())

    out = run_cli(repo, "advance")
    assert out["ok"] is False
    assert "do not re-run" in out["error"]
    assert "tdd status" in out["error"]
    assert isinstance(out["result"]["pid"], int)
    assert out["result"]["started_at"] is not None
    assert isinstance(out["result"]["elapsed_s"], int)


def test_a_dead_advance_claim_is_reclaimed(repo):
    proc = subprocess.Popen(["true"])
    proc.wait()
    dead_pid = proc.pid
    with pytest.raises(ProcessLookupError):
        os.kill(dead_pid, 0)

    plan = write_plan(repo, TWO_CYCLE_PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out

    led = Ledger(gitutil.repo_identity(repo))
    led.claim_advance(str(repo), hostname=socket.gethostname(), pid=dead_pid)

    out = run_cli(repo, "advance")
    assert out["ok"] is True, out


def test_advance_releases_its_claim_when_the_handler_raises(repo, monkeypatch):
    from tddcli.cli import cmd_advance

    plan = write_plan(repo, TWO_CYCLE_PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out

    def raiser(*args, **kwargs):
        raise RuntimeError("injected failure")

    monkeypatch.setattr("tddcli.cli.do_advance", raiser)

    prev = os.getcwd()
    os.chdir(repo)
    try:
        with pytest.raises(RuntimeError, match="injected failure"):
            cmd_advance(argparse.Namespace(retry=False))
    finally:
        os.chdir(prev)

    led = Ledger(gitutil.repo_identity(repo))
    rows = led.all("SELECT * FROM advance_claim WHERE worktree_path = ?", (str(repo),))
    assert rows == []
