"""`gitutil.tree_hash` hashes working-tree content under its roots (issue #146)."""

from __future__ import annotations

from conftest import git
from tddcli import gitutil


def _repo(tmp_path):
    """A committed repo with two roots, `p` and `q`, and `*.log` ignored."""
    r = tmp_path / "r"
    r.mkdir()
    git(r, "init", "-q")
    git(r, "config", "user.email", "t@example.com")
    git(r, "config", "user.name", "T")
    (r / "p").mkdir()
    (r / "q").mkdir()
    (r / "p" / "a.py").write_text("x = 1\n")
    (r / "q" / "b.py").write_text("y = 1\n")
    (r / ".gitignore").write_text("*.log\n")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "init")
    return r


def test_deleting_a_tracked_file_changes_the_hash(tmp_path):
    r = _repo(tmp_path)
    h0 = gitutil.tree_hash(r, ["p"])
    (r / "p" / "a.py").unlink()
    assert gitutil.tree_hash(r, ["p"]) != h0
