"""The machine-level runner config, and the role this process takes from it."""

from __future__ import annotations

from dataclasses import dataclass


class RunnerConfigError(RuntimeError):
    pass


@dataclass
class RunnerConfig:
    pass


def load() -> RunnerConfig | None:
    raise NotImplementedError
