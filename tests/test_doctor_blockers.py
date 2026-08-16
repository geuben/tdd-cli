"""Every blocker `tdd doctor` emits must name what to fix.

The incident: doctor returned `resolve_blocker` / "Resolve the failing checks above"
with a single failing check — `{"check": "worktree clean", "ok": false, "detail": ""}`.
The dirt was an unrelated planning note and a `.claude/settings.json` edit. The agent
could not see either, guessed, re-ran doctor, and got the identical opaque failure.

Two invariants close that loop:

1. A failing check always carries a detail. `check()` raises rather than record an
   unfalsifiable blocker, so the class cannot reappear in a check added later.
2. Only dirt the loop would actually observe blocks — a declared project root, a
   declared artifact, or `tdd.toml`. Everything else is reported, not enforced
   (the PRD's "tree clean enough", §8.1).
"""

from __future__ import annotations

from conftest import git, run_cli


def _check(out: dict, name: str) -> dict:
    matches = [c for c in out["result"]["checks"] if c["check"] == name]
    assert len(matches) == 1, out["result"]["checks"]
    return matches[0]


def test_dirt_inside_a_project_root_blocks_and_names_the_path(repo):
    (repo / "backend" / "app" / "scratch.py").write_text("x = 1\n")

    clean = _check(run_cli(repo, "doctor"), "worktree clean")
    assert clean["ok"] is False
    assert "backend/app/scratch.py" in clean["detail"]


def test_a_modified_tdd_toml_blocks(repo):
    (repo / "tdd.toml").write_text((repo / "tdd.toml").read_text() + "\n")

    clean = _check(run_cli(repo, "doctor"), "worktree clean")
    assert clean["ok"] is False
    assert "tdd.toml" in clean["detail"]


def test_dirt_outside_every_declared_root_does_not_block(repo):
    """The incident's own shape: a planning note and an editor setting. Neither is
    readable by any adapter, so neither can corrupt a baseline."""
    (repo / "tasks").mkdir()
    (repo / "tasks" / "fix-406-proxy-ws-forwarding.md").write_text("# plan\n")
    (repo / ".claude").mkdir()
    (repo / ".claude" / "settings.json").write_text("{}\n")

    clean = _check(run_cli(repo, "doctor"), "worktree clean")
    assert clean["ok"] is True, clean
    # Reported, not enforced — a human still wants to know the tree is not pristine.
    assert "tasks/fix-406-proxy-ws-forwarding.md" in clean["detail"]


def test_doctors_own_probe_residue_does_not_block(repo):
    """Doctor shells out to `uv run` and `vitest list`, which write `.venv`,
    `node_modules` and cache directories into the tree it then grades. Without this,
    running doctor is what makes doctor fail — and running it again re-does it."""
    (repo / "backend" / ".venv" / "bin").mkdir(parents=True)
    (repo / "backend" / ".venv" / "bin" / "python").write_text("")
    (repo / "backend" / "__pycache__").mkdir()
    (repo / "backend" / "__pycache__" / "app.pyc").write_text("")

    clean = _check(run_cli(repo, "doctor"), "worktree clean")
    assert clean["ok"] is True, clean


def test_blocking_dirt_is_reported_even_when_unrelated_dirt_exists(repo):
    (repo / "backend" / "app" / "scratch.py").write_text("x = 1\n")
    (repo / "notes.md").write_text("# notes\n")

    clean = _check(run_cli(repo, "doctor"), "worktree clean")
    assert clean["ok"] is False
    assert "backend/app/scratch.py" in clean["detail"]


def test_no_failing_check_is_ever_emitted_without_a_detail(repo_broken):
    """The structural half. `repo_broken` fails collection; dirty the tree and break
    the artifact wiring too, so several failure paths run in one invocation."""
    (repo_broken / "verify" / "tests" / "test_extra.py").write_text("\n")
    (repo_broken / "tdd.toml").write_text(
        (repo_broken / "tdd.toml").read_text()
        + '\n[artifact.openapi]\npath = "openapi.json"\nproduced_by = "backend"\n'
    )

    out = run_cli(repo_broken, "doctor")
    failing = [c for c in out["result"]["checks"] if not c["ok"]]
    assert failing, out["result"]["checks"]
    for c in failing:
        assert c["detail"].strip(), c


def test_a_check_cannot_fail_without_a_detail():
    """Enforced at the helper, so a check added later inherits the guarantee rather
    than relying on its author to remember."""
    import pytest

    from tddcli.cli import _doctor_checklist

    checks, check = _doctor_checklist()
    check("fine", False, "here is what to do")
    with pytest.raises(AssertionError, match="silent"):
        check("silent", False)
    assert [c["check"] for c in checks] == ["fine"]


def _with_artifact(repo, hook: str = 'regenerate = "true"') -> None:
    (repo / "schema").mkdir(exist_ok=True)
    (repo / "schema" / "openapi.json").write_text("{}\n")
    (repo / "tdd.toml").write_text(
        (repo / "tdd.toml").read_text()
        + f'\n[artifact.openapi]\npath = "schema/openapi.json"\n'
          f'produced_by = "backend"\n{hook}\n'
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "declare openapi artifact")


def test_dirt_at_a_declared_artifact_path_blocks(repo):
    """An artifact sits outside every project root but is still read by a run —
    `run start` verifies its freshness. Uncommitted drift there is exactly the
    staleness the artifact edge exists to catch."""
    _with_artifact(repo)
    (repo / "schema" / "openapi.json").write_text('{"drift": true}\n')

    clean = _check(run_cli(repo, "doctor"), "worktree clean")
    assert clean["ok"] is False
    assert "schema/openapi.json" in clean["detail"]


def test_an_artifact_needs_only_one_of_check_or_regenerate(repo):
    """Either hook alone makes freshness verifiable — requiring both would fail
    every artifact that only knows how to rebuild itself."""
    _with_artifact(repo, hook='regenerate = "true"')

    assert _check(run_cli(repo, "doctor"), "artifact openapi: has check or regenerate")["ok"] is True

    _check_only = repo / "tdd.toml"
    _check_only.write_text(_check_only.read_text().replace('regenerate = "true"', 'check = "true"'))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "swap regenerate for check")

    assert _check(run_cli(repo, "doctor"), "artifact openapi: has check or regenerate")["ok"] is True


def test_a_long_dirt_list_is_truncated_but_the_fifth_path_is_not(repo):
    """The detail is read by an agent, so it stays bounded — but the boundary must
    not eat a path it had room for."""
    for i in range(5):
        (repo / "backend" / "app" / f"f{i}.py").write_text("x = 1\n")

    detail = _check(run_cli(repo, "doctor"), "worktree clean")["detail"]
    assert "more)" not in detail, detail
    assert "backend/app/f4.py" in detail

    (repo / "backend" / "app" / "f5.py").write_text("x = 1\n")
    detail = _check(run_cli(repo, "doctor"), "worktree clean")["detail"]
    assert "(+1 more)" in detail, detail


def test_test_paths_omission_says_what_to_add(repo):
    (repo / "tdd.toml").write_text(
        '[project.backend]\nroot = "backend"\nadapter = "pytest"\ntest_paths = []\n'
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "drop test_paths")

    declared = _check(run_cli(repo, "doctor"), "test_paths declared")
    assert declared["ok"] is False
    assert "test_paths" in declared["detail"]
