from __future__ import annotations

import json

from conftest import run_cli, write_plan
from tddcli import identity
from tddcli.ledger import Ledger

MINIMAL_PLAN = """\
---
cycles:
  - n: 1
    project: backend
    title: "placeholder"
    test: "tests/test_smoke.py::test_smoke"
    commit_red: "test: placeholder"
    commit_green: "feat: placeholder"
---
# Minimal plan for executor attribution tests
"""


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


def test_run_start_records_executor_unknown_event(repo, tmp_path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("TDD_EXECUTOR_MODEL", raising=False)
    monkeypatch.setattr(identity, "TRANSCRIPT_ROOT", tmp_path / "empty-transcripts")

    plan = write_plan(repo, MINIMAL_PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out

    ledger = Ledger(repo)
    rows = ledger.all(
        "SELECT detail FROM integrity_event WHERE kind = 'executor_unknown'"
    )
    assert len(rows) == 1
    assert "CLAUDE_CODE_SESSION_ID" in rows[0]["detail"]


def test_run_start_envelope_carries_executor_warning(repo, tmp_path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("TDD_EXECUTOR_MODEL", raising=False)
    monkeypatch.setattr(identity, "TRANSCRIPT_ROOT", tmp_path / "empty-transcripts")

    plan = write_plan(repo, MINIMAL_PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out

    warning = out["result"].get("executor_warning")
    assert warning and "CLAUDE_CODE_SESSION_ID" in warning
