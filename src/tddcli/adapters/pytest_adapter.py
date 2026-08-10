"""pytest adapter.

Two defects in the prior system are corrected here (R10.2):

* `collectors` is inspected, so an import error reports `not_collected` and is never
  conflated with a mistyped identifier (`not_found`). One resolves by writing a stub;
  the other by fixing a name. Conflating them sent agents to ask a human.
* The report file is written to a fresh temp directory each run, so a stale report can
  never be read as if current.
"""

from __future__ import annotations

import json
import shlex
import tempfile
from pathlib import Path

from .base import (
    FAILED,
    NOT_COLLECTED,
    NOT_FOUND,
    PASSED,
    Adapter,
    Collection,
    GateResult,
    Verdict,
    _overlap_error,
    _suite_overlap,
    run_command,
)

#: Environment-manager marker files, most specific first. A pyproject.toml alone is
#: NOT a marker: Poetry, pipenv, PDM and plain-venv projects all have one, and
#: assuming uv there runs the suite in an environment the project never built.
RUNNER_MARKERS = (
    ("uv.lock", "uv run "),
    ("poetry.lock", "poetry run "),
    ("Pipfile", "pipenv run "),
    ("pdm.lock", "pdm run "),
)


class PytestAdapter(Adapter):
    name = "pytest"

    def stub_hint(self) -> str:
        return "`raise NotImplementedError` in every body"

    def _runner_prefix(self) -> str:
        """The project root is checked before the worktree root: a workspace keeps
        one lockfile at the top, but a member with its own marker owns its choice."""
        for base in (self.root, self.worktree):
            for marker, prefix in RUNNER_MARKERS:
                if (base / marker).is_file():
                    return prefix
        pyproject = self.root / "pyproject.toml"
        if pyproject.is_file() and "[tool.poetry]" in pyproject.read_text():
            return "poetry run "
        return ""

    def _base_cmd(self) -> str:
        return f"{self._runner_prefix()}pytest"

    def plugin_probe_cmd(self) -> str:
        """The pytest-json-report check, runnable in the project's own environment."""
        return f"{self._runner_prefix()}python -c 'import pytest_jsonreport'"

    def _test_cmd(self) -> str:
        """The project's own suite command, so the suite under TDD is the real one."""
        return self.project.test_command or self._base_cmd()

    def _collect_cmd(self) -> str:
        return self.project.collect_command or self._base_cmd()

    def _suite_report(
        self, base_cmd: str, extra_env: dict[str, str] | None
    ) -> tuple[dict | None, str]:
        with tempfile.TemporaryDirectory(prefix="tdd-pytest-") as tmp:
            report_path = Path(tmp) / "report.json"
            # Only reporting flags are appended — parallelism, markers and plugins
            # stay exactly as the project declared them. json-report is xdist-safe:
            # `collectors` is omitted when nothing fails to collect, and present with
            # the failing entry when something does, which is when it is consulted.
            cmd = (
                f"{base_cmd} --json-report"
                f" --json-report-file={shlex.quote(str(report_path))}"
            )
            code, out, err = self._run_suite(cmd, extra_env)
            if not report_path.is_file():
                return None, (
                    f"`{base_cmd}` produced no JSON report"
                    " (is pytest-json-report installed?): " + (err or out)[:500]
                )
            return json.loads(report_path.read_text()), ""

    def run(self, target: str | None = None) -> Verdict:
        verdict = Verdict(project=self.project.name, adapter=self.name, target=target)
        # Union across the default suite and every override suite (R7.13). A suite
        # that produces no report is a loud error, not a silent gap: swallowing it
        # would report a target that lives in that suite as `not_found`, sending the
        # agent to rewrite a test that is fine.
        tests: list[dict] = []
        collectors: list[dict] = []
        suite_ids: list[set[str]] = []
        for base_cmd, extra_env in self._suite_invocations():
            report, error = self._suite_report(base_cmd, extra_env)
            if report is None:
                verdict.error = error
                return verdict
            verdict.duration_ms += int(report.get("duration", 0) * 1000)
            tests.extend(report.get("tests", []))
            collectors.extend(report.get("collectors", []))
            suite_ids.append({t["nodeid"] for t in report.get("tests", [])})

        overlap = _suite_overlap(suite_ids)
        if overlap:
            verdict.error = _overlap_error(overlap)
            return verdict

        uncollectable: set[str] = set()
        for collector in collectors:
            if collector.get("outcome") not in (None, "passed"):
                uncollectable.add(collector.get("nodeid", ""))

        for test in tests:
            qualified = self.qualify(test["nodeid"])
            if test["outcome"] == "passed":
                verdict.passed.append(qualified)
            elif test["outcome"] in ("failed", "error"):
                verdict.failed.append(qualified)

        if target is None:
            verdict.target_outcome = NOT_FOUND
            return verdict

        native = self.strip(target)
        hit = next((t for t in tests if t["nodeid"] == native), None)
        if hit is not None:
            verdict.target_outcome = PASSED if hit["outcome"] == "passed" else FAILED
            call = hit.get("call") or hit.get("setup") or {}
            verdict.target_failure = str(call.get("longrepr", ""))[:1500]
        else:
            target_file = native.split("::", 1)[0]
            if any(c == target_file or c.startswith(target_file) for c in uncollectable):
                verdict.target_outcome = NOT_COLLECTED
                verdict.target_failure = self._collector_error(collectors, target_file)[:1500]
            else:
                verdict.target_outcome = NOT_FOUND
        return verdict

    @staticmethod
    def _collector_error(collectors: list[dict], target_file: str) -> str:
        for collector in collectors:
            if collector.get("nodeid", "").startswith(target_file):
                return str(collector.get("longrepr", ""))
        return ""

    def _collect_cmd_for(self, rel: str) -> tuple[str, dict[str, str] | None]:
        """The collection command for one file: the owning override's, else the
        project default. An override without a `collect_command` collects with its
        `test_command` — pytest's `--collect-only` composes with any run command."""
        ov = self.project.override_for(rel)
        if ov is None:
            return self._collect_cmd(), self._suite_env(None)
        return ov.collect_command or ov.test_command, self._suite_env(ov)

    def _test_files(self) -> list[Path]:
        found: list[Path] = []
        for pattern in self.project.test_patterns or ["tests/"]:
            if pattern.endswith("/"):
                base = self.root / pattern
                if base.is_dir():
                    found.extend(sorted(base.rglob("test_*.py")))
                    found.extend(sorted(base.rglob("*_test.py")))
            else:
                found.extend(sorted(self.root.glob(pattern)))
        return sorted({p for p in found if p.is_file()})

    def collectable(self) -> GateResult:
        """One whole-suite `--collect-only` per declared suite (§10) — the default
        command plus each override's — not the per-file `collect()` loop below.
        That loop is R10.3/R10.4's per-file collection, the slow path (the
        whole-suite probe costs 0.04s on a broken project vs. minutes for the
        per-file sweep on a real one).

        Reads **stdout**, not stderr: `uv` writes environment warnings
        (`VIRTUAL_ENV=... does not match ...`) to stderr while pytest writes the
        actual `ModuleNotFoundError` to stdout. A doctor check that reads stderr
        loses the real error and the failure surfaces unattributed.
        """
        chunks = []
        probes = [(self._collect_cmd(), self._suite_env(None))] + [
            (ov.collect_command or ov.test_command, self._suite_env(ov))
            for ov in self.project.overrides
        ]
        for cmd, env in probes:
            code, out, err = run_command(
                f"{cmd} --collect-only -q", self.root, extra_env=env
            )
            if code != 0:
                chunks.append(out.strip())
        return GateResult(ok=not chunks, output="\n\n".join(chunks)[:2000])

    def override_isolation(self) -> GateResult:
        """Probes the *test* command's discovery, not `collect_command`'s: the
        test command is what runs at suite time, and a scoped `test_command`
        with a bare per-file `collect_command` is a legitimate registry (the
        per-file command always gets an explicit path). `{workers}` becomes 0 —
        xdist's "no workers" — since discovery needs no parallelism. A probe
        that fails to collect at all is `collectable`'s finding, not this one's."""
        if not self.project.overrides:
            return GateResult(ok=True)
        probe = f"{self._test_cmd().replace('{workers}', '0')} --collect-only -q"
        code, out, err = run_command(probe, self.root, extra_env=self._suite_env(None))
        reached = sorted({
            f for f in (
                line.split("::", 1)[0]
                for line in out.splitlines()
                if "::" in line
            )
            if self.project.override_for(f)
        })
        if not reached:
            return GateResult(ok=True)
        return GateResult(ok=False, output=(
            "the default suite's discovery reaches files an override owns, so"
            " suite runs would observe them without the override's command/env:"
            f" {', '.join(reached[:5])}. Scope the default test_command so it"
            " cannot reach them (e.g. `pytest tests/`)."
        ))

    def collect(self) -> Collection:
        """Per file (R10.3) — one uncollectable module must not destroy the whole set."""
        result = Collection()
        for path in self._test_files():
            rel = path.relative_to(self.root)
            base, env = self._collect_cmd_for(str(rel))
            code, out, err = run_command(
                f"{base} --collect-only -q {shlex.quote(str(rel))}",
                self.root,
                extra_env=env,
            )
            if code != 0:
                result.failed_files[str(rel)] = (err or out).strip()[:800]
                continue
            for line in out.splitlines():
                line = line.strip()
                if "::" in line and not line.startswith(("=", "-", "no tests")):
                    result.tests.add(self.qualify(line))
        return result
