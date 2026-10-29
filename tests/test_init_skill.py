"""`tdd init --skill`: the driving skill and hooks, from the copies installed with the binary."""

from __future__ import annotations

from pathlib import Path

import yaml

from tddcli import contract
from tddcli.envelope import ENVELOPE_VERSION, VERB_SET_VERSION

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_the_shipped_skill_declares_the_versions_this_binary_emits():
    text = (REPO_ROOT / "examples/skills/tdd-drive/SKILL.md").read_text()
    front = yaml.safe_load(contract.split_front_matter(text))
    assert front.get("metadata") == {
        "verb_set_version": str(VERB_SET_VERSION),
        "envelope_version": str(ENVELOPE_VERSION),
    }
