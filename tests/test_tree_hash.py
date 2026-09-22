"""`gitutil.tree_hash` hashes working-tree content under its roots (issue #146)."""

from __future__ import annotations

import os
import time

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


def test_editing_an_untracked_file_changes_the_hash(tmp_path):
    r = _repo(tmp_path)
    (r / "p" / "new.py").write_text("1")
    h1 = gitutil.tree_hash(r, ["p"])
    (r / "p" / "new.py").write_text("2")
    assert gitutil.tree_hash(r, ["p"]) != h1


def test_an_ignored_file_does_not_change_the_hash(tmp_path):
    r = _repo(tmp_path)
    h0 = gitutil.tree_hash(r, ["p"])
    (r / "p" / "x.log").write_text("z")
    assert gitutil.tree_hash(r, ["p"]) == h0


def test_a_change_outside_the_roots_does_not_change_the_hash(tmp_path):
    r = _repo(tmp_path)
    h0 = gitutil.tree_hash(r, ["p"])
    (r / "q" / "b.py").write_text("y = 2\n")
    assert gitutil.tree_hash(r, ["p"]) == h0


def test_hashing_leaves_the_index_untouched(tmp_path):
    r = _repo(tmp_path)
    (r / "p" / "a.py").write_text("x = 9\n")
    (r / "p" / "new.py").write_text("1")
    gitutil.tree_hash(r, ["p"])
    assert git(r, "diff", "--cached", "--name-only") == ""


def test_a_missing_root_hashes_without_error(tmp_path):
    r = _repo(tmp_path)
    assert isinstance(gitutil.tree_hash(r, ["nope"]), str)


def test_the_same_content_hashes_the_same_unstaged_staged_and_committed(tmp_path):
    r = _repo(tmp_path)
    (r / "p" / "a.py").write_text("x = 2\n")
    unstaged = gitutil.tree_hash(r, ["p"])
    git(r, "add", "-A")
    staged = gitutil.tree_hash(r, ["p"])
    git(r, "commit", "-q", "-m", "g")
    committed = gitutil.tree_hash(r, ["p"])
    assert len({unstaged, staged, committed}) == 1


def test_a_repo_with_no_index_yet_hashes_without_error(tmp_path):
    r = tmp_path / "r"
    r.mkdir()
    git(r, "init", "-q")
    (r / "a.py").write_text("x = 1\n")
    assert isinstance(gitutil.tree_hash(r, ["."]), str)


def test_a_same_size_edit_the_stat_cache_cannot_see_still_changes_the_hash(tmp_path):
    """The throwaway index must keep the real index's mtime.

    An entry whose mtime is not older than its index file is "racily clean", and
    git re-reads it rather than trusting stat. Here the entry and the real index
    share one mtime, and the edit keeps the size, inode and mtime (ctime is not
    trusted), so only that racy check can see it. A copy with a fresh mtime makes
    the entry look older than its index, stat is trusted, and the edit is missed.
    """
    r = tmp_path / "r"
    r.mkdir()
    git(r, "init", "-q")
    git(r, "config", "user.email", "t@example.com")
    git(r, "config", "user.name", "T")
    git(r, "config", "core.trustctime", "false")
    (r / "p").mkdir()
    a = r / "p" / "a.py"
    a.write_text("x = 1\n")
    past = time.time_ns() - 100 * 10**9
    os.utime(a, ns=(past, past))
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "init")
    os.utime(r / ".git" / "index", ns=(past, past))
    before = gitutil.tree_hash(r, ["p"])

    a.write_text("x = 2\n")
    os.utime(a, ns=(past, past))

    assert gitutil.tree_hash(r, ["p"]) != before
