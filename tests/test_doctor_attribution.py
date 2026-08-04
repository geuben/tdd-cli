"""`tdd doctor` attributes a collection failure to its project (issues #3 and #5).

P2 — the closest existing check, `verify: pytest-json-report installed`, reads the
subprocess's *stderr*, and `uv` writes environment warnings there while pytest writes
the actual `ModuleNotFoundError` to *stdout*. Reading the wrong stream is the root
cause of issue #3.

`repo_broken` (P4) cannot start a run and must only be used here — doctor needs none.

Fixture friction, per the plan: `uv run` inside `repo_broken`'s `verify` project
creates `verify/.venv`, so `worktree clean` reports `false` in doctor output. Assert
on the specific check under test, never on `healthy`, unless the test is explicitly
about the exit/`ok` contract (cycle 17).

See tasks/multi-agent-feedback.md Part D.
"""

from __future__ import annotations

from conftest import git, run_cli


def test_doctor_attributes_a_collection_failure_to_its_project(repo_broken):
    out = run_cli(repo_broken, "doctor")
    checks = out["result"]["checks"]
    verify_checks = [c for c in checks if c.get("detail", "").find("yaml_does_not_exist") != -1]
    assert verify_checks, checks
    # cycle 16.5 replaced the `f"{name}: ..."` prefix convention with an explicit
    # `project=` field on the check dict.
    named = [c for c in verify_checks if c.get("project") == "verify"]
    assert named, verify_checks


def test_doctor_reports_a_per_project_result_map(repo_broken):
    out = run_cli(repo_broken, "doctor")
    projects = out["result"]["projects"]
    assert projects["verify"]["ok"] is False, projects


def test_doctor_fails_when_a_check_fails(repo_broken):
    out = run_cli(repo_broken, "doctor")
    assert out["ok"] is False, out


def test_doctor_succeeds_when_every_check_passes(repo):
    """The other half of cycle 17's `ok = healthy`: a genuinely healthy environment
    must still report `ok: true`, not just fail loudly when unhealthy. `uv run`'s
    `.venv` and pytest's cache directories are gitignored so `worktree clean` can
    actually pass — see the plan's "Fixture friction" note on `repo_broken`."""
    (repo / ".gitignore").write_text(".venv/\n__pycache__/\n.pytest_cache/\n*.egg-info/\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "add gitignore")

    out = run_cli(repo, "doctor")
    assert out["ok"] is True, out["result"]["checks"]


def test_doctor_names_a_missing_node_modules(repo_multi):
    out = run_cli(repo_multi, "doctor")
    checks = out["result"]["checks"]
    frontend_checks = [c for c in checks if c.get("project") == "frontend"]
    node_modules_checks = [c for c in frontend_checks if "node_modules" in c.get("detail", "")]
    assert node_modules_checks, frontend_checks
    for c in node_modules_checks:
        assert "at Vitest" not in c["detail"]
        assert "at async" not in c["detail"]


def test_doctor_does_not_check_node_modules_for_a_pytest_project(repo_multi):
    """The `node_modules present` check is vitest-specific — a pytest project has no
    `node_modules` either, and must not be flagged for lacking one."""
    out = run_cli(repo_multi, "doctor")
    checks = out["result"]["checks"]
    backend_checks = [c for c in checks if c.get("project") == "backend"]
    assert backend_checks, checks
    assert not any(c["check"] == "node_modules present" for c in backend_checks), backend_checks
