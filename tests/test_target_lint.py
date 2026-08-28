"""Tests for target lint: grammar and root-prefix validation at plan register / run start."""
from __future__ import annotations

from pathlib import Path

from conftest import run_cli, write_plan
from tddcli import config as config_mod
from tddcli.adapters.gradle_adapter import GradleAdapter
from tddcli.adapters.vitest_adapter import VitestAdapter
from tddcli.adapters.xctest_adapter import XCTestAdapter

_VITEST_TOML = """
[project.frontend]
root       = "frontend"
adapter    = "vitest"
test_paths = ["**/*.test.ts"]
"""

_GRADLE_TOML = """
[project.app]
root         = "app"
adapter      = "gradle"
test_paths   = ["src/test/"]
test_command = "./gradlew test"
"""

_XCTEST_TOML = """
[project.ios]
root         = "ios"
adapter      = "xctest"
test_paths   = ["AppTests/"]
test_command = "xcodebuild test -scheme AppTests"
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


def xctest_adapter_for(tmp_path: Path) -> XCTestAdapter:
    (tmp_path / "tdd.toml").write_text(_XCTEST_TOML)
    (tmp_path / "ios" / "AppTests").mkdir(parents=True)
    cfg = config_mod.load(tmp_path)
    return XCTestAdapter(cfg.project("ios"), tmp_path)


def gradle_adapter_for(tmp_path: Path) -> GradleAdapter:
    (tmp_path / "tdd.toml").write_text(_GRADLE_TOML)
    (tmp_path / "app" / "src" / "test").mkdir(parents=True)
    cfg = config_mod.load(tmp_path)
    return GradleAdapter(cfg.project("app"), tmp_path)


def test_xctest_target_without_three_parts_is_flagged(tmp_path):
    adapter = xctest_adapter_for(tmp_path)
    msg = adapter.lint_target_id("AppTests.RecTests.testStopsRecording")
    assert msg
    assert "Bundle/Class" in msg


def test_gradle_target_without_slash_is_flagged(tmp_path):
    adapter = gradle_adapter_for(tmp_path)
    msg = adapter.lint_target_id("com.foo.BarTest.testBaz")
    assert msg
    assert "/" in msg


def test_vitest_target_without_describe_separator_is_flagged(tmp_path):
    adapter = vitest_adapter_for(tmp_path)
    msg = adapter.lint_target_id("a.test.ts::does a thing")
    assert msg
    assert " > " in msg


def test_register_accepts_a_genuinely_nested_root_path(repo):
    (repo / "tdd.toml").write_text(
        "[project.proj]\n"
        'root       = "backend"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "lint       = []\n"
        "typecheck  = []\n"
    )
    (repo / "backend" / "backend" / "tests").mkdir(parents=True)
    (repo / "backend" / "backend" / "tests" / "test_add.py").write_text("def test_add(): pass\n")
    import subprocess
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "nested root"], check=True)
    plan = write_plan(
        repo,
        "---\ncycles:\n  - n: 1\n    project: proj\n    test: \"backend/tests/test_add.py::test_add\"\n    files: []\n---\n",
    )
    out = run_cli(repo, "plan", "register", plan)
    assert out["ok"] is True


def test_register_refuses_a_root_duplicated_pytest_target(repo):
    (repo / "tdd.toml").write_text(
        "[project.proj]\n"
        'root       = "backend"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "lint       = []\n"
        "typecheck  = []\n"
    )
    import subprocess
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "swap project name"], check=True)
    plan = write_plan(
        repo,
        "---\ncycles:\n  - n: 1\n    project: proj\n    test: \"backend/tests/test_add.py::test_add\"\n    files: []\n---\n",
    )
    out = run_cli(repo, "plan", "register", plan)
    assert out["ok"] is False
    assert out["result"]["reason"] == "target_lint"
    findings = out["result"]["findings"]
    assert len(findings) == 1
    assert findings[0]["suggestion"] == "tests/test_add.py::test_add"


def test_register_refuses_a_pytest_target_without_separator(repo):
    plan = write_plan(repo, _PLAN_NO_SEP)
    out = run_cli(repo, "plan", "register", plan)
    assert out["ok"] is False
    assert out["result"]["reason"] == "target_lint"
    findings = out["result"]["findings"]
    assert len(findings) == 1
    assert findings[0]["cycle"] == 1
    assert "::" in findings[0]["problem"]
