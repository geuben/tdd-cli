"""`tdd run abandon`: end a run that will not be finished (issue #150)."""

from __future__ import annotations

from conftest import current_user, git, run_cli, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger

PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding"
    test: "tests/test_add.py::test_add_two_numbers"
---
# Plan
"""


def ledger(repo):
    return Ledger(gitutil.repo_identity(repo))


def register(repo):
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    return plan


def start(path, plan):
    out = run_cli(path, "run", "start", "--plan", plan)
    assert out["ok"], out
    return out


def outcome(repo, run_id):
    return ledger(repo).one("SELECT outcome FROM run WHERE id = ?", (run_id,))["outcome"]


def last_run_id(repo):
    return ledger(repo).one("SELECT id FROM run ORDER BY id DESC LIMIT 1")["id"]


def add_worktree(repo, path):
    git(repo, "worktree", "add", "-q", "--detach", str(path))
    return path


def remove_worktree(repo, path):
    git(repo, "worktree", "remove", "--force", str(path))


def test_abandon_ends_the_live_run_as_abandoned(repo):
    plan = register(repo)
    start(repo, plan)

    run_cli(repo, "run", "abandon", "--reason", "superseded by #145")

    row = ledger(repo).one("SELECT outcome, ended_at FROM run")
    assert (row["outcome"], row["ended_at"] is not None) == ("abandoned", True)


def test_metrics_reports_the_reason_and_who_abandoned_the_run(repo):
    plan = register(repo)
    start(repo, plan)

    run_cli(repo, "run", "abandon", "--reason", "superseded by #145")

    entry = run_cli(repo, "metrics")["result"]["runs"][0]
    assert entry.get("abandoned") == {
        "reason": "superseded by #145",
        "by": {
            "account": current_user(),
            "executor": "pytest-executor",
            "executor_source": "declared",
        },
    }


def test_abandoning_records_a_human_intervention(repo):
    plan = register(repo)
    start(repo, plan)

    run_cli(repo, "run", "abandon", "--reason", "superseded by #145")

    notes = [r["note"] for r in ledger(repo).all("SELECT note FROM human_intervention")]
    assert notes == ["abandoned: superseded by #145"]


def test_fleet_stops_listing_an_abandoned_run(repo):
    plan = register(repo)
    start(repo, plan)

    run_cli(repo, "run", "abandon", "--reason", "superseded by #145")

    assert run_cli(repo, "fleet", "--json")["result"]["runs"] == []


def test_abandon_by_id_ends_a_run_whose_worktree_is_gone(repo, tmp_path):
    plan = register(repo)
    wt = add_worktree(repo, tmp_path / "wt-a")
    start(wt, plan)
    run_id = last_run_id(repo)
    remove_worktree(repo, wt)

    run_cli(
        repo,
        "run",
        "abandon",
        "--run",
        str(run_id),
        "--reason",
        "worktree removed; superseded by #145",
    )

    assert outcome(repo, run_id) == "abandoned"


def test_a_new_run_starts_in_a_fresh_worktree_after_abandon(repo, tmp_path):
    plan = register(repo)
    wt = add_worktree(repo, tmp_path / "wt-a")
    start(wt, plan)
    run_id = last_run_id(repo)
    remove_worktree(repo, wt)
    run_cli(repo, "run", "abandon", "--run", str(run_id), "--reason", "superseded by #145")

    add_worktree(repo, wt)

    assert run_cli(wt, "run", "start", "--plan", plan)["ok"] is True


def test_abandon_accepts_live_and_blocked_runs_in_every_accepted_form(repo, tmp_path):
    plan = register(repo)

    # (a) a blocked run in the caller's worktree, without --run
    start(repo, plan)
    a_id = last_run_id(repo)
    run_cli(repo, "blocker", "--kind", "tooling", "--detail", "d")
    run_cli(repo, "run", "abandon", "--reason", "blocked for good")

    # (b) a blocked run by --run when its worktree is gone
    wt_b = add_worktree(repo, tmp_path / "wt-b")
    start(wt_b, plan)
    b_id = last_run_id(repo)
    run_cli(wt_b, "blocker", "--kind", "tooling", "--detail", "d")
    remove_worktree(repo, wt_b)
    run_cli(repo, "run", "abandon", "--run", str(b_id), "--reason", "blocked and removed")

    # (c) a live run by --run from its own worktree
    wt_c = add_worktree(repo, tmp_path / "wt-c")
    start(wt_c, plan)
    c_id = last_run_id(repo)
    run_cli(wt_c, "run", "abandon", "--run", str(c_id), "--reason", "own worktree")

    assert [outcome(repo, a_id), outcome(repo, b_id), outcome(repo, c_id)] == [
        "abandoned",
        "abandoned",
        "abandoned",
    ]
