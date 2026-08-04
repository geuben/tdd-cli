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


@pytest.fixture
def repo_multi(repo, ledger_home):
    """`repo` plus an empty vitest `frontend` (a `package.json`, no test files).

    P5 proved this starts a run cleanly: `run start` reports `baselines: {backend: 0,
    frontend: 0}`. Used by cycles 9 and 18.
    """
    (repo / "frontend").mkdir()
    (repo / "frontend" / "package.json").write_text('{"name": "frontend", "version": "1.0.0"}\n')
    (repo / "tdd.toml").write_text(
        '[project.backend]\n'
        'root       = "backend"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "lint       = []\n"
        "typecheck  = []\n"
        "\n"
        "[project.frontend]\n"
        'root       = "frontend"\n'
        'adapter    = "vitest"\n'
        'test_paths = ["**/*.test.ts", "**/*.test.tsx"]\n'
        "lint       = []\n"
        "typecheck  = []\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "add empty vitest frontend")
    return repo


@pytest.fixture
def repo_broken(repo, ledger_home):
    """`repo` plus a second pytest project `verify` that cannot collect.

    Mirrors the real `pyyaml` incident. P4 proved `run start` refuses this project —
    so it must only be used by doctor cycles (15-17), which need no run.
    """
    (repo / "verify" / "tests").mkdir(parents=True)
    (repo / "verify" / "tests" / "test_v.py").write_text(
        "import yaml_does_not_exist\n\n"
        "def test_v():\n    assert True\n"
    )
    (repo / "tdd.toml").write_text(
        '[project.backend]\n'
        'root       = "backend"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "lint       = []\n"
        "typecheck  = []\n"
        "\n"
        "[project.verify]\n"
        'root       = "verify"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "lint       = []\n"
        "typecheck  = []\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "add broken verify project")
    return repo


def write_plan(repo: Path, body: str, name: str = "tasks/plan.md") -> str:
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"plan: {name}")
    return name


def run_cli_text(repo: Path, *argv: str) -> str:
    """Invoke the CLI in-process, returning raw stdout."""
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
    return buf.getvalue()


def run_cli(repo: Path, *argv: str) -> dict:
    """Invoke the CLI and parse its JSON envelope."""
    import json

    return json.loads(run_cli_text(repo, *argv))
