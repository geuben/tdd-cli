"""Worktree claim during baseline collection (issue #4, foundation for #2).

See tasks/multi-agent-feedback.md Part A.
"""

from __future__ import annotations

import os
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pytest

from conftest import run_cli, write_plan
from tddcli import adapters, gitutil
from tddcli.ledger import Ledger

PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    stub_expected: ["app/calc.py"]
    commit_red: "test: adding two numbers"
    commit_green: "feat: add()"
---

# Plan
"""


def register(repo):
    plan = write_plan(repo, PLAN)
    reg = run_cli(repo, "plan", "register", plan)
    assert reg["ok"], reg
    return plan


def test_second_start_reports_the_active_run_id(repo):
    plan = register(repo)
    first = run_cli(repo, "run", "start", "--plan", plan)
    assert first["ok"], first

    second = run_cli(repo, "run", "start", "--plan", plan)
    assert second["ok"] is False
    assert second["result"]["reason"] == "run_already_active"
    assert second["result"]["run_id"] == 1


def test_successful_start_leaves_no_claim(repo, monkeypatch):
    """The claim is taken before probing and released once the run has started.

    Spies on `adapters.build`, called once per project during the probe loop
    (P6), rather than on the still-stubbed `Ledger.active_claim` — the seam must
    not depend on the method this cycle is implementing.
    """
    plan = register(repo)
    real_build = adapters.build
    seen_claims: list[bool] = []

    def spy(project, worktree):
        led = Ledger(gitutil.repo_identity(worktree))
        rows = led.all(
            "SELECT * FROM baseline_claim WHERE worktree_path = ?", (str(worktree),)
        )
        seen_claims.append(bool(rows))
        return real_build(project, worktree)

    monkeypatch.setattr(adapters, "build", spy)

    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out

    assert any(seen_claims), "claim was never taken"

    led = Ledger(gitutil.repo_identity(repo))
    assert led.all("SELECT * FROM baseline_claim") == []


def test_start_is_rejected_while_a_baseline_is_collecting(repo):
    plan = register(repo)
    led = Ledger(gitutil.repo_identity(repo))
    led.claim(
        str(repo), hostname=socket.gethostname(), pid=os.getpid(), projects_total=1,
    )

    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"] is False
    assert out["result"]["reason"] == "baseline_in_progress"


def test_only_one_of_two_concurrent_starts_wins(repo):
    """P1, reproduced as a test. Assert on returned envelopes only — `run_cli`
    redirects stdout process-globally and threaded output interleaves (P1 caveat).

    Calls `cmd_run_start` directly rather than through `run_cli`: `contextlib.
    redirect_stdout` is itself process-global, and two threads entering/exiting it
    concurrently can hand one thread an empty buffer before either envelope is ever
    inspected — a capture-layer race, not the claim race this test targets. `cwd` is
    set once, outside the thread pool, since both attempts target the same worktree
    and need no per-call `chdir`.
    """
    import os as os_mod

    from tddcli.cli import build_parser, cmd_run_start

    plan = register(repo)
    parser = build_parser()

    def attempt(_):
        args = parser.parse_args(["run", "start", "--plan", plan])
        return cmd_run_start(args).to_dict()

    prev = os_mod.getcwd()
    os_mod.chdir(repo)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, range(2)))
    finally:
        os_mod.chdir(prev)

    oks = [r["ok"] for r in results]
    assert oks.count(True) == 1, results


def test_a_refused_baseline_leaves_no_claim(repo):
    """An R9.5a refusal (every file fails to collect) must not strand the claim —
    otherwise a retry after fixing the environment is itself refused."""
    (repo / "backend" / "tests" / "test_smoke.py").write_text(
        "import module_does_not_exist\n\n"
        "def test_smoke():\n    assert True\n"
    )
    plan = register(repo)

    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"] is False

    led = Ledger(gitutil.repo_identity(repo))
    assert led.all("SELECT * FROM baseline_claim") == []


def test_a_claim_from_a_dead_process_is_reclaimed(repo):
    """A `run start` that was `SIGKILL`ed leaves a claim behind naming a pid that is
    no longer running. Without reclaim, that blocks the worktree forever."""
    proc = subprocess.Popen(["true"])
    proc.wait()
    dead_pid = proc.pid
    with pytest.raises(ProcessLookupError):
        os.kill(dead_pid, 0)

    plan = register(repo)
    led = Ledger(gitutil.repo_identity(repo))
    led.claim(
        str(repo), hostname=socket.gethostname(), pid=dead_pid, projects_total=1,
    )

    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"] is True, out


def test_baseline_in_progress_tells_the_agent_to_poll(repo):
    plan = register(repo)
    led = Ledger(gitutil.repo_identity(repo))
    led.claim(
        str(repo), hostname=socket.gethostname(), pid=os.getpid(), projects_total=1,
    )

    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"] is False
    assert "tdd progress" in out["error"]
    assert "do not re-run" in out["error"]


def test_a_fresh_cross_host_claim_is_not_stale(repo):
    """A pid is meaningless from another host (Decisions); a fresh claim from one
    must not be treated as dead just because it names a foreign hostname."""
    led = Ledger(gitutil.repo_identity(repo))
    led.claim(str(repo), hostname="some-other-host", pid=1, projects_total=1)

    claim = led.active_claim(str(repo))
    assert claim["stale"] is False, claim


def test_an_old_cross_host_claim_is_stale(repo):
    """Past the 60-minute age fallback, a cross-host claim is reclaimed — otherwise
    a crashed agent on another machine bricks the worktree forever."""
    import datetime as _dt

    led = Ledger(gitutil.repo_identity(repo))
    led.claim(str(repo), hostname="some-other-host", pid=1, projects_total=1)
    old = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(minutes=61)).isoformat()
    led.db.execute(
        "UPDATE baseline_claim SET started_at = ? WHERE worktree_path = ?", (old, str(repo)),
    )
    led.db.commit()

    claim = led.active_claim(str(repo))
    assert claim["stale"] is True, claim


def test_a_failed_update_does_not_strand_the_write_lock(repo):
    """`update` must roll back on failure, exactly as `insert` does.

    Python's sqlite3 module does not roll back a failed statement, so the
    connection's implicit transaction stays open and holds SQLite's write lock
    until the connection is garbage collected. `insert` was fixed when the
    concurrent-start race exposed it; `update` has the same hazard on any
    constraint violation, and nothing exercised it.
    """
    import sqlite3

    from tddcli.ledger import now

    led = Ledger(gitutil.repo_identity(repo))
    led.claim(str(repo) + "-a", hostname="h", pid=1, projects_total=1)
    second = led.insert(
        "baseline_claim", worktree_path=str(repo) + "-b",
        hostname="h", pid=2, started_at=now(),
    )

    with pytest.raises(sqlite3.IntegrityError):
        led.update("baseline_claim", second, worktree_path=str(repo) + "-a")

    # A short timeout so a stranded lock fails fast rather than after 30s.
    other = sqlite3.connect(led.path, timeout=0.5)
    try:
        other.execute(
            "INSERT INTO baseline_claim(worktree_path, hostname, pid, started_at)"
            " VALUES (?, 'h', 3, ?)",
            (str(repo) + "-c", now()),
        )
        other.commit()
    finally:
        other.close()
