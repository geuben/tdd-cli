from __future__ import annotations

import json

from tddcli import identity


def test_env_override_resolves_as_declared(tmp_path, monkeypatch):
    monkeypatch.setenv("TDD_EXECUTOR_MODEL", "harness-model")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.setattr(identity, "TRANSCRIPT_ROOT", tmp_path / "nowhere")

    e = identity.resolve(None)
    assert e.model == "harness-model"
    assert e.source == "declared"


def test_declared_override_beats_transcript(tmp_path, monkeypatch):
    slug = str(tmp_path / "proj").replace("/", "-")
    transcripts = tmp_path / "projects" / slug
    transcripts.mkdir(parents=True)
    (transcripts / "sess-99.jsonl").write_text(
        json.dumps({"type": "assistant", "model": "claude-transcript-model"}) + "\n"
    )
    monkeypatch.setattr(identity, "TRANSCRIPT_ROOT", tmp_path / "projects")
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "sess-99")
    monkeypatch.setenv("TDD_EXECUTOR_MODEL", "harness-model")

    e = identity.resolve(tmp_path / "proj")
    assert e.source == "declared"
    assert e.model == "harness-model"


def test_reason_names_the_missing_session_env(tmp_path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("TDD_EXECUTOR_MODEL", raising=False)
    monkeypatch.setattr(identity, "TRANSCRIPT_ROOT", tmp_path / "nowhere")

    e = identity.resolve(None)
    assert e.model == "unknown"
    assert "CLAUDE_CODE_SESSION_ID" in e.reason


def test_reason_names_the_missing_transcript(tmp_path, monkeypatch):
    empty_root = tmp_path / "projects"
    empty_root.mkdir()
    monkeypatch.setattr(identity, "TRANSCRIPT_ROOT", empty_root)
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "sess-gone")
    monkeypatch.delenv("TDD_EXECUTOR_MODEL", raising=False)

    e = identity.resolve(None)
    assert e.model == "unknown"
    assert e.reason and "sess-gone" in e.reason


def test_reason_names_the_model_less_transcript(tmp_path, monkeypatch):
    root = tmp_path / "projects"
    (root / "slug").mkdir(parents=True)
    (root / "slug" / "sess-empty.jsonl").write_text(
        json.dumps({"type": "user", "content": "hello"}) + "\n"
    )
    monkeypatch.setattr(identity, "TRANSCRIPT_ROOT", root)
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "sess-empty")
    monkeypatch.delenv("TDD_EXECUTOR_MODEL", raising=False)

    e = identity.resolve(None)
    assert e.model == "unknown"
    assert e.reason and "no model" in e.reason.lower()
