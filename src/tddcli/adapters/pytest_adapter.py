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
    Verdict,
    run_command,
)


class PytestAdapter(Adapter):
    name = "pytest"

    def _base_cmd(self) -> str:
        return "uv run pytest" if (self.root / "pyproject.toml").is_file() else "pytest"

    def run(self, target: str | None = None) -> Verdict:
        verdict = Verdict(project=self.project.name, adapter=self.name, target=target)
        with tempfile.TemporaryDirectory(prefix="tdd-pytest-") as tmp:
            report_path = Path(tmp) / "report.json"
            cmd = (
                f"{self._base_cmd()} --json-report"
                f" --json-report-file={shlex.quote(str(report_path))} -q"
            )
            code, out, err = run_command(cmd, self.root)
            if not report_path.is_file():
                verdict.error = (
                    "pytest produced no JSON report (is pytest-json-report installed?): "
                    + (err or out)[:500]
                )
                return verdict
            report = json.loads(report_path.read_text())

        verdict.duration_ms = int(report.get("duration", 0) * 1000)

        uncollectable: set[str] = set()
        for collector in report.get("collectors", []):
            if collector.get("outcome") not in (None, "passed"):
                uncollectable.add(collector.get("nodeid", ""))

        for test in report.get("tests", []):
            qualified = self.qualify(test["nodeid"])
            if test["outcome"] == "passed":
                verdict.passed.append(qualified)
            elif test["outcome"] in ("failed", "error"):
                verdict.failed.append(qualified)

        if target is None:
            verdict.target_outcome = NOT_FOUND
            return verdict

        native = self.strip(target)
        hit = next(
            (t for t in report.get("tests", []) if t["nodeid"] == native), None
        )
        if hit is not None:
            verdict.target_outcome = PASSED if hit["outcome"] == "passed" else FAILED
            call = hit.get("call") or hit.get("setup") or {}
            verdict.target_failure = str(call.get("longrepr", ""))[:1500]
        else:
            target_file = native.split("::", 1)[0]
            if any(c == target_file or c.startswith(target_file) for c in uncollectable):
                verdict.target_outcome = NOT_COLLECTED
                verdict.target_failure = self._collector_error(report, target_file)[:1500]
            else:
                verdict.target_outcome = NOT_FOUND
        return verdict

    @staticmethod
    def _collector_error(report: dict, target_file: str) -> str:
        for collector in report.get("collectors", []):
            if collector.get("nodeid", "").startswith(target_file):
                return str(collector.get("longrepr", ""))
        return ""

    def _test_files(self) -> list[Path]:
        found: list[Path] = []
        for pattern in self.project.test_paths or ["tests/"]:
            if pattern.endswith("/"):
                base = self.root / pattern
                if base.is_dir():
                    found.extend(sorted(base.rglob("test_*.py")))
                    found.extend(sorted(base.rglob("*_test.py")))
            else:
                found.extend(sorted(self.root.glob(pattern)))
        return sorted({p for p in found if p.is_file()})

    def collect(self) -> Collection:
        """Per file (R10.3) — one uncollectable module must not destroy the whole set."""
        result = Collection()
        for path in self._test_files():
            rel = path.relative_to(self.root)
            code, out, err = run_command(
                f"{self._base_cmd()} --collect-only -q {shlex.quote(str(rel))}", self.root
            )
            if code != 0:
                result.failed_files[str(rel)] = (err or out).strip()[:800]
                continue
            for line in out.splitlines():
                line = line.strip()
                if "::" in line and not line.startswith(("=", "-", "no tests")):
                    result.tests.add(self.qualify(line))
        return result
