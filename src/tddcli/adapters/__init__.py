from __future__ import annotations

import importlib.metadata
from pathlib import Path

from .base import Adapter, Collection, GateResult, Verdict
from .exec_adapter import ExecAdapter
from .gradle_adapter import GradleAdapter
from .pytest_adapter import PytestAdapter
from .vitest_adapter import VitestAdapter
from .xctest_adapter import XCTestAdapter

REGISTRY: dict[str, type[Adapter]] = {
    "exec": ExecAdapter,
    "gradle": GradleAdapter,
    "pytest": PytestAdapter,
    "vitest": VitestAdapter,
    "xctest": XCTestAdapter,
}


def _entry_points():
    """Third-party adapters, published under the `tddcli.adapters` entry-point group.

    A separate seam so tests can substitute fake entry points without installing a
    distribution. Loading is deferred to `build`: enumerating names must stay cheap
    (doctor lists them), and a broken plugin must not break projects that never
    reference it.
    """
    return importlib.metadata.entry_points(group="tddcli.adapters")


def available() -> set[str]:
    """Every adapter name that `build` could resolve, built-in or plugin."""
    return set(REGISTRY) | {ep.name for ep in _entry_points()}


def build(project, worktree: Path) -> Adapter:
    # Built-ins always win: a plugin must not be able to shadow `pytest` and
    # change what observed test execution means for every existing config.
    cls = REGISTRY.get(project.adapter)
    if cls is None:
        for ep in _entry_points():
            if ep.name == project.adapter:
                cls = ep.load()
                break
    if cls is None:
        raise RuntimeError(f"unknown adapter {project.adapter!r}; available: {sorted(available())}")
    return cls(project, worktree)


__all__ = ["Adapter", "Collection", "GateResult", "Verdict", "REGISTRY", "available", "build"]
