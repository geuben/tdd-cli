from __future__ import annotations

from pathlib import Path

from .base import Adapter, Collection, GateResult, Verdict
from .pytest_adapter import PytestAdapter
from .vitest_adapter import VitestAdapter

REGISTRY: dict[str, type[Adapter]] = {
    "pytest": PytestAdapter,
    "vitest": VitestAdapter,
}


def build(project, worktree: Path) -> Adapter:
    try:
        cls = REGISTRY[project.adapter]
    except KeyError:
        raise RuntimeError(
            f"unknown adapter {project.adapter!r}; available: {sorted(REGISTRY)}"
        ) from None
    return cls(project, worktree)


__all__ = ["Adapter", "Collection", "GateResult", "Verdict", "REGISTRY", "build"]
