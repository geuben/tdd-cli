"""Artifact regeneration commits the artifact's own path, not just `generated` output.

A regenerate hook that rewrites an upstream artifact file (an OpenAPI spec, say)
used to leave it dirty for the whole run: only `generated = true` paths were
staged into the `chore(...): regenerate` commit. CI then compared the committed
(stale) spec against the committed (fresh) client and reported drift, and every
subsequent phase commit re-flagged the file as `undeclared_file_touched`.
"""

from __future__ import annotations

from conftest import git, run_cli, write_plan

PLAN = """---
cycles:
  - n: 1
    project: backend
    refactor_cycle: true
    title: "behaviour-preserving cleanup"
---
"""


def _start_run(repo, artifact_toml: str):
    (repo / "schema").mkdir()
    (repo / "schema" / "openapi.json").write_text("v1\n")
    with (repo / "tdd.toml").open("a") as f:
        f.write(artifact_toml)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "declare artifacts")
    plan = write_plan(repo, PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]


def test_regeneration_commits_the_artifacts_own_path(repo):
    """The regenerated spec must land in the chore commit even without `generated = true`."""
    _start_run(
        repo,
        "\n[artifact.openapi]\n"
        'path        = "schema/openapi.json"\n'
        'produced_by = "backend"\n'
        "regenerate  = \"printf 'v2\\\\n' > schema/openapi.json\"\n",
    )
    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "complete", out

    assert "schema/openapi.json" not in git(repo, "status", "--porcelain")
    subjects = git(repo, "log", "--pretty=%s")
    assert "chore(openapi): regenerate" in subjects
    files = git(repo, "log", "--name-only", "--pretty=", "--grep", "chore(openapi)")
    assert "schema/openapi.json" in files


def test_regeneration_commits_upstream_paths_the_hook_refreshed(repo):
    """A downstream hook that rewrites its upstream spec stages both, per the chain."""
    _start_run(
        repo,
        "\n[artifact.openapi]\n"
        'path        = "schema/openapi.json"\n'
        'produced_by = "backend"\n'
        "\n[artifact.api_client]\n"
        'path        = "generated"\n'
        'produced_by = "artifact.openapi"\n'
        "regenerate  = \"mkdir -p generated"
        " && printf 'client-v2\\\\n' > generated/client.ts"
        " && printf 'v2\\\\n' > schema/openapi.json\"\n"
        "generated   = true\n",
    )
    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "complete", out

    assert "schema/openapi.json" not in git(repo, "status", "--porcelain")
    files = git(repo, "log", "--name-only", "--pretty=", "--grep", "chore(api_client)")
    assert "generated/client.ts" in files
    assert "schema/openapi.json" in files
