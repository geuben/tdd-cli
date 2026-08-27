"""Staging and commits, derived from the phase being left (§9.5).

The tool stages; agents never do. `git add -A` is never used.

R9.14 falls out of this for free: if the RED commit's staged set would contain a file
that is neither a test nor a declared stub, that *is* implementation written during
RED — detected exactly, in every language, without parsing a line of source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import gitutil
from .config import Config
from .contract import DeclaredCycle

RED = "red"
GREEN = "green"
REFACTOR = "refactor"
PIN = "pin"


@dataclass
class Classification:
    tests: list[str] = field(default_factory=list)
    stubs: list[str] = field(default_factory=list)
    implementation: list[str] = field(default_factory=list)
    generated: list[str] = field(default_factory=list)
    outside: list[str] = field(default_factory=list)      # outside every project root
    excluded: list[str] = field(default_factory=list)     # pre-existing dirt (R9.21)
    ignored: list[str] = field(default_factory=list)      # build output; never authored
    ancillary: list[str] = field(default_factory=list)    # plan-declared cross-project paths

    @property
    def undeclared_impl(self) -> list[str]:
        return self.implementation

    def adopt_stubs(self, paths: list[str]) -> None:
        """Move tool-sanctioned stubs out of implementation and into the RED commit.

        The plan declares stubs it foresaw; this covers the ones the *tool* demanded
        after an uncollectable target (R9.14) — leaving them classified as
        implementation would report the agent for doing exactly as it was told.
        """
        chosen = set(paths)
        self.implementation = [p for p in self.implementation if p not in chosen]
        self.stubs = sorted(set(self.stubs) | chosen)


def classify(
    config: Config,
    changed: set[str],
    cycle_projects: list[str],
    declared: DeclaredCycle | None,
    excluded: set[str],
    ancillary: set[str] | None = None,
) -> Classification:
    out = Classification()
    stub_set = set(declared.stub_expected) if declared else set()
    roots = {config.project(p).root for p in cycle_projects}

    for rel in sorted(changed):
        if config.is_ignored(rel):            # build output is never authored
            out.ignored.append(rel)
            continue
        if rel in excluded:
            out.excluded.append(rel)
            continue
        if config.is_generated(rel):          # R7.7
            out.generated.append(rel)
            continue
        owner = config.owning_project(rel)
        if owner is None or owner.root not in roots:
            out.outside.append(rel)
            continue
        if owner.is_test_file(rel):
            out.tests.append(rel)
        elif rel in stub_set or owner.relative_to_root(rel) in stub_set:
            out.stubs.append(rel)
        else:
            out.implementation.append(rel)
    return out


def paths_for_phase(phase: str, classification: Classification) -> list[str]:
    if phase == RED:
        return sorted(classification.tests + classification.stubs)
    if phase == PIN:
        return sorted(classification.tests)
    # GREEN and REFACTOR take everything authored inside the cycle's projects.
    return sorted(
        classification.tests + classification.stubs + classification.implementation
    )


def default_message(phase: str, declared: DeclaredCycle | None, ordinal: int) -> str:
    if declared and phase in declared.commit_messages:
        return declared.commit_messages[phase]
    title = (declared.title if declared else "") or f"cycle {ordinal}"
    return {
        RED: f"test: {title}",
        PIN: f"test: pin {title}",
        GREEN: f"feat: {title}",
        REFACTOR: f"refactor: {title}",
    }[phase]


def commit(
    worktree: Path,
    paths: list[str],
    message: str,
    trailers: dict[str, str],
) -> tuple[str | None, list[str]]:
    """Stage exactly `paths` and commit. Returns (sha, staged) — (None, []) if empty."""
    gitutil.reset_index(worktree)
    if not paths:
        return None, []
    gitutil.add(worktree, paths)
    staged = gitutil.staged_paths(worktree)
    if not staged:
        return None, []
    sha = gitutil.commit(worktree, message, trailers)
    return sha, staged


def commit_generated(
    worktree: Path, paths: list[str], artifact: str, trailers: dict[str, str]
) -> tuple[str | None, list[str]]:
    """R9.20 — regenerated output lands in its own commit, separately reviewable."""
    return commit(worktree, paths, f"chore({artifact}): regenerate", trailers)
