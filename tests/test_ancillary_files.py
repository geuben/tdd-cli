"""Tests for plan-level ancillary_files support (issue #70)."""

from __future__ import annotations

import json

import pytest

from conftest import run_cli, write_plan


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

    ledger = Ledger(gitutil.repo_identity(repo))
    row = ledger.one(
        "SELECT ancillary_files FROM plan_contract ORDER BY id DESC LIMIT 1"
    )
    assert json.loads(row["ancillary_files"]) == ["notes.md"]
