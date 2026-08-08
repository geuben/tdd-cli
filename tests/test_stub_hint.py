"""The create_stub directive must speak the target project's language.

Found in review: the directive hardcoded `raise NotImplementedError` — Python
advice served verbatim to vitest projects. The idiom belongs to the adapter.
"""

from __future__ import annotations

from conftest import run_cli, write_plan
from tddcli import config as config_mod
from tddcli.adapters.pytest_adapter import PytestAdapter
from tddcli.adapters.vitest_adapter import VitestAdapter

TOML = """
[project.backend]
root       = "backend"
adapter    = "pytest"
test_paths = ["tests/"]

[project.frontend]
root       = "frontend"
adapter    = "vitest"
test_paths = ["**/*.test.ts"]
"""


def _projects(tmp_path):
    (tmp_path / "tdd.toml").write_text(TOML)
    (tmp_path / "backend").mkdir()
    (tmp_path / "frontend").mkdir()
    return config_mod.load(tmp_path)


def test_pytest_stub_idiom_is_raise_not_implemented(tmp_path):
    cfg = _projects(tmp_path)
    hint = PytestAdapter(cfg.project("backend"), tmp_path).stub_hint()
    assert "raise NotImplementedError" in hint


def test_vitest_stub_idiom_is_throw_not_python(tmp_path):
    cfg = _projects(tmp_path)
    hint = VitestAdapter(cfg.project("frontend"), tmp_path).stub_hint()
    assert "throw new Error" in hint
    assert "NotImplementedError" not in hint


PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    stub_expected: ["app/calc.py"]
---

# Plan
"""

TEST_ADD = """from app.calc import add


def test_add_two_numbers():
    assert add(2, 3) == 5
"""


def test_create_stub_detail_uses_the_target_projects_adapter(repo, monkeypatch):
    """The directive's idiom must come from stub_hint() of the adapter that owns
    the uncollectable target — not from a string baked into advance.py."""
    from tddcli import adapters

    real_build = adapters.build

    def build_with_sentinel(project, worktree):
        adapter = real_build(project, worktree)
        monkeypatch.setattr(
            type(adapter), "stub_hint", lambda self: "SENTINEL_STUB_IDIOM",
            raising=False,
        )
        return adapter

    monkeypatch.setattr(adapters, "build", build_with_sentinel)

    plan = write_plan(repo, PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)

    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "create_stub"
    assert "SENTINEL_STUB_IDIOM" in out["next_action"]["detail"]


def test_create_stub_detail_speaks_python_for_a_pytest_project(repo):
    plan = write_plan(repo, PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)

    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "create_stub"
    assert "raise NotImplementedError" in out["next_action"]["detail"]
