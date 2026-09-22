"""Who acts in the agent's territory.

Everything the tool does outside its own state — spawning suites, gates, hooks and
git — goes through the actor installed here, and nothing else in the package may
spawn a process (`tests/test_actor_seams.py` holds that line). On a single-user
machine the actor is the process itself. In split mode (issue 142) the runner's uid
must never execute the agent's code as itself, so a different actor is installed.
"""

from __future__ import annotations

import base64
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from . import agentfs


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

    def relay(self, argv: Sequence[str], *, input: str) -> subprocess.CompletedProcess[str]:
        """Run a command whose answer is ours to pass on: stdout is captured so the
        caller can print it, stderr is inherited so its heartbeats stay live."""
        return subprocess.run(list(argv), stdout=subprocess.PIPE, text=True, input=input)

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
        # `-n`: a sudo that prompts would hang an unattended agent. With the agent's
        # environment in hand, `-E` passes exactly that; with none, sudo resets to the
        # agent's own, and `-H` stops macOS leaving `HOME` at the runner's.
        keep = "-H" if self.agent_env is None else "-E"
        wrapped = [self.sudo, "-n", keep, "-u", self.agent, "--", *argv]
        return super().run_argv(wrapped, cwd=cwd, env=env, timeout=timeout, input=input)

    def run_shell(self, command, *, cwd, env=None, timeout=None):
        return self.run_argv(["/bin/sh", "-c", command], cwd=cwd, env=env, timeout=timeout)

    def _env(self, extra):  # type: ignore[override]
        """The agent's environment, never the runner's: `-E` hands sudo exactly this."""
        if self.agent_env is None:
            return super()._env(extra)
        return {**self.agent_env, **(extra or {})}

    def _agentfs(self, op: str, *args: object, input: str | None = None):
        """One file operation, in a helper process that is the agent."""
        argv = [sys.executable, "-m", "tddcli.agentfs", op, *(str(a) for a in args)]
        proc = self.run_argv(argv, input=input)
        if proc.returncode not in (0, agentfs.MISSING):
            raise OSError(f"agentfs {op} {' '.join(map(str, args))}: {proc.stderr.strip()}")
        return proc

    def read_text(self, path):
        proc = self._agentfs("read", path)
        return None if proc.returncode == agentfs.MISSING else proc.stdout

    def write_file(self, path, data):
        self._agentfs("write", path, input=base64.b64encode(data).decode())

    def remove_file(self, path):
        self._agentfs("unlink", path)

    def make_temp_dir(self, prefix):
        return Path(self._agentfs("mkdtemp", prefix).stdout)

    def remove_tree(self, path):
        self._agentfs("rmtree", path)

    def link(self, src, dst):
        self._agentfs("symlink", src, dst)


_current: LocalActor = LocalActor()


def current() -> LocalActor:
    return _current


def install(actor: LocalActor) -> None:
    global _current
    _current = actor
