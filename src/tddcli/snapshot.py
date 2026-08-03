"""Working-tree snapshots for sensitivity checks (§8.4, R8.5).

Restoration must return the tree to its *pre-mutation* state, never to HEAD: at a
passed-on-arrival the RED test is written but uncommitted, so the tree is legitimately
dirty and `git checkout --` would destroy it. Untracked files cannot be restored by
git at all, so contents are captured directly.

Build output is excluded throughout — a suite run between `begin` and `end` rewrites
`.pyc` files, and comparing those would make every verification fail.
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from . import gitutil
from .config import Config

MAX_CAPTURE_BYTES = 4 * 1024 * 1024


def authored_dirty(worktree: Path, config: Config) -> set[str]:
    return {p for p in gitutil.dirty_paths(worktree) if not config.is_ignored(p)}


def _read(worktree: Path, rel: str) -> bytes | None:
    path = worktree / rel
    if not path.is_file():
        return None
    if path.stat().st_size > MAX_CAPTURE_BYTES:
        return None
    return path.read_bytes()


def capture(worktree: Path, config: Config) -> str:
    """Snapshot every non-ignored dirty path, contents included."""
    entries = {}
    for rel in sorted(authored_dirty(worktree, config)):
        data = _read(worktree, rel)
        entries[rel] = (
            None if data is None else base64.b64encode(data).decode("ascii")
        )
    return json.dumps({"files": entries})


def fingerprint(worktree: Path, config: Config) -> str:
    h = hashlib.sha256()
    for rel in sorted(authored_dirty(worktree, config)):
        h.update(rel.encode())
        data = _read(worktree, rel)
        h.update(hashlib.sha256(data).digest() if data is not None else b"missing")
    return h.hexdigest()


def restore(worktree: Path, config: Config, snapshot_json: str) -> list[str]:
    """Return the tree to the captured state. Returns the paths acted on."""
    saved = json.loads(snapshot_json)["files"]
    touched: list[str] = []

    for rel in sorted(authored_dirty(worktree, config)):
        if rel in saved:
            continue
        # Dirty now, clean when captured: revert it, or remove it if it is new.
        path = worktree / rel
        tracked = bool(
            gitutil.git(worktree, "ls-files", "--", rel, check=False).strip()
        )
        if tracked:
            gitutil.checkout_paths(worktree, [rel])
        elif path.is_file():
            path.unlink()
        touched.append(rel)

    for rel, encoded in saved.items():
        path = worktree / rel
        if encoded is None:
            if path.is_file():
                path.unlink()
                touched.append(rel)
            continue
        data = base64.b64decode(encoded)
        if not path.is_file() or path.read_bytes() != data:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            touched.append(rel)

    return sorted(set(touched))
