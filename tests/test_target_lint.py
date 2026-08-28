"""Tests for target lint: grammar and root-prefix validation at plan register / run start."""
from __future__ import annotations

from pathlib import Path

from conftest import run_cli, write_plan
from tddcli import config as config_mod
from tddcli.adapters.vitest_adapter import VitestAdapter

_VITEST_TOML = """
[project.frontend]
root       = "frontend"
adapter    = "vitest"
test_paths = ["**/*.test.ts"]
"""


def vitest_adapter_for(tmp_path: Path) -> VitestAdapter:
    (tmp_path / "tdd.toml").write_text(_VITEST_TOML)
    (tmp_path / "frontend").mkdir()
    cfg = config_mod.load(tmp_path)
    return VitestAdapter(cfg.project("frontend"), tmp_path)

_PLAN_NO_SEP = """---
cycles:
  - n: 1
    project: backend
    title: "register refuses a pytest target without the :: separator"
    test: "tests/test_add.py"
    files: []
---
"""


def test_vitest_target_without_describe_separator_is_flagged(tmp_path):
    adapter = vitest_adapter_for(tmp_path)
    msg = adapter.lint_target_id("a.test.ts::does a thing")
    assert msg
    assert " > " in msg


def test_register_refuses_a_pytest_target_without_separator(repo):
    plan = write_plan(repo, _PLAN_NO_SEP)
    out = run_cli(repo, "plan", "register", plan)
    assert out["ok"] is False
    assert out["result"]["reason"] == "target_lint"
    findings = out["result"]["findings"]
    assert len(findings) == 1
    assert findings[0]["cycle"] == 1
    assert "::" in findings[0]["problem"]
