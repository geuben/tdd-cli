"""Adapter contract (§10). Adding an adapter requires no change to core logic."""

from __future__ import annotations

import os
import subprocess
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .. import leases
from ..envelope import heartbeat

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


def _suite_overlap(suite_ids: list[set[str]]) -> list[str]:
    """Test ids observed by more than one suite invocation of the union (R7.13).
    Overlap means the default command's discovery reaches files an override
    owns, so those tests also ran without the override's command/env — and
    target matching would judge the target by whichever run came first."""
    counts = Counter(i for ids in suite_ids for i in ids)
    return sorted(i for i, n in counts.items() if n > 1)


def _overlap_error(overlap: list[str]) -> str:
    shown = ", ".join(overlap[:5])
    more = f" (and {len(overlap) - 5} more)" if len(overlap) > 5 else ""
    return (
        f"observed by more than one suite invocation: {shown}{more}."
        " The default suite's discovery reaches files an override owns, so"
        " these tests also ran without the override's command/env. Scope the"
        " default test_command so it cannot reach them (e.g. pass the default"
        " test directories explicitly)."
    )


def clip_failure(text: str, limit: int = 1500) -> str:
    """Clip failure text to `limit`, keeping both ends. Python puts the actual
    error at the tail of a traceback, so a head-only cut on a deep stack
    (async frameworks, ORMs, HTTP clients) delivered framework frames and cut
    exactly the line that says what went wrong — forcing a re-run outside tdd
    to see an error the tool already had. The head is kept too: for a plain
    assertion failure the first line carries the assertion itself."""
    if len(text) <= limit:
        return text
    head = limit // 5
    tail = limit - head
    return f"{text[:head]}\n… [clipped] …\n{text[-tail:]}"


#: Opt-in per-command timing. Off by default: the per-file collect loop would emit
#: one line per test file on every invocation, drowning the heartbeats that exist
#: to make a slow baseline legible.
TIMING_ENV = "TDD_TIMING"


def run_command(
    command: str,
    cwd: Path,
    timeout: int = 1800,
    extra_env: dict[str, str] | None = None,
    label: str | None = None,
) -> tuple[int, str, str]:
    """Every subprocess the tool spawns passes through here, which makes it the one
    place worth timing: suite runs, per-file collection, lint and typecheck gates,
    doctor probes, artifact hooks.

    `label` is what makes the rows groupable. This function sees a command string
    and a cwd — not which project or phase asked for it — so an unlabelled timing
    is readable by a human and useless to a query.
    """
    started = time.monotonic()
    proc = subprocess.run(
        command,
        shell=True,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=None if extra_env is None else {**os.environ, **extra_env},
    )
    if os.environ.get(TIMING_ENV):
        heartbeat(
            event="command_timing",
            label=label,
            command=command,
            cwd=str(cwd),
            duration_ms=int((time.monotonic() - started) * 1000),
            exit_code=proc.returncode,
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
        return qualified[len(prefix) :] if qualified.startswith(prefix) else qualified

    def normalise_id(self, test_id: str) -> str:
        """Return the canonical form of a declared target id for matching against collected ids.

        The default is an identity — subclasses override when the runner's collected
        ids differ from a natural human spelling (e.g. vitest's describe/test separator).
        """
        return test_id

    def run(self, target: str | None = None) -> Verdict:
        raise NotImplementedError

    def _run_suite(
        self,
        command: str,
        extra_env: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> tuple[int, str, str]:
        """Run the suite under a machine-wide worker lease.

        Substituting `{workers}` is opt-in per project; a command without the
        placeholder runs verbatim, so parallelism stays exactly as the project
        declared (§10). TDD_WORKERS is exported either way for commands that
        prefer to read the budget themselves. The lease is held for the whole
        invocation so concurrent agents in other worktrees see this one and
        take a smaller share.

        When the project declares `lease`, an exclusive named lease is acquired
        first (outer context), so only one instance of that suite runs machine-
        wide at a time. When `timeout` is given it overrides the project-level
        and default values.
        """
        effective_timeout = timeout or self.project.timeout or 1800

        def _run(workers: int) -> tuple[int, str, str]:
            return run_command(
                command.replace("{workers}", str(workers)),
                self.root,
                timeout=effective_timeout,
                extra_env={"TDD_WORKERS": str(workers), **(extra_env or {})},
                label="suite",
            )

        lease_name = getattr(self.project, "lease", None)
        if lease_name:
            with leases.named_lease(lease_name):
                with leases.worker_lease() as workers:
                    return _run(workers)
        else:
            with leases.worker_lease() as workers:
                return _run(workers)

    def _test_cmd(self) -> str:
        raise NotImplementedError

    def _suite_invocations(self) -> list[tuple[str, dict[str, str] | None]]:
        """The default suite plus one invocation per declared override (R7.13).

        Runs and collection union these results, so a test reachable only under an
        alternate runner config is still observed — without widening the default
        config, which is exactly the workaround that breaks CI.
        """
        return [(self._test_cmd(), self._suite_env(None))] + [
            (ov.test_command, self._suite_env(ov)) for ov in self.project.overrides
        ]

    def _suite_env(self, override) -> dict[str, str] | None:
        """The environment for one suite invocation: the project's `env`, with the
        owning override's layered on top (None means the default suite). `${VAR}`
        references resolve from the environment at invocation time, so a port
        assigned per checkout need not be hard-coded in the reviewed file."""
        merged = {**self.project.env, **(override.env if override else {})}
        if not merged:
            return None
        return {k: os.path.expandvars(v) for k, v in merged.items()}

    def stub_hint(self) -> str:
        """The language idiom for a stub body, quoted into the create_stub directive."""
        return "a body that fails loudly, never working logic"

    def collect(self) -> Collection:
        """Enumerate the project's tests: one invocation per declared suite, with
        the per-file loop kept for what that cannot account for (issue #27).

        Per file, collection cost scaled with *file count* rather than test count —
        measured at 77% of a whole `run start`, against a floor of ~1.08s per
        invocation that is the environment manager resolving plus the runner
        booting, not collection work.

        The batch and the loop do not discover the same way: a batch uses the
        runner's own config, the loop walks `test_paths`. So the loop still runs for
        every file the batch did not report — whether the batch failed, returned
        nothing, or simply never mentioned that file. R10.3's guarantee is
        unchanged: one uncollectable file is attributed to itself, and cannot
        destroy the set. What changes is that the healthy case no longer pays for
        the broken one.
        """
        result = Collection()
        unaccounted = {str(p.relative_to(self.root)) for p in self._test_files()}
        for command, env in self._collect_invocations():
            batch = self._collect_batch(command, env)
            if batch is None:
                continue
            tests, files = batch
            result.tests |= tests
            unaccounted -= files
        return self._collect_per_file(unaccounted, result)

    def _collect_invocations(self) -> list[tuple[str, dict[str, str] | None]]:
        """One collection command per declared suite: the default plus each
        override's (R7.13), so an override's files are enumerated with its own
        command and env."""
        raise NotImplementedError

    def _collect_batch(
        self, command: str, env: dict[str, str] | None
    ) -> tuple[set[str], set[str]] | None:
        """`(test ids, files seen)` for one whole-suite invocation, or None when it
        produced nothing usable — the signal to leave its files to the loop."""
        raise NotImplementedError

    def _collect_per_file(self, rels: set[str], result: Collection) -> Collection:
        """R10.3's loop, now reached only for files no batch accounted for."""
        raise NotImplementedError

    def collectable(self) -> GateResult:
        raise NotImplementedError

    def override_isolation(self) -> GateResult:
        """Whether the default suite's discovery stays out of files an override
        owns (R7.13's premise). Overlap means runs observe those tests without
        the override's command/env — and the union then holds the same test
        twice with conflicting outcomes. Adapters with a way to probe discovery
        override this; the base answer is ok so third-party adapters without a
        probe don't fail doctor."""
        return GateResult(ok=True)

    def lint(self) -> GateResult:
        return self._gate(self.project.lint)

    def typecheck(self) -> GateResult:
        return self._gate(self.project.typecheck)

    def _gate(self, commands: list[str]) -> GateResult:
        chunks = []
        for cmd in commands:
            code, out, err = run_command(cmd, self.root, label="gate")
            if code != 0:
                chunks.append(f"$ {cmd}\n{out}\n{err}".strip())
        return GateResult(ok=not chunks, output="\n\n".join(chunks)[:4000])
