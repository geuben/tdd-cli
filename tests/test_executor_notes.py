"""Executor-narrative channel: tdd note command and rendering (issue #77)."""

from __future__ import annotations

from conftest import git, run_cli, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger

PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    commit_red: "test: add"
    commit_green: "feat: add()"
---

# Plan
"""

TEST_ADD = """from app.calc import add


def test_add_two_numbers():
    assert add(2, 3) == 5
"""

CALC_WORKING = "def add(a, b):\n    return a + b\n"
CALC_MUTATED = "def add(a, b):\n    return 0\n"


def _start(repo):
    (repo / "backend" / "app" / "calc.py").write_text(CALC_WORKING)
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "add calc.py and test")
    plan = write_plan(repo, PLAN)
    reg = run_cli(repo, "plan", "register", plan)
    assert reg["ok"], reg
    started = run_cli(repo, "run", "start", "--plan", plan)
    assert started["ok"], started
    return started


def test_note_attaches_to_the_open_cycle_with_its_phase(repo):
    started = _start(repo)
    run_id = started["run"]["id"]

    out = run_cli(repo, "note", "the fixture assumption was wrong")
    assert out["ok"], out

    led = Ledger(gitutil.repo_identity(repo))
    rows = led.all("SELECT * FROM note ORDER BY id")
    assert len(rows) == 1
    row = rows[0]
    assert row["run_id"] == run_id
    assert row["cycle_id"] is not None
    assert row["phase"] == "AWAITING_TEST"
    assert row["text"] == "the fixture assumption was wrong"
