"""A project declares the command the tool runs (R7.12).

Without this the tool runs its adapter's default invocation, which can differ from
what the project actually runs. The motivating repo's suite is
`pytest tests/ -v -n auto` — parallel via xdist — while the adapter's default was
serial. That is both far slower and not the same suite the team trusts.
"""

from __future__ import annotations

from pathlib import Path

from tddcli import adapters
from tddcli import config as config_mod

from conftest import git, run_cli, write_plan

PLAN = """---
cycles:
  - n: 1
    project: backend
    test: "tests/test_add.py::test_add"
    stub_expected: ["app/calc.py"]
---
"""


def project_with(tmp_path: Path, extra: str):
    (tmp_path / "tdd.toml").write_text(
        '[project.backend]\n'
        'root       = "backend"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n' + extra
    )
    return config_mod.load(tmp_path).project("backend")


def test_declared_test_command_is_used_verbatim(tmp_path):
    project = project_with(tmp_path, 'test_command = "uv run pytest tests/ -n auto"\n')
    adapter = adapters.build(project, tmp_path)
    assert adapter._test_cmd() == "uv run pytest tests/ -n auto"


def test_only_reporting_flags_are_appended(tmp_path, monkeypatch):
    project = project_with(tmp_path, 'test_command = "uv run pytest tests/ -v -n auto"\n')
    adapter = adapters.build(project, tmp_path)
    seen = {}

    def fake_run(command, cwd, timeout=1800):
        seen["command"] = command
        return 1, "", "no report"

    monkeypatch.setattr(adapters.pytest_adapter, "run_command", fake_run)
    adapter.run("backend::tests/a.py::test_x")

    assert seen["command"].startswith("uv run pytest tests/ -v -n auto ")
    assert "--json-report" in seen["command"]
    # Nothing that would change which tests run or how.
    for flag in ("-q", "-p ", "-k ", "-m "):
        assert flag not in seen["command"].replace("uv run pytest tests/ -v -n auto", "")


def test_collect_command_is_separate_so_collection_is_not_parallelised(tmp_path):
    project = project_with(
        tmp_path,
        'test_command    = "uv run pytest tests/ -n auto"\n'
        'collect_command = "uv run pytest"\n',
    )
    adapter = adapters.build(project, tmp_path)
    assert "-n auto" not in adapter._collect_cmd()


def test_defaults_are_unchanged_when_nothing_is_declared(tmp_path):
    project = project_with(tmp_path, "")
    adapter = adapters.build(project, tmp_path)
    assert adapter._test_cmd() == adapter._base_cmd()
    assert adapter._collect_cmd() == adapter._base_cmd()


def test_a_declared_command_drives_a_real_cycle(repo):
    """End-to-end with an explicit command, proving the wiring is live."""
    (repo / "tdd.toml").write_text(
        '[project.backend]\n'
        'root         = "backend"\n'
        'adapter      = "pytest"\n'
        'test_paths   = ["tests/"]\n'
        'test_command = "pytest tests/ -v"\n'
        "lint         = []\n"
        "typecheck    = []\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "declare the suite command")

    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]

    (repo / "backend" / "tests" / "test_add.py").write_text(
        "from app.calc import add\n\n\ndef test_add():\n    assert add(1, 1) == 2\n"
    )
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    red = run_cli(repo, "advance")
    assert red["next_action"]["verb"] == "write_implementation", red
