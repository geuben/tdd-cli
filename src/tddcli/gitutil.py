"""Git access. Every call is explicit about its worktree; nothing is resolved from cwd."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


def git(worktree: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", "-C", str(worktree), *args],
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def worktree_root(start: Path) -> Path:
    out = git(start, "rev-parse", "--show-toplevel").strip()
    if not out:
        raise GitError(f"not a git worktree: {start}")
    return Path(out).resolve()


def repo_identity(worktree: Path) -> Path:
    """The canonical repository path — the *common* git dir, shared by all worktrees.

    R13.3: the ledger is keyed by this, not by the worktree, so pruning a worktree
    never orphans its runs.
    """
    common = git(worktree, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
    return Path(common).resolve().parent


def head(worktree: Path) -> str:
    return git(worktree, "rev-parse", "HEAD").strip()


def blob_sha_at_head(worktree: Path, rel_path: str) -> tuple[str, str]:
    """(blob_sha, commit_sha) for a path as committed — never the working-tree copy."""
    commit = head(worktree)
    out = git(worktree, "rev-parse", f"HEAD:{rel_path}", check=False).strip()
    if not out or " " in out:
        raise GitError(f"{rel_path} is not committed at HEAD")
    return out, commit


def show_at_head(worktree: Path, rel_path: str) -> str:
    return git(worktree, "show", f"HEAD:{rel_path}")


def tracked_at_head(worktree: Path, paths: list[str]) -> set[str]:
    """Which of `paths` exist in the HEAD commit — so a path absent here is a new file."""
    if not paths:
        return set()
    out = git(worktree, "ls-tree", "-r", "--name-only", "-z", "HEAD", "--", *paths)
    return {p for p in out.split("\0") if p}


def status_porcelain(worktree: Path) -> list[tuple[str, str]]:
    out = git(worktree, "status", "--porcelain=v1", "-uall")
    entries = []
    for line in out.splitlines():
        if not line.strip():
            continue
        entries.append((line[:2], line[3:].strip()))
    return entries


def is_dirty(worktree: Path) -> bool:
    return bool(status_porcelain(worktree))


def dirty_paths(worktree: Path) -> set[str]:
    return {path for _, path in status_porcelain(worktree)}


def changed_paths(worktree: Path) -> set[str]:
    """Tracked modifications plus untracked files, relative to the worktree root."""
    return dirty_paths(worktree)


def diff_text(worktree: Path) -> str:
    return git(worktree, "diff")


def tree_hash(worktree: Path, roots: list[str]) -> str:
    """Hash of tracked content under the given roots, plus untracked file contents.

    Backs `no_change_since_last_run` (§6) and the refactor-phase skip (§6.1).
    """
    h = hashlib.sha256()
    for root in sorted(roots):
        h.update(root.encode())
        h.update(git(worktree, "ls-files", "-s", "--", root).encode())
        diff = git(worktree, "diff", "--", root)
        h.update(diff.encode())
        untracked = git(worktree, "ls-files", "-o", "--exclude-standard", "--", root)
        for rel in sorted(untracked.split()):
            h.update(rel.encode())
            p = worktree / rel
            if p.is_file():
                h.update(p.read_bytes())
    return h.hexdigest()


def add(worktree: Path, paths: list[str]) -> None:
    if paths:
        git(worktree, "add", "--", *paths)


def reset_index(worktree: Path) -> None:
    git(worktree, "reset", "-q")


def commit(worktree: Path, message: str, trailers: dict[str, str]) -> str:
    body = message
    if trailers:
        body += "\n\n" + "\n".join(f"{k}: {v}" for k, v in trailers.items())
    git(worktree, "commit", "-q", "-m", body)
    return head(worktree)


def checkout_paths(worktree: Path, paths: list[str]) -> None:
    if paths:
        git(worktree, "checkout", "--", *paths)


def staged_paths(worktree: Path) -> list[str]:
    out = git(worktree, "diff", "--cached", "--name-only")
    return [p for p in out.splitlines() if p.strip()]
