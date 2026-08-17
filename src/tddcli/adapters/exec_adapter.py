"""exec adapter — exit-code oracles as first-class tests (§10).

Each file matching `test_paths` is one test; the verdict is the exit code.
No output parsing, no runner protocol. Any toolchain can be bootstrapped by
wrapping its runner in a script before (or instead of) a native adapter
existing; shell-gate TDD cycles (write a failing check, migrate code until it
exits 0) use this adapter natively.

Collection is a filesystem walk — no subprocess needed.  A file that is
matched by `test_paths` but cannot be run (not executable, no `test_command`)
maps to `not_collected` rather than `failed`, preserving the "a broken oracle
is not RED" semantics the other adapters uphold via import errors.
"""

from __future__ import annotations

import os
import shlex
import time
from pathlib import Path

from .base import (
    FAILED,
    NOT_COLLECTED,
    PASSED,
    Adapter,
    Collection,
    GateResult,
    Verdict,
    clip_failure,
    run_command,
)


class ExecAdapter(Adapter):
    name = "exec"

    def stub_hint(self) -> str:
        return "a script body that exits non-zero (e.g. `exit 1` with a message explaining what is missing)"

    # ------------------------------------------------------------------
    # Command resolution
    # ------------------------------------------------------------------

    def _cmd_for(self, rel: str) -> str:
        """The shell command that runs one script.

        When `test_command` is set it acts as a template: `{file}` is replaced
        by the shell-quoted relative path.  Without it the file is invoked
        directly (requires executable bit and a shebang line).
        """
        if self.project.test_command:
            return self.project.test_command.replace("{file}", shlex.quote(rel))
        return f"./{rel}"

    def _is_runnable(self, path: Path) -> bool:
        """True when the file can be executed: either a test_command handles it,
        or the file itself has the executable bit set."""
        if self.project.test_command:
            return True
        return os.access(path, os.X_OK)

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _test_files(self) -> list[Path]:
        found: set[Path] = set()
        for pattern in self.project.test_patterns or []:
            if pattern.endswith("/"):
                base = self.root / pattern
                if base.is_dir():
                    for p in base.rglob("*"):
                        if p.is_file():
                            found.add(p)
            else:
                for p in self.root.glob(pattern):
                    if p.is_file():
                        found.add(p)
        return sorted(found)

    # ------------------------------------------------------------------
    # Collection — filesystem walk, no subprocess
    # ------------------------------------------------------------------

    def collect(self) -> Collection:
        result = Collection()
        for path in self._test_files():
            rel = str(path.relative_to(self.root))
            if self._is_runnable(path):
                result.tests.add(self.qualify(rel))
            else:
                result.failed_files[rel] = (
                    f"{rel}: not executable and no test_command configured"
                    ' (chmod +x, or add test_command = "bash {file}" to tdd.toml)'
                )
        return result

    # The base collect() calls these three; exec overrides collect() entirely
    # so they are never reached.  Providing trivial bodies avoids surprises if
    # a subclass or test calls them directly.
    def _collect_invocations(self):
        return []

    def _collect_batch(self, command, env):
        return None

    def _collect_per_file(self, rels, result):
        return result

    # ------------------------------------------------------------------
    # Doctor gate
    # ------------------------------------------------------------------

    def collectable(self) -> GateResult:
        """Warn about files that matched test_paths but cannot be run."""
        if self.project.test_command:
            return GateResult(ok=True)
        non_exec = [
            str(p.relative_to(self.root)) for p in self._test_files() if not os.access(p, os.X_OK)
        ]
        if not non_exec:
            return GateResult(ok=True)
        listed = "\n".join(non_exec[:10])
        more = f"\n… and {len(non_exec) - 10} more" if len(non_exec) > 10 else ""
        return GateResult(
            ok=False,
            output=(
                "these files matched test_paths but are not executable"
                ' (chmod +x, or set test_command = "bash {file}" in tdd.toml):\n' + listed + more
            ),
        )

    # ------------------------------------------------------------------
    # Suite run
    # ------------------------------------------------------------------

    def run(self, target: str | None = None) -> Verdict:
        verdict = Verdict(project=self.project.name, adapter=self.name, target=target)
        env = self._suite_env(None)
        started = time.monotonic()

        for path in self._test_files():
            rel = str(path.relative_to(self.root))
            qualified = self.qualify(rel)

            # When targeting, skip every other test for speed.
            if target is not None and qualified != target:
                continue

            if not self._is_runnable(path):
                if target == qualified:
                    verdict.target_outcome = NOT_COLLECTED
                    verdict.target_failure = f"{rel}: not executable and no test_command configured"
                continue

            code, out, err = run_command(
                self._cmd_for(rel), self.root, extra_env=env, label="suite"
            )
            combined = (out + "\n" + err).strip()

            if code == 0:
                verdict.passed.append(qualified)
                if target == qualified:
                    verdict.target_outcome = PASSED
            else:
                verdict.failed.append(qualified)
                if target == qualified:
                    verdict.target_outcome = FAILED
                    verdict.target_failure = clip_failure(combined)

        verdict.duration_ms = int((time.monotonic() - started) * 1000)
        return verdict
