from __future__ import annotations

import json
from pathlib import Path

from tddcli import config as config_mod
from tddcli import identity, snapshot
from tddcli.ledger import Ledger


def cfg_for(repo: Path):
    return config_mod.load(repo)


def test_snapshot_restores_an_uncommitted_file_untouched(repo):
    """The RED test is uncommitted at a passed-on-arrival; it must survive intact."""
    cfg = cfg_for(repo)
    test_file = repo / "backend" / "tests" / "test_new.py"
    test_file.write_text("def test_new():\n    assert True\n")

    snap = snapshot.capture(repo, cfg)
    before = snapshot.fingerprint(repo, cfg)

    test_file.write_text("def test_new():\n    assert False  # mutated\n")
    (repo / "backend" / "app" / "victim.py").write_text("X = 1\n")

    snapshot.restore(repo, cfg, snap)
    assert snapshot.fingerprint(repo, cfg) == before
    assert test_file.read_text() == "def test_new():\n    assert True\n"
    assert not (repo / "backend" / "app" / "victim.py").exists()


def test_snapshot_reverts_a_tracked_file_to_its_captured_state(repo):
    cfg = cfg_for(repo)
    tracked = repo / "backend" / "tests" / "test_smoke.py"
    snap = snapshot.capture(repo, cfg)
    before = snapshot.fingerprint(repo, cfg)

    tracked.write_text("def test_smoke():\n    assert False\n")
    snapshot.restore(repo, cfg, snap)

    assert tracked.read_text() == "def test_smoke():\n    assert True\n"
    assert snapshot.fingerprint(repo, cfg) == before


def test_build_output_never_affects_the_fingerprint(repo):
    """A suite run between begin and end rewrites .pyc; that must not fail the check."""
    cfg = cfg_for(repo)
    before = snapshot.fingerprint(repo, cfg)
    cache = repo / "backend" / "tests" / "__pycache__"
    cache.mkdir(parents=True, exist_ok=True)
    (cache / "test_smoke.cpython-312.pyc").write_bytes(b"\x00binary")
    assert snapshot.fingerprint(repo, cfg) == before


def test_a_partial_restore_is_detected(repo):
    cfg = cfg_for(repo)
    victim = repo / "backend" / "app" / "thing.py"
    victim.write_text("VALUE = 1\n")
    snapshot.capture(repo, cfg)
    before = snapshot.fingerprint(repo, cfg)

    victim.write_text("VALUE = 2\n")
    # A restore the agent performed badly, by hand.
    assert snapshot.fingerprint(repo, cfg) != before


# -- identity --------------------------------------------------------------


def test_model_is_read_from_the_session_transcript(tmp_path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    slug = str(project).replace("/", "-")
    transcripts = tmp_path / "home" / ".claude" / "projects" / slug
    transcripts.mkdir(parents=True)
    (transcripts / "sess-1.jsonl").write_text(
        json.dumps({"type": "assistant", "model": "claude-sonnet-4-6"}) + "\n"
    )
    monkeypatch.setattr(
        identity, "TRANSCRIPT_ROOT", tmp_path / "home" / ".claude" / "projects"
    )
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "sess-1")
    monkeypatch.delenv("TDD_EXECUTOR_MODEL", raising=False)

    executor = identity.resolve(project)
    assert executor.model == "claude-sonnet-4-6"
    assert executor.source == "transcript"


def test_human_label_is_the_fallback_not_the_default(tmp_path, monkeypatch):
    monkeypatch.setattr(identity, "TRANSCRIPT_ROOT", tmp_path / "nowhere")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("TDD_EXECUTOR_MODEL", raising=False)

    assert identity.resolve(None, "opus-by-hand").source == "human"
    assert identity.resolve(None).model == "unknown"


def test_last_model_wins_when_a_session_switches(tmp_path, monkeypatch):
    root = tmp_path / "projects"
    (root / "slug").mkdir(parents=True)
    (root / "slug" / "s.jsonl").write_text(
        json.dumps({"model": "claude-opus-5"}) + "\n"
        + json.dumps({"model": "claude-sonnet-4-6"}) + "\n"
    )
    monkeypatch.setattr(identity, "TRANSCRIPT_ROOT", root)
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "s")
    monkeypatch.delenv("TDD_EXECUTOR_MODEL", raising=False)
    assert identity.resolve(None).model == "claude-sonnet-4-6"


def test_cached_baseline_respects_max_age(tmp_path, monkeypatch):
    from datetime import datetime, timedelta, timezone
    monkeypatch.setenv("TDD_LEDGER_HOME", str(tmp_path))
    ledger = Ledger(tmp_path / "repo")

    ledger.cache_baseline(
        "svc", "treeA", "cfgA",
        failing=[],
        tests=["svc::t::a"],
        failed_files={},
    )
    # back-date the entry to 2 minutes ago
    old_ts = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
    ledger.db.execute(
        "UPDATE baseline_cache SET created_at = ? WHERE project = 'svc'", (old_ts,)
    )
    ledger.db.commit()

    # with a 60-second TTL the entry is too old → None
    assert ledger.cached_baseline("svc", "treeA", "cfgA", max_age_s=60) is None
    # with no TTL the entry is still returned
    assert ledger.cached_baseline("svc", "treeA", "cfgA") is not None


def test_baseline_cache_round_trips_by_content_key(tmp_path, monkeypatch):
    monkeypatch.setenv("TDD_LEDGER_HOME", str(tmp_path))
    ledger = Ledger(tmp_path / "repo")

    ledger.cache_baseline(
        "svc", "treeA", "cfgA",
        failing=["svc::t::a"],
        tests=["svc::t::a", "svc::t::b"],
        failed_files={},
    )

    row = ledger.cached_baseline("svc", "treeA", "cfgA")
    assert json.loads(row["failing"]) == ["svc::t::a"]
    assert json.loads(row["tests"]) == ["svc::t::a", "svc::t::b"]
    assert json.loads(row["failed_files"]) == {}

    assert ledger.cached_baseline("svc", "treeB", "cfgA") is None
    assert ledger.cached_baseline("svc", "treeA", "cfgB") is None


def test_previous_baseline_returns_prior_runs_failing_set(tmp_path, monkeypatch):
    from tddcli.ledger import now

    monkeypatch.setenv("TDD_LEDGER_HOME", str(tmp_path))
    ledger = Ledger(tmp_path / "repo")

    W = "/some/worktree"
    contract_id = ledger.insert(
        "plan_contract",
        plan_path="tasks/plan.md",
        git_blob_sha=None,
        git_commit=None,
        status="declared",
        declared_cycles="[]",
        annotation_keys="[]",
        ancillary_files="[]",
        registered_at=now(),
    )
    prior_run_id = ledger.insert(
        "run",
        plan_contract_id=contract_id,
        executor_model="test-model",
        executor_source="human",
        worktree_path=W,
        started_at=now(),
        ended_at=now(),
        preexisting_dirty="[]",
    )
    ledger.insert(
        "baseline",
        run_id=prior_run_id,
        project="backend",
        failing=json.dumps(["backend::t::a", "backend::t::b"]),
        captured_at=now(),
        source="probed",
    )

    result = ledger.previous_baseline(W, "backend", before_run_id=prior_run_id + 100)
    assert result == {"backend::t::a", "backend::t::b"}

    result_none = ledger.previous_baseline(W, "backend", before_run_id=prior_run_id)
    assert result_none is None
