"""Git lookups that share one process answer what separate calls answered."""

from __future__ import annotations

import pytest

from conftest import git, run_cli, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger

PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
---

# Plan
"""


def test_locate_from_a_subdirectory_names_the_worktree_and_the_repository(repo):
    assert gitutil.locate(repo / "backend" / "app") == (
        gitutil.worktree_root(repo),
        gitutil.repo_identity(repo),
    )


def test_locate_in_a_linked_worktree_keys_by_the_main_repository(repo, tmp_path):
    linked = tmp_path / "linked"
    git(repo, "worktree", "add", "-q", str(linked))
    assert gitutil.locate(linked) == (linked.resolve(), repo.resolve())


def test_locate_outside_a_repository_fails(tmp_path):
    with pytest.raises(gitutil.GitError):
        gitutil.locate(tmp_path)


def test_locate_refuses_an_empty_toplevel(tmp_path, monkeypatch):
    monkeypatch.setattr(gitutil, "git", lambda *a, **k: "\n/somewhere/.git\n")
    with pytest.raises(gitutil.GitError, match="not a git worktree"):
        gitutil.locate(tmp_path)


def test_blob_sha_at_head_is_the_blob_and_the_commit_git_reports(repo):
    plan = write_plan(repo, PLAN)
    assert gitutil.blob_sha_at_head(repo, plan) == (
        git(repo, "rev-parse", f"HEAD:{plan}").strip(),
        git(repo, "rev-parse", "HEAD").strip(),
    )


def test_blob_sha_at_head_without_a_commit_fails(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "plan.md").write_text("x\n")
    with pytest.raises(gitutil.GitError):
        gitutil.blob_sha_at_head(tmp_path, "plan.md")


@pytest.mark.parametrize(
    "output",
    [
        pytest.param("HEAD\n" + "a" * 40 + "\n", id="head-unresolved"),
        pytest.param("a" * 40 + "\n", id="blob-line-missing"),
    ],
)
def test_blob_sha_at_head_refuses_output_missing_either_sha(tmp_path, monkeypatch, output):
    monkeypatch.setattr(gitutil, "git", lambda *a, **k: output)
    with pytest.raises(gitutil.GitError):
        gitutil.blob_sha_at_head(tmp_path, "plan.md")


def test_run_start_records_the_head_when_the_plan_blob_cannot_be_read(repo, monkeypatch):
    plan = write_plan(repo, PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]

    def unreadable(worktree, rel):
        raise gitutil.GitError("unreadable")

    monkeypatch.setattr(gitutil, "blob_sha_at_head", unreadable)
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out
    row = Ledger(gitutil.repo_identity(repo)).one(
        "SELECT start_sha FROM run WHERE id = ?", (out["run"]["id"],)
    )
    assert row["start_sha"] == gitutil.head(repo)
