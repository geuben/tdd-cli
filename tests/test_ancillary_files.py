"""Tests for plan-level ancillary_files support (issue #70)."""

from __future__ import annotations

from conftest import git, run_cli, write_plan

PLAN_WITH_ANCILLARY = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    commit_red: "test: adding two numbers"
    commit_green: "feat: add()"
ancillary_files:
  - notes.md
---

# Plan
"""


def test_plan_register_persists_ancillary_files(repo, ledger_home):
    from tddcli import gitutil
    from tddcli.ledger import Ledger

    plan_rel = write_plan(repo, PLAN_WITH_ANCILLARY, name="tasks/plan.md")
    result = run_cli(repo, "plan", "register", plan_rel)
    assert result["ok"] is True

    import json

    ledger = Ledger(gitutil.repo_identity(repo))
    row = ledger.one(
        "SELECT ancillary_files FROM plan_contract ORDER BY id DESC LIMIT 1"
    )
    assert json.loads(row["ancillary_files"]) == ["notes.md"]


TEST_ADD = """from app.calc import add


def test_add_two_numbers():
    assert add(2, 3) == 5
"""


def test_declared_ancillary_file_is_committed_and_not_flagged(repo, ledger_home):
    plan_rel = write_plan(repo, PLAN_WITH_ANCILLARY, name="tasks/plan.md")
    assert run_cli(repo, "plan", "register", plan_rel)["ok"]
    assert run_cli(repo, "run", "start", "--plan", plan_rel)["ok"]

    # Write ancillary file at repo root (outside 'backend' project root)
    (repo / "notes.md").write_text("ancillary notes\n")

    # Drive RED: write test + stub
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    run_cli(repo, "advance")  # RED → AWAITING_IMPL

    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    run_cli(repo, "advance")  # GREEN → AWAITING_REFACTOR
    run_cli(repo, "advance")  # REFACTOR → complete

    events = run_cli(repo, "metrics")["result"]["runs"][0]["integrity_events"]
    assert events.get("undeclared_file_touched", 0) == 0

    # notes.md must be tracked at HEAD
    tracked = git(repo, "ls-files", "notes.md").strip()
    assert tracked == "notes.md"
