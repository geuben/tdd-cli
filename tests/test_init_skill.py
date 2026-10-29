"""`tdd init --skill`: the driving skill and hooks, from the copies installed with the binary."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from conftest import run_cli
from tddcli import contract, docs
from tddcli.envelope import ENVELOPE_VERSION, VERB_SET_VERSION

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = ".claude/skills/tdd-drive/SKILL.md"


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
