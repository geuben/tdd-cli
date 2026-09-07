"""Artifact regeneration commits the artifact's own path, not just `generated` output.

A regenerate hook that rewrites an upstream artifact file (an OpenAPI spec, say)
used to leave it dirty for the whole run: only `generated = true` paths were
staged into the `chore(...): regenerate` commit. CI then compared the committed
(stale) spec against the committed (fresh) client and reported drift, and every
subsequent phase commit re-flagged the file as `undeclared_file_touched`.
"""

from __future__ import annotations

from conftest import git, run_cli, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger

PLAN = """---
cycles:
  - n: 1
    project: backend
    refactor_cycle: true
    title: "behaviour-preserving cleanup"
---
"""

OPENAPI_ARTIFACT_TOML = (
    "\n[artifact.openapi]\n"
    'path        = "schema/openapi.json"\n'
    'produced_by = "backend"\n'
    "regenerate  = \"printf 'v2\\\\n' > schema/openapi.json\"\n"
)


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


def _start_run_with_id(repo, artifact_toml: str) -> int:
    """Like _start_run but returns the run_id from the run start envelope."""
    (repo / "schema").mkdir()
    (repo / "schema" / "openapi.json").write_text("v1\n")
    with (repo / "tdd.toml").open("a") as f:
        f.write(artifact_toml)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "declare artifacts")
    plan = write_plan(repo, PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out
    return out["run"]["id"]


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
        'regenerate  = "mkdir -p generated'
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


def test_successful_regeneration_marks_artifact_check_regenerated(repo):
    """The artifact_check row must have regenerated=1 when the hook produces a commit."""
    run_id = _start_run_with_id(repo, OPENAPI_ARTIFACT_TOML)

    ledger = Ledger(gitutil.repo_identity(repo))
    row = ledger.one(
        "SELECT regenerated FROM artifact_check WHERE run_id = ? AND artifact = 'openapi' AND stale = 1",
        (run_id,),
    )
    assert row is not None, "expected a stale artifact_check row for openapi"
    assert row["regenerated"] == 1, f"expected regenerated=1, got {row['regenerated']}"


def test_resolved_stale_artifact_emits_no_event(repo):
    """When the tool resolves staleness with a commit, no stale_artifact event is emitted."""
    run_id = _start_run_with_id(repo, OPENAPI_ARTIFACT_TOML)

    ledger = Ledger(gitutil.repo_identity(repo))
    events = ledger.all(
        "SELECT * FROM integrity_event WHERE run_id = ? AND kind = 'stale_artifact'",
        (run_id,),
    )
    assert events == [], f"expected no stale_artifact events, got {events}"


def test_unresolved_stale_artifact_still_emits_event(repo):
    """A stale artifact with no regenerate hook must still emit stale_artifact."""
    with (repo / "tdd.toml").open("a") as f:
        f.write(
            "\n[artifact.spec]\n"
            'path        = "backend/spec.json"\n'
            'produced_by = "backend"\n'
            'check       = "false"\n'
        )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "declare spec artifact")
    plan = write_plan(repo, PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out
    run_id = out["run"]["id"]

    ledger = Ledger(gitutil.repo_identity(repo))
    event = ledger.one(
        "SELECT * FROM integrity_event WHERE run_id = ? AND kind = 'stale_artifact' AND detail = 'spec'",
        (run_id,),
    )
    assert event is not None, "expected a stale_artifact event for spec"


def test_failed_regenerate_after_stale_check_reports_hook_failure_not_stale(repo, tmp_path):
    marker = tmp_path / "fail"
    (repo / "wasm").mkdir()
    (repo / "wasm" / "bundle.js").write_text("v1\n")
    with (repo / "tdd.toml").open("a") as f:
        f.write(
            "\n[artifact.wasm]\n"
            'path        = "wasm/bundle.js"\n'
            'produced_by = "backend"\n'
            'check       = "false"\n'
            f'regenerate  = "test ! -f {marker} || {{ echo boom >&2; exit 1; }}"\n'
        )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "declare wasm artifact")
    plan = write_plan(repo, PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    # run start: check=false → stale, hook succeeds (no marker) → run-level stale_artifact
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out
    run_id = out["run"]["id"]

    marker.touch()
    run_cli(repo, "advance")

    ledger = Ledger(gitutil.repo_identity(repo))
    kinds = [
        row["kind"]
        for row in ledger.all(
            "SELECT kind FROM integrity_event WHERE run_id = ? AND cycle_id IS NOT NULL ORDER BY id",
            (run_id,),
        )
    ]
    assert kinds == ["artifact_regenerate_failed"]


def test_cycle_closes_once_the_regenerate_hook_recovers(repo, tmp_path):
    marker = tmp_path / "fail"
    (repo / "wasm").mkdir()
    (repo / "wasm" / "bundle.js").write_text("v1\n")
    with (repo / "tdd.toml").open("a") as f:
        f.write(
            "\n[artifact.wasm]\n"
            'path        = "wasm/bundle.js"\n'
            'produced_by = "backend"\n'
            f'regenerate  = "test ! -f {marker} || {{ echo boom >&2; exit 1; }}"\n'
        )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "declare wasm artifact")
    plan = write_plan(repo, PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out

    # First advance: hook fails → fix_regression
    marker.touch()
    first = run_cli(repo, "advance")
    assert first["next_action"]["verb"] == "fix_regression", first

    # Remove marker so hook recovers, advance again → complete
    marker.unlink()
    second = run_cli(repo, "advance")
    assert second["next_action"]["verb"] == "complete"


def test_failed_regenerate_hook_at_close_replies_fix_regression(repo, tmp_path):
    marker = tmp_path / "fail"
    (repo / "wasm").mkdir()
    (repo / "wasm" / "bundle.js").write_text("v1\n")
    with (repo / "tdd.toml").open("a") as f:
        f.write(
            "\n[artifact.wasm]\n"
            'path        = "wasm/bundle.js"\n'
            'produced_by = "backend"\n'
            f'regenerate  = "test ! -f {marker} || {{ echo boom >&2; exit 1; }}"\n'
        )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "declare wasm artifact")
    plan = write_plan(repo, PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out

    marker.touch()
    adv = run_cli(repo, "advance")
    assert (
        adv["next_action"]["verb"],
        [f["artifact"] for f in adv["result"].get("artifact_failures", [])],
    ) == ("fix_regression", ["wasm"])


def test_failed_regenerate_hook_emits_artifact_regenerate_failed_event(repo, tmp_path):
    import json

    marker = tmp_path / "fail"
    (repo / "wasm").mkdir()
    (repo / "wasm" / "bundle.js").write_text("v1\n")
    with (repo / "tdd.toml").open("a") as f:
        f.write(
            "\n[artifact.wasm]\n"
            'path        = "wasm/bundle.js"\n'
            'produced_by = "backend"\n'
            f'regenerate  = "test ! -f {marker} || {{ echo boom >&2; exit 1; }}"\n'
        )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "declare wasm artifact")
    plan = write_plan(repo, PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out
    run_id = out["run"]["id"]

    marker.touch()
    run_cli(repo, "advance")

    ledger = Ledger(gitutil.repo_identity(repo))
    event = ledger.one(
        "SELECT detail FROM integrity_event WHERE run_id = ? AND kind = 'artifact_regenerate_failed'",
        (run_id,),
    )
    detail = json.loads(event["detail"]) if event else {}
    assert (detail.get("artifact"), detail.get("code"), "boom" in detail.get("stderr", "")) == (
        "wasm",
        1,
        True,
    )


def test_failed_regenerate_hook_marks_artifact_check_regenerate_failed(repo, tmp_path):
    marker = tmp_path / "fail"
    (repo / "wasm").mkdir()
    (repo / "wasm" / "bundle.js").write_text("v1\n")
    with (repo / "tdd.toml").open("a") as f:
        f.write(
            "\n[artifact.wasm]\n"
            'path        = "wasm/bundle.js"\n'
            'produced_by = "backend"\n'
            f'regenerate  = "test ! -f {marker} || {{ echo boom >&2; exit 1; }}"\n'
        )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "declare wasm artifact")
    plan = write_plan(repo, PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out
    run_id = out["run"]["id"]

    marker.touch()
    run_cli(repo, "advance")

    ledger = Ledger(gitutil.repo_identity(repo))
    row = ledger.one(
        "SELECT * FROM artifact_check WHERE run_id = ? AND cycle_id IS NOT NULL AND artifact = 'wasm'",
        (run_id,),
    )
    assert dict(row).get("regenerate_failed") == 1


def test_friction_log_reports_regenerated_artifacts_benignly(repo):
    """The friction log must list auto-regenerated artifacts without using stale_artifact."""
    _start_run(repo, OPENAPI_ARTIFACT_TOML)
    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "complete", out

    friction_path = repo / "friction.md"
    render_out = run_cli(repo, "log", "render", "--out", str(friction_path))
    assert render_out["ok"], render_out

    text = friction_path.read_text()
    assert "auto-regenerated" in text, "expected 'auto-regenerated' in friction log"
    assert "openapi" in text, "expected 'openapi' in friction log"
    assert "stale_artifact" not in text, "stale_artifact must not appear in friction log"
