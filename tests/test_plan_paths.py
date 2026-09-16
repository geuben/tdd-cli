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

MODIFIES_TESTS_PLAN = """---
cycles:
  - n: 1
    project: backend
    test: "tests/test_add.py::test_add"
    modifies_tests:
      - "tests/test_helper.py::test_helper"
    commit_red: "test: add"
    commit_green: "feat: add"
---
"""


def test_resolves_modifies_tests_ids_labelled_with_their_field(repo):
    plan = write_plan(repo, MODIFIES_TESTS_PLAN)
    result = run_cli(repo, "plan", "paths", plan, "--json")["result"]["paths"]
    modifies = [r for r in result if r["field"] == "modifies_tests"]
    assert modifies == [
        {
            "cycle": 1,
            "field": "modifies_tests",
            "id": "tests/test_helper.py::test_helper",
            "project": "backend",
            "path": "backend/tests/test_helper.py",
        }
    ]


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
