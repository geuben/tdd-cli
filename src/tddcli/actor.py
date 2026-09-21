"""Who acts in the agent's territory.

Everything the tool does outside its own state — spawning suites, gates, hooks and
git — goes through the actor installed here, and nothing else in the package may
spawn a process (`tests/test_actor_seams.py` holds that line). On a single-user
machine the actor is the process itself. In split mode (issue 142) the runner's uid
must never execute the agent's code as itself, so a different actor is installed.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
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

    def read_text(self, path: Path) -> str | None:
        """None when the file is missing: callers ask "did it get written?" by reading."""
        try:
            return Path(path).read_text()
        except FileNotFoundError:
            return None

    def write_file(self, path: Path, data: bytes) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def remove_file(self, path: Path) -> None:
        Path(path).unlink(missing_ok=True)

    def make_temp_dir(self, prefix: str) -> Path:
        return Path(tempfile.mkdtemp(prefix=prefix))

    def remove_tree(self, path: Path) -> None:
        shutil.rmtree(path, ignore_errors=True)

    def link(self, src: Path, dst: Path) -> None:
        dst = Path(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.symlink_to(src)

    @staticmethod
    def _env(extra: dict[str, str] | None) -> dict[str, str] | None:
        """`extra` is laid over the inherited environment, never in place of it."""
        return None if extra is None else {**os.environ, **extra}


class SudoActor(LocalActor):
    """Acts as the agent, from a runner that is a different uid."""

    def __init__(self, sudo: str, agent: str, env: dict[str, str] | None):
        self.sudo = sudo
        self.agent = agent
        self.agent_env = env

    def run_argv(self, argv, *, cwd=None, env=None, timeout=None, input=None):
        # `-n`: a sudo that prompts would hang an unattended agent.
        wrapped = [self.sudo, "-n", "-E", "-u", self.agent, "--", *argv]
        return super().run_argv(wrapped, cwd=cwd, env=env, timeout=timeout, input=input)

    def run_shell(self, command, *, cwd, env=None, timeout=None):
        return self.run_argv(["/bin/sh", "-c", command], cwd=cwd, env=env, timeout=timeout)

    def _env(self, extra):  # type: ignore[override]
        """The agent's environment, never the runner's: `-E` hands sudo exactly this."""
        if self.agent_env is None:
            return super()._env(extra)
        return {**self.agent_env, **(extra or {})}

    def read_text(self, path):
        raise NotImplementedError

    def write_file(self, path, data):
        raise NotImplementedError

    def remove_file(self, path):
        raise NotImplementedError

    def make_temp_dir(self, prefix):
        raise NotImplementedError

    def remove_tree(self, path):
        raise NotImplementedError

    def link(self, src, dst):
        raise NotImplementedError


_current: LocalActor = LocalActor()


def current() -> LocalActor:
    return _current


def install(actor: LocalActor) -> None:
    global _current
    _current = actor
