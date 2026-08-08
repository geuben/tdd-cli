"""Single-project repos: `root = "."` (§7.1).

Most repositories are one project with `tests/` at the top level, not a monorepo
of subdirectory roots. `Project.owns` matched roots only by `<root>/` prefix, so a
root of "." owned nothing: every changed file classified as outside the project,
and `tdd init` never proposed the repository root as a project at all.
"""

from __future__ import annotations

import subprocess

import pytest

from conftest import git, run_cli, write_plan
from tddcli import config as config_mod

TOML = """
[project.app]
root       = "."
adapter    = "pytest"
test_paths = ["tests/"]
lint       = []
typecheck  = []
"""

PLAN = """---
cycles:
  - n: 1
    project: app
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    stub_expected: ["app/calc.py"]
---
"""

TEST_ADD = """from app.calc import add


def test_add_two_numbers():
    assert add(2, 3) == 5
"""


@pytest.fixture
def flat_repo(tmp_path, ledger_home):
    """A git repo whose only project is the repository root itself."""
    root = tmp_path / "workspace"
    (root / "tests").mkdir(parents=True)
    (root / "app").mkdir()
    (root / "tdd.toml").write_text(TOML)
    (root / "app" / "__init__.py").write_text("")
    (root / "tests" / "test_smoke.py").write_text("def test_smoke():\n    assert True\n")
    (root / "conftest.py").write_text(
        "import sys, pathlib\n"
        "sys.path.insert(0, str(pathlib.Path(__file__).parent))\n"
    )
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    git(root, "config", "user.email", "test@example.com")
    git(root, "config", "user.name", "Test")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "initial")
    return root


def test_a_root_project_owns_top_level_paths(flat_repo):
    cfg = config_mod.load(flat_repo)
    app = cfg.project("app")
    assert app.owns("tests/test_add.py")
    assert app.owns("app/calc.py")
    assert app.relative_to_root("tests/test_add.py") == "tests/test_add.py"
    assert app.is_test_file("tests/test_add.py")
    assert not app.is_test_file("app/calc.py")


def test_a_nested_root_still_wins_over_the_repo_root(tmp_path):
    (tmp_path / "tdd.toml").write_text(
        TOML + '\n[project.backend]\nroot = "backend"\nadapter = "pytest"\n'
        'test_paths = ["tests/"]\n'
    )
    cfg = config_mod.load(tmp_path)
    assert cfg.owning_project("backend/app/x.py").name == "backend"
    assert cfg.owning_project("app/x.py").name == "app"


def test_full_cycle_in_a_single_project_repo(flat_repo):
    plan = write_plan(flat_repo, PLAN)
    assert run_cli(flat_repo, "plan", "register", plan)["ok"]
    assert run_cli(flat_repo, "run", "start", "--plan", plan)["ok"]

    (flat_repo / "tests" / "test_add.py").write_text(TEST_ADD)
    (flat_repo / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    red = run_cli(flat_repo, "advance")
    assert red["run"]["phase"] == "AWAITING_IMPL", red
    assert set(red["result"]["staged"]) == {"tests/test_add.py", "app/calc.py"}

    (flat_repo / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    green = run_cli(flat_repo, "advance")
    assert green["run"]["phase"] == "AWAITING_REFACTOR", green

    closed = run_cli(flat_repo, "advance")
    assert closed["next_action"]["verb"] == "complete", closed


def test_init_proposes_the_repo_root_as_a_project(tmp_path, ledger_home):
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname = 'workspace'\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True)

    out = run_cli(root, "init")
    assert out["ok"], out
    body = (root / "tdd.toml").read_text()
    assert 'root       = "."' in body
    assert 'adapter    = "pytest"' in body
