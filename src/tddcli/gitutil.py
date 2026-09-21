"""Git access. Every call is explicit about its worktree; nothing is resolved from cwd."""

from __future__ import annotations

import contextlib
import hashlib
from collections.abc import Generator, Sequence
from pathlib import Path

from . import actor


class GitError(RuntimeError):
    pass


def git(worktree: Path, *args: str, check: bool = True, env: dict[str, str] | None = None) -> str:
    argv = ["git", "-C", str(worktree), *args]
    if env:
        # On the command line, not in the process environment: a SudoActor with no
        # agent environment runs `sudo -H`, which resets the environment, and a lost
        # GIT_INDEX_FILE would point `git add` at the agent's real index.
        argv = ["env", *(f"{k}={v}" for k, v in env.items()), *argv]
    proc = actor.current().run_argv(argv)
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
    """Hash of working-tree content under the given roots: tracked and untracked,
    ignored files excluded. Independent of index and commit state, so the same
    content hashes the same before and after it is staged or committed.

    Backs `no_change_since_last_run` (§6) and the refactor-phase skip (§6.1).

    The content is read by `git add -A` into a throwaway index, seeded from the
    real one (mtime included) so git's stat cache spares unchanged files a
    re-hash. The real index is never touched: staging derives commits from it.
    `GIT_INDEX_FILE` must be absolute, since `git -C` moves the cwd. `add` takes
    no pathspec, because a root that exists neither on disk nor in the index is
    a pathspec error, and an artifact path is hashed before `regenerate` may have
    created it.
    """
    real_index = Path(
        git(worktree, "rev-parse", "--path-format=absolute", "--git-path", "index").strip()
    )
    h = hashlib.sha256()
    with tempfile.TemporaryDirectory(prefix="tdd-tree-hash-") as tmp:
        index = Path(tmp) / "index"
        if real_index.is_file():
            # copy2, not copyfile: the copy must keep the real index's mtime. Git
            # re-reads any entry not older than its index file ("racy git"); a fresh
            # mtime would let a same-size edit made in the same second pass as clean.
            shutil.copy2(real_index, index)
        env = {"GIT_INDEX_FILE": str(index.resolve())}
        git(worktree, "add", "-A", env=env)
        for root in sorted(roots):
            h.update(root.encode())
            h.update(git(worktree, "ls-files", "-s", "--", root, env=env).encode())
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


@contextlib.contextmanager
def temporary_worktree(
    worktree: Path, sha: str, link_ignored_under: Sequence[str] = ()
) -> Generator[Path, None, None]:
    tmp_dir = actor.current().make_temp_dir("tdd-probe-")
    try:
        git(worktree, "worktree", "add", "--detach", str(tmp_dir), sha)
        for root in link_ignored_under:
            root_path = worktree / root
            listing = git(
                worktree, "ls-files", "-o", "-i", "--exclude-standard", "--directory", "--", root
            )
            for entry in listing.splitlines():
                entry = entry.rstrip("/")
                rel = entry[len(root) + 1 :] if entry.startswith(root + "/") else entry
                if not rel or "/" in rel:
                    continue
                src = root_path / rel
                dst = tmp_dir / root / rel
                if dst.exists() or dst.is_symlink():
                    continue
                try:
                    actor.current().link(src, dst)
                except OSError:
                    pass
        yield tmp_dir
    finally:
        try:
            git(worktree, "worktree", "remove", "--force", str(tmp_dir))
        except GitError:
            pass
        actor.current().remove_tree(tmp_dir)
