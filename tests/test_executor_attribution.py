from __future__ import annotations

import json
from pathlib import Path

from tddcli import identity


def test_env_override_resolves_as_declared(tmp_path, monkeypatch):
    monkeypatch.setenv("TDD_EXECUTOR_MODEL", "harness-model")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.setattr(identity, "TRANSCRIPT_ROOT", tmp_path / "nowhere")

    e = identity.resolve(None)
    assert e.model == "harness-model"
    assert e.source == "declared"
