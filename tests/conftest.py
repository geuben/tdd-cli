from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True
    ).stdout


@pytest.fixture
def ledger_home(tmp_path, monkeypatch):
    home = tmp_path / "ledger-home"
    home.mkdir()
    monkeypatch.setenv("TDD_LEDGER_HOME", str(home))
    return home


@pytest.fixture
def repo(tmp_path, ledger_home):
    """A git repo with one Python project, wired for the pytest adapter."""
    root = tmp_path / "workspace"
    (root / "backend" / "tests").mkdir(parents=True)
    (root / "backend" / "app").mkdir(parents=True)

    (root / "tdd.toml").write_text(
        '[project.backend]\n'
        'root       = "backend"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "lint       = []\n"
        "typecheck  = []\n"
    )
    (root / "backend" / "app" / "__init__.py").write_text("")
    (root / "backend" / "tests" / "test_smoke.py").write_text(
        "def test_smoke():\n    assert True\n"
    )
    (root / "backend" / "conftest.py").write_text(
        "import sys, pathlib\n"
        "sys.path.insert(0, str(pathlib.Path(__file__).parent))\n"
    )

    git(root.parent, "init", "-q", str(root)) if False else None
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    git(root, "config", "user.email", "test@example.com")
    git(root, "config", "user.name", "Test")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "initial")
    return root


def write_plan(repo: Path, body: str, name: str = "tasks/plan.md") -> str:
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"plan: {name}")
    return name


def run_cli(repo: Path, *argv: str) -> dict:
    """Invoke the CLI in-process with cwd set to the repo."""
    import json
    import io
    import contextlib

    from tddcli.cli import main

    prev = os.getcwd()
    os.chdir(repo)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            main(list(argv))
    finally:
        os.chdir(prev)
    return json.loads(buf.getvalue())
