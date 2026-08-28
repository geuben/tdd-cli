"""Tests for target lint: grammar and root-prefix validation at plan register / run start."""
from __future__ import annotations

from conftest import run_cli, write_plan

_PLAN_NO_SEP = """---
cycles:
  - n: 1
    project: backend
    title: "register refuses a pytest target without the :: separator"
    test: "tests/test_add.py"
    files: []
---
"""


def test_register_refuses_a_pytest_target_without_separator(repo):
    plan = write_plan(repo, _PLAN_NO_SEP)
    out = run_cli(repo, "plan", "register", plan)
    assert out["ok"] is False
    assert out["result"]["reason"] == "target_lint"
    findings = out["result"]["findings"]
    assert len(findings) == 1
    assert findings[0]["cycle"] == 1
    assert "::" in findings[0]["problem"]
