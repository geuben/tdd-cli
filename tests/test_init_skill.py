"""`tdd init --skill`: the driving skill and hooks, from the copies installed with the binary."""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml

from conftest import run_cli
from tddcli import contract, docs
from tddcli.envelope import ENVELOPE_VERSION, VERB_SET_VERSION

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = ".claude/skills/tdd-drive/SKILL.md"
STOP_HOOK = ".claude/hooks/tdd_stop_hook.py"
BASH_HOOK = ".claude/hooks/tdd_bash_hook.py"


@pytest.fixture
def bare_repo(tmp_path, ledger_home):
    root = tmp_path / "workspace"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    return root


@pytest.fixture
def packaged(tmp_path, monkeypatch):
    """A fake installed `_docs`: what init must copy from, not the checkout."""
    files = {
        "examples/skills/tdd-drive/SKILL.md": "packaged skill\n",
        "examples/claude-code-hooks/stop_hook.py": "packaged stop\n",
        "examples/claude-code-hooks/bash_hook.py": "packaged bash\n",
    }
    root = tmp_path / "_docs"
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    monkeypatch.setattr(docs, "_PACKAGED", root)
    return files


def read(repo: Path, rel: str) -> str | None:
    path = repo / rel
    return path.read_text() if path.is_file() else None


def test_the_shipped_skill_declares_the_versions_this_binary_emits():
    text = (REPO_ROOT / "examples/skills/tdd-drive/SKILL.md").read_text()
    front = yaml.safe_load(contract.split_front_matter(text))
    assert front.get("metadata") == {
        "verb_set_version": str(VERB_SET_VERSION),
        "envelope_version": str(ENVELOPE_VERSION),
    }


def test_init_skill_writes_the_installed_driving_skill(bare_repo, packaged):
    run_cli(bare_repo, "init", "--skill", "claude-code")
    assert read(bare_repo, SKILL) == "packaged skill\n"


def test_an_unknown_harness_is_refused_and_nothing_is_written(bare_repo):
    out = run_cli(bare_repo, "init", "--skill", "cursor")
    assert (
        out["ok"],
        out["result"].get("reason"),
        "claude-code" in out.get("error", ""),
        (bare_repo / "tdd.toml").exists(),
    ) == (False, "unknown_harness", True, False)


def test_init_skill_writes_the_installed_hooks(bare_repo, packaged):
    run_cli(bare_repo, "init", "--skill", "claude-code")
    assert {STOP_HOOK: read(bare_repo, STOP_HOOK), BASH_HOOK: read(bare_repo, BASH_HOOK)} == {
        STOP_HOOK: "packaged stop\n",
        BASH_HOOK: "packaged bash\n",
    }


def test_every_scaffolded_file_is_carried_into_the_wheel():
    from tddcli import harness

    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    included = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]
    sources = [f.source for h in harness.HARNESSES.values() for f in h.files]
    assert {s: included.get(s) for s in sources} == {s: f"tddcli/_docs/{s}" for s in sources}


def test_a_scaffold_missing_from_the_install_is_refused_and_nothing_is_written(
    bare_repo, monkeypatch
):
    monkeypatch.setattr(docs, "_PACKAGED", Path("/nonexistent"))
    monkeypatch.setattr(docs, "_SOURCE", Path("/nonexistent"))
    out = run_cli(bare_repo, "init", "--skill", "claude-code")
    assert (
        out["ok"],
        out["result"].get("reason"),
        (bare_repo / "tdd.toml").exists(),
        read(bare_repo, SKILL),
    ) == (False, "missing_from_install", False, None)
