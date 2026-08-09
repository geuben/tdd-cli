"""Adapter contract (§10). Adding an adapter requires no change to core logic."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .. import leases

NOT_FOUND = "not_found"
NOT_COLLECTED = "not_collected"
PASSED = "passed"
FAILED = "failed"


@dataclass
class Verdict:
    project: str
    adapter: str
    target: str | None = None
    target_outcome: str = NOT_FOUND
    target_failure: str = ""
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    duration_ms: int = 0
    error: str | None = None


@dataclass
class GateResult:
    ok: bool
    output: str = ""


@dataclass
class Collection:
    """Per-file collection (R10.3): one uncollectable file must not destroy the set."""

    tests: set[str] = field(default_factory=set)
    failed_files: dict[str, str] = field(default_factory=dict)


def run_command(
    command: str, cwd: Path, timeout: int = 1800,
    extra_env: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    proc = subprocess.run(
        command,
        shell=True,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=None if extra_env is None else {**os.environ, **extra_env},
    )
    return proc.returncode, proc.stdout, proc.stderr


class Adapter:
    name = "base"

    def __init__(self, project, worktree: Path):
        self.project = project
        self.worktree = worktree
        self.root = worktree / project.root

    def qualify(self, raw_id: str) -> str:
        """Namespace a runner-native id with its project (R9.12)."""
        return f"{self.project.name}::{raw_id}"

    def strip(self, qualified: str) -> str:
        prefix = f"{self.project.name}::"
        return qualified[len(prefix):] if qualified.startswith(prefix) else qualified

    def run(self, target: str | None = None) -> Verdict:
        raise NotImplementedError

    def _run_suite(
        self, command: str, extra_env: dict[str, str] | None = None
    ) -> tuple[int, str, str]:
        """Run the suite under a machine-wide worker lease.

        Substituting `{workers}` is opt-in per project; a command without the
        placeholder runs verbatim, so parallelism stays exactly as the project
        declared (§10). TDD_WORKERS is exported either way for commands that
        prefer to read the budget themselves. The lease is held for the whole
        invocation so concurrent agents in other worktrees see this one and
        take a smaller share.
        """
        with leases.worker_lease() as workers:
            return run_command(
                command.replace("{workers}", str(workers)),
                self.root,
                extra_env={"TDD_WORKERS": str(workers), **(extra_env or {})},
            )

    def _test_cmd(self) -> str:
        raise NotImplementedError

    def _suite_invocations(self) -> list[tuple[str, dict[str, str] | None]]:
        """The default suite plus one invocation per declared override (R7.13).

        Runs and collection union these results, so a test reachable only under an
        alternate runner config is still observed — without widening the default
        config, which is exactly the workaround that breaks CI.
        """
        return [(self._test_cmd(), None)] + [
            (ov.test_command, self._override_env(ov)) for ov in self.project.overrides
        ]

    @staticmethod
    def _override_env(override) -> dict[str, str] | None:
        """`${VAR}` references resolve from the environment at invocation time, so a
        port assigned by the harness need not be hard-coded in the reviewed file."""
        if override is None or not override.env:
            return None
        return {k: os.path.expandvars(v) for k, v in override.env.items()}

    def stub_hint(self) -> str:
        """The language idiom for a stub body, quoted into the create_stub directive."""
        return "a body that fails loudly, never working logic"

    def collect(self) -> Collection:
        raise NotImplementedError

    def collectable(self) -> GateResult:
        raise NotImplementedError

    def lint(self) -> GateResult:
        return self._gate(self.project.lint)

    def typecheck(self) -> GateResult:
        return self._gate(self.project.typecheck)

    def _gate(self, commands: list[str]) -> GateResult:
        chunks = []
        for cmd in commands:
            code, out, err = run_command(cmd, self.root)
            if code != 0:
                chunks.append(f"$ {cmd}\n{out}\n{err}".strip())
        return GateResult(ok=not chunks, output="\n\n".join(chunks)[:4000])
