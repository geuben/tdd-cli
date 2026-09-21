"""Who acts in the agent's territory.

Everything the tool does outside its own state — spawning suites, gates, hooks and
git — goes through the actor installed here, and nothing else in the package may
spawn a process (`tests/test_actor_seams.py` holds that line). On a single-user
machine the actor is the process itself. In split mode (issue 142) the runner's uid
must never execute the agent's code as itself, so a different actor is installed.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Sequence
from pathlib import Path


class LocalActor:
    """Acts as the current process: a single-user machine, and a client's local verbs."""

    def run_argv(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        timeout: int | None = None,
        input: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(argv),
            cwd=None if cwd is None else str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            input=input,
            env=self._env(env),
        )

    def run_shell(
        self,
        command: str,
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=self._env(env),
        )

    @staticmethod
    def _env(extra: dict[str, str] | None) -> dict[str, str] | None:
        """`extra` is laid over the inherited environment, never in place of it."""
        return None if extra is None else {**os.environ, **extra}


_current: LocalActor = LocalActor()


def current() -> LocalActor:
    return _current


def install(actor: LocalActor) -> None:
    global _current
    _current = actor
