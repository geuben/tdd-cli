"""The agent harnesses `tdd init --skill` can scaffold.

A closed set, unlike adapters: an adapter loads code, a harness is only data —
the shipped files to copy out and where they go. Copied, never referenced in
place, so a project commits no path into somebody's site-packages.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scaffold:
    #: Repository-relative path of the shipped copy — and, verbatim, its path under `_docs`.
    source: str
    #: Worktree-relative path init writes it to.
    dest: str


@dataclass(frozen=True)
class Harness:
    name: str
    files: tuple[Scaffold, ...]


HARNESSES: dict[str, Harness] = {
    "claude-code": Harness(
        "claude-code",
        (Scaffold("examples/skills/tdd-drive/SKILL.md", ".claude/skills/tdd-drive/SKILL.md"),),
    ),
}
