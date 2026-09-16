from __future__ import annotations

from conftest import run_cli, write_plan

PYTEST_PLAN = """---
cycles:
  - n: 1
    project: backend
    test: "tests/test_add.py::test_add"
    commit_red: "test: add"
    commit_green: "feat: add"
---
"""


def test_resolves_a_pytest_target_to_a_repository_path(repo):
    plan = write_plan(repo, PYTEST_PLAN)
    result = run_cli(repo, "plan", "paths", plan, "--json")["result"]["paths"]
    assert result == [
        {
            "cycle": 1,
            "field": "test",
            "id": "tests/test_add.py::test_add",
            "project": "backend",
            "path": "backend/tests/test_add.py",
        }
    ]
