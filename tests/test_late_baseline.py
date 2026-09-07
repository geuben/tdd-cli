"""Late-baseline probing: start sha capture, temporary worktrees, and per-test verdicts."""

from __future__ import annotations

import json

from conftest import run_cli, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger
from test_baseline_integrity import BACKEND_ONLY_PLAN, PLAN, TEST_ADD


def _drive_to_close(repo):
    """Register BACKEND_ONLY_PLAN, start, RED, GREEN; leave cycle 1 in AWAITING_REFACTOR.

    Marks the schema artifact as generated so that touching it in the close sweep
    advance does not trigger undeclared_file_touched on the backend-only cycle.
    """
    from conftest import git as _git
    toml = (repo / "tdd.toml").read_text()
    (repo / "tdd.toml").write_text(toml.replace('regenerate  = "true"', 'regenerate  = "true"\ngenerated   = true'))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "mark schema artifact as generated")
    plan = write_plan(repo, BACKEND_ONLY_PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    raise NotImplementedError\n")
    run_cli(repo, "advance")  # RED -> AWAITING_IMPL
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    run_cli(repo, "advance")  # GREEN -> AWAITING_REFACTOR
    return out


def _pull_svc_into_the_sweep(repo):
    """Touching the schema artifact path pulls svc (its consumer) into the close sweep."""
    (repo / "other" / "schema.json").write_text('{"touched": true}')


def test_temporary_worktree_links_ignored_directories_under_the_project_root(repo):
    from conftest import git as _git
    gitignore = repo / ".gitignore"
    gitignore.write_text(gitignore.read_text() + "node_modules/\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "add node_modules to gitignore")
    sha = gitutil.head(repo)
    (repo / "backend" / "node_modules" / "pkg").mkdir(parents=True)
    (repo / "backend" / "node_modules" / "pkg" / "index.js").write_text("x")
    with gitutil.temporary_worktree(repo, sha, link_ignored_under=["backend"]) as tmp:
        target = tmp / "backend" / "node_modules" / "pkg" / "index.js"
        seen = target.read_text() if target.exists() else None
    assert seen == "x"


def test_temporary_worktree_checks_out_the_sha_and_is_removed_on_exit(repo):
    first = gitutil.head(repo)
    (repo / "backend" / "app" / "new.py").write_text("x = 1\n")
    from conftest import git as _git
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "second commit")
    with gitutil.temporary_worktree(repo, first) as tmp:
        inside = gitutil.head(tmp)
    assert (inside, tmp.exists()) == (first, False)


def test_run_start_records_the_start_sha_on_the_run_row(repo):
    write_plan(repo, PLAN)
    sha = gitutil.head(repo)
    run_cli(repo, "plan", "register", "tasks/plan.md")
    out = run_cli(repo, "run", "start", "--plan", "tasks/plan.md")
    assert out["ok"], out
    ledger = Ledger(gitutil.repo_identity(repo))
    run_id = out["run"]["id"]
    row = ledger.one("SELECT * FROM run WHERE id = ?", (run_id,))
    assert dict(row).get("start_sha") == sha


def test_a_failure_present_at_the_start_sha_lets_the_cycle_close(repo_schema_other):
    repo = repo_schema_other
    _drive_to_close(repo)
    _pull_svc_into_the_sweep(repo)
    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "complete"


def test_a_failure_absent_at_the_start_sha_is_a_regression_in_a_late_baselined_project(
    repo_schema_other,
):
    repo = repo_schema_other
    from conftest import git as _git

    (repo / "svc" / "tests" / "test_svc.py").write_text("def test_svc_passes():\n    assert True\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "make svc green at start sha")
    _drive_to_close(repo)
    (repo / "svc" / "tests" / "test_svc.py").write_text("def test_svc_passes():\n    assert False\n")
    _pull_svc_into_the_sweep(repo)
    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "fix_regression"


def test_baseline_amended_records_a_verdict_per_test(repo):
    from conftest import git as _git
    from test_baseline_integrity import reach_refactor

    (repo / "backend" / "tests" / "test_flaky.py").write_text("def test_flaky():\n    assert False\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "add pre-existing flaky test")
    reach_refactor(repo)
    ledger = Ledger(gitutil.repo_identity(repo))
    run_row = ledger.one(
        "SELECT * FROM run WHERE worktree_path = ? ORDER BY id DESC LIMIT 1", (str(repo),)
    )
    run_id = run_row["id"]
    start_sha = run_row["start_sha"]
    ledger.db.execute(
        "UPDATE baseline SET failing = '[]' WHERE run_id = ? AND project = 'backend'", (run_id,)
    )
    ledger.db.commit()
    (repo / "backend" / "tests" / "test_smoke.py").write_text("def test_smoke():\n    assert False\n")
    run_cli(repo, "advance")
    run_cli(repo, "blocker", "--kind", "pre_existing_failure", "--detail", "x")
    run_cli(repo, "resume", "--unblock", "--note", "n", "--accept-failures")
    event = ledger.one(
        "SELECT detail FROM integrity_event WHERE run_id = ? AND kind = 'baseline_amended'",
        (run_id,),
    )
    assert json.loads(event["detail"]) == {
        "backend": {
            "start_sha": start_sha,
            "accepted": {"backend::tests/test_flaky.py::test_flaky": "fails at start sha"},
            "refused": {"backend::tests/test_smoke.py::test_smoke": "passes at start sha"},
        }
    }


def test_accept_failures_accepts_a_test_that_fails_at_the_start_sha(repo):
    from conftest import git as _git
    from test_baseline_integrity import reach_refactor

    (repo / "backend" / "tests" / "test_flaky.py").write_text("def test_flaky():\n    assert False\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "add pre-existing flaky test")
    reach_refactor(repo)
    ledger = Ledger(gitutil.repo_identity(repo))
    run_row = ledger.one(
        "SELECT * FROM run WHERE worktree_path = ? ORDER BY id DESC LIMIT 1", (str(repo),)
    )
    run_id = run_row["id"]
    ledger.db.execute(
        "UPDATE baseline SET failing = '[]' WHERE run_id = ? AND project = 'backend'", (run_id,)
    )
    ledger.db.commit()
    run_cli(repo, "advance")
    run_cli(repo, "blocker", "--kind", "pre_existing_failure", "--detail", "x")
    resumed = run_cli(repo, "resume", "--unblock", "--note", "n", "--accept-failures")
    assert resumed["result"].get("accepted_into_baseline") == {
        "backend": ["backend::tests/test_flaky.py::test_flaky"]
    }


def test_accept_failures_refuses_a_test_that_passes_at_the_start_sha(repo):
    from test_baseline_integrity import reach_refactor
    reach_refactor(repo)
    (repo / "backend" / "tests" / "test_smoke.py").write_text("def test_smoke():\n    assert False\n")
    run_cli(repo, "advance")
    run_cli(repo, "blocker", "--kind", "pre_existing_failure", "--detail", "x")
    resumed = run_cli(repo, "resume", "--unblock", "--note", "n", "--accept-failures")
    ledger = Ledger(gitutil.repo_identity(repo))
    run_id = resumed["run"]["id"]
    row = ledger.one("SELECT failing FROM baseline WHERE run_id = ? AND project = 'backend'", (run_id,))
    assert (
        json.loads(row["failing"]),
        resumed["result"].get("refused_from_baseline"),
    ) == ([], {"backend": ["backend::tests/test_smoke.py::test_smoke"]})


def test_an_unobservable_late_probe_blocks_without_a_baseline_row(repo_schema_other):
    repo = repo_schema_other
    from conftest import git as _git

    (repo / "svc" / "tests" / "test_svc.py").write_text(
        "import nope_missing\n\ndef test_svc_fails():\n    assert False\n"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "svc: uncollectable at start sha")
    _drive_to_close(repo)
    (repo / "svc" / "tests" / "test_svc.py").write_text("def test_svc_fails():\n    assert False\n")
    _pull_svc_into_the_sweep(repo)
    ledger = Ledger(gitutil.repo_identity(repo))
    run_row = ledger.one(
        "SELECT * FROM run WHERE worktree_path = ? ORDER BY id DESC LIMIT 1", (str(repo),)
    )
    run_id = run_row["id"]
    out = run_cli(repo, "advance")
    row = ledger.one(
        "SELECT * FROM baseline WHERE run_id = ? AND project = 'svc'", (run_id,)
    )
    event = ledger.one(
        "SELECT * FROM integrity_event WHERE run_id = ? AND kind = 'baseline_late_probe_unobserved'",
        (run_id,),
    )
    assert (
        out["next_action"]["verb"],
        row is None,
        "--accept-failures" in out["next_action"].get("detail", ""),
        event is not None,
    ) == ("resolve_blocker", True, False, True)


def test_close_sweep_late_probes_an_unbaselined_project_at_the_start_sha(repo_schema_other):
    repo = repo_schema_other
    _drive_to_close(repo)
    ledger = Ledger(gitutil.repo_identity(repo))
    run_row = ledger.one(
        "SELECT * FROM run WHERE worktree_path = ? ORDER BY id DESC LIMIT 1", (str(repo),)
    )
    run_id = run_row["id"]
    start_sha = run_row["start_sha"]
    _pull_svc_into_the_sweep(repo)
    run_cli(repo, "advance")
    row = ledger.one(
        "SELECT source, failing FROM baseline WHERE run_id = ? AND project = 'svc'", (run_id,)
    )
    event = ledger.one(
        "SELECT detail FROM integrity_event WHERE run_id = ? AND kind = 'baseline_late_probe'",
        (run_id,),
    )
    detail = json.loads(event["detail"]) if event else {}
    assert (
        row["source"] if row else None,
        json.loads(row["failing"]) if row else None,
        detail.get("start_sha"),
    ) == ("late_probe", ["svc::tests/test_svc.py::test_svc_fails"], start_sha)
