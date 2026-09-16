from __future__ import annotations

from conftest import run_cli, write_plan
from tddcli import config as config_mod
from tddcli import contract as contract_mod
from tddcli import plan_paths as plan_paths_mod

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


def _make_cfg(tmp_path, toml: str):
    (tmp_path / "tdd.toml").write_text(toml)
    return config_mod.load(tmp_path)


def _resolve(tmp_path, toml: str, plan_text: str):
    cfg = _make_cfg(tmp_path, toml)
    c = contract_mod.parse(plan_text, "tasks/p.md", cfg)
    return plan_paths_mod.resolve(c, cfg, tmp_path)


_CARGO_TOML = (
    "[project.dd-bridge]\n"
    'root       = "crates/dd-bridge"\n'
    'adapter    = "cargo"\n'
    'test_paths = ["tests/"]\n'
)


def test_a_cargo_lib_id_is_unresolved_with_no_path_in_id(tmp_path):
    plan_text = (
        "---\ncycles:\n"
        "  - n: 1\n    project: dd-bridge\n    refactor_cycle: true\n"
        "    modifies_tests:\n      - \"lib::inner::tests::unit_thing\"\n"
        "    commit_refactor: x\n---\n"
    )
    result = _resolve(tmp_path, _CARGO_TOML, plan_text)
    assert result["unresolved"] == [
        {
            "cycle": 1,
            "field": "modifies_tests",
            "id": "lib::inner::tests::unit_thing",
            "project": "dd-bridge",
            "reason": "no_path_in_id",
        }
    ]


def test_a_root_project_yields_an_unprefixed_path(tmp_path):
    toml = (
        "[project.flat]\n"
        'root       = "."\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
    )
    plan_text = (
        "---\ncycles:\n"
        "  - n: 1\n    project: flat\n    test: \"tests/test_add.py::test_add\"\n"
        "    commit_red: x\n    commit_green: x\n---\n"
    )
    result = _resolve(tmp_path, toml, plan_text)
    assert result["paths"][0]["path"] == "tests/test_add.py"


def test_every_qualification_form_resolves_to_the_same_path(repo):
    forms = [
        "tests/test_add.py::test_add",
        "backend/tests/test_add.py::test_add",
        "backend::tests/test_add.py::test_add",
    ]
    results = []
    for form in forms:
        plan_text = (
            "---\ncycles:\n"
            f"  - n: 1\n    project: backend\n    test: \"{form}\"\n"
            "    commit_red: x\n    commit_green: x\n---\n"
        )
        plan = write_plan(repo, plan_text, f"tasks/plan_{len(results)}.md")
        paths = run_cli(repo, "plan", "paths", plan, "--json")["result"]["paths"]
        results.append((paths[0]["project"], paths[0]["path"]))
    assert results[0] == results[1] == results[2]


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
