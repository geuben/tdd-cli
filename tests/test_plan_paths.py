from __future__ import annotations

import subprocess
from pathlib import Path

from conftest import git, run_cli, write_plan
from tddcli import config as config_mod
from tddcli import contract as contract_mod
from tddcli import plan_paths as plan_paths_mod
from tddcli.adapters.gradle_adapter import GradleAdapter
from tddcli.adapters.xctest_adapter import XCTestAdapter

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


def _gradle_adapter_for(tmp_path: Path, extra_files=()) -> GradleAdapter:
    (tmp_path / "tdd.toml").write_text(_GRADLE_TOML)
    (tmp_path / "app" / "src" / "test").mkdir(parents=True)
    for rel, text in extra_files:
        p = tmp_path / "app" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    cfg = config_mod.load(tmp_path)
    return GradleAdapter(cfg.project("app"), tmp_path)


_BAR_TEST_KT = """\
package com.example.feature

import org.junit.Test

class BarTest {
    @Test
    fun rejectsAnEmptyName() {}
}
"""


def test_gradle_scans_sources_to_map_an_id_to_its_file(tmp_path):
    adapter = _gradle_adapter_for(
        tmp_path,
        [("src/test/kotlin/com/example/feature/BarTest.kt", _BAR_TEST_KT)],
    )
    result = adapter.scan_target_paths()
    assert result == {
        "com.example.feature.BarTest/rejectsAnEmptyName": "src/test/kotlin/com/example/feature/BarTest.kt"
    }


def _xctest_adapter_for(tmp_path: Path, extra_files=()) -> XCTestAdapter:
    (tmp_path / "tdd.toml").write_text(_XCTEST_TOML)
    (tmp_path / "ios" / "AppTests").mkdir(parents=True)
    for rel, text in extra_files:
        p = tmp_path / "ios" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    cfg = config_mod.load(tmp_path)
    return XCTestAdapter(cfg.project("ios"), tmp_path)


_REC_TESTS_SWIFT = """\
import XCTest

class RecTests: XCTestCase {
    func testStopsRecording() {}
}
"""


def test_xctest_scans_sources_to_map_an_id_to_its_file(tmp_path):
    adapter = _xctest_adapter_for(
        tmp_path,
        [("AppTests/RecTests.swift", _REC_TESTS_SWIFT)],
    )
    result = adapter.scan_target_paths()
    assert result == {"AppTests/RecTests/testStopsRecording": "AppTests/RecTests.swift"}


def test_a_gradle_id_resolves_through_the_source_scan(tmp_path):
    (tmp_path / "tdd.toml").write_text(_GRADLE_TOML)
    (tmp_path / "app" / "src" / "test" / "kotlin" / "com" / "example" / "feature").mkdir(
        parents=True
    )
    (tmp_path / "app" / "src" / "test" / "kotlin" / "com" / "example" / "feature" / "BarTest.kt").write_text(
        _BAR_TEST_KT
    )
    plan_text = (
        "---\ncycles:\n"
        "  - n: 1\n    project: app\n    refactor_cycle: true\n"
        "    modifies_tests:\n"
        "      - \"com.example.feature.BarTest/rejectsAnEmptyName\"\n"
        "    commit_refactor: x\n---\n"
    )
    cfg = config_mod.load(tmp_path)
    c = contract_mod.parse(plan_text, "tasks/p.md", cfg)
    result = plan_paths_mod.resolve(c, cfg, tmp_path)
    assert result["paths"][0]["path"] == "app/src/test/kotlin/com/example/feature/BarTest.kt"


def _make_cfg(tmp_path, toml: str):
    (tmp_path / "tdd.toml").write_text(toml)
    return config_mod.load(tmp_path)


def _resolve(tmp_path, toml: str, plan_text: str):
    cfg = _make_cfg(tmp_path, toml)
    c = contract_mod.parse(plan_text, "tasks/p.md", cfg)
    return plan_paths_mod.resolve(c, cfg, tmp_path)


_GRADLE_TOML = (
    "[project.app]\n"
    'root       = "app"\n'
    'adapter    = "gradle"\n'
    'test_paths = ["src/test/"]\n'
    'test_command = "./gradlew test"\n'
)

_XCTEST_TOML = (
    "[project.ios]\n"
    'root       = "ios"\n'
    'adapter    = "xctest"\n'
    'test_paths = ["AppTests/"]\n'
    'test_command = "xcodebuild test -scheme AppTests"\n'
)

_CARGO_TOML = (
    "[project.dd-bridge]\n"
    'root       = "crates/dd-bridge"\n'
    'adapter    = "cargo"\n'
    'test_paths = ["tests/"]\n'
)


def _make_cargo_repo(tmp_path):
    root = tmp_path / "workspace"
    (root / "crates" / "dd-bridge").mkdir(parents=True)
    (root / "tdd.toml").write_text(_CARGO_TOML)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    git(root, "config", "user.email", "test@example.com")
    git(root, "config", "user.name", "Test")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "initial")
    return root


def test_a_refactor_cycles_modifies_tests_are_resolved(tmp_path):
    plan_text = (
        "---\ncycles:\n"
        "  - n: 1\n    project: dd-bridge\n    refactor_cycle: true\n"
        "    modifies_tests:\n"
        "      - \"adapter_host_catalog::host_catalog_lists_each_running\"\n"
        "    commit_refactor: x\n"
        "  - n: 2\n    project: dd-bridge\n    refactor_cycle: true\n"
        "    modifies_tests:\n"
        "      - \"other_file::some_test\"\n"
        "    commit_refactor: x\n---\n"
    )
    result = _resolve(tmp_path, _CARGO_TOML, plan_text)
    cycle2_paths = [r for r in result["paths"] if r["cycle"] == 2]
    assert len(cycle2_paths) == 1
    assert cycle2_paths[0]["path"] == "crates/dd-bridge/tests/other_file.rs"


def test_a_cargo_integration_test_id_resolves_under_the_project_root(tmp_path):
    plan_text = (
        "---\ncycles:\n"
        "  - n: 1\n    project: dd-bridge\n    refactor_cycle: true\n"
        "    modifies_tests:\n"
        "      - \"adapter_host_catalog::host_catalog_lists_each_running\"\n"
        "    commit_refactor: x\n---\n"
    )
    result = _resolve(tmp_path, _CARGO_TOML, plan_text)
    assert result["paths"][0]["path"] == "crates/dd-bridge/tests/adapter_host_catalog.rs"


def test_unresolved_ids_do_not_fail_the_command(tmp_path, ledger_home):
    repo = _make_cargo_repo(tmp_path)
    plan_text = (
        "---\ncycles:\n"
        "  - n: 1\n    project: dd-bridge\n    refactor_cycle: true\n"
        "    modifies_tests:\n      - \"lib::inner::tests::unit_thing\"\n"
        "    commit_refactor: x\n---\n"
    )
    plan = write_plan(repo, plan_text)
    result = run_cli(repo, "plan", "paths", plan, "--json")
    assert result["ok"] is True


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
