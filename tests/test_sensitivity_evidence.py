"""Sensitivity evidence line: ledger storage and friction-log rendering (issue #68)."""

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


def _drive_sensitivity(repo):
    """Advance → SENSITIVITY_REQUIRED, then run sensitivity begin/check/end."""
    out = run_cli(repo, "advance")
    assert out["run"]["phase"] == "SENSITIVITY_REQUIRED", out
    run_cli(repo, "sensitivity", "begin")
    (repo / "backend" / "app" / "calc.py").write_text(CALC_MUTATED)
    checked = run_cli(repo, "sensitivity", "check")
    assert checked["ok"], checked
    ended = run_cli(repo, "sensitivity", "end")
    assert ended["result"]["restored_ok"] is True
    return checked


def test_sensitivity_check_records_the_evidence_line(repo):
    _start(repo)
    _drive_sensitivity(repo)
    led = Ledger(gitutil.repo_identity(repo))
    row = led.one("SELECT evidence_line FROM sensitivity_check ORDER BY id DESC LIMIT 1")
    assert row is not None
    assert row["evidence_line"].startswith("assert")
