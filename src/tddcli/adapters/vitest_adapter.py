"""vitest adapter.

Test ids are `<worktree-relative file> > <fullName>`, where fullName is the
space-joined ancestorTitles plus the test title. vitest may prefix its JSON with
non-JSON lines, so the payload is located rather than assumed (R10.2).
"""

from __future__ import annotations

import json
import os
import shlex
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
    run_command,
)


def _extract_json(raw: str) -> dict | None:
    start = raw.find("{")
    while start != -1:
        try:
            return json.loads(raw[start:])
        except json.JSONDecodeError:
            start = raw.find("{", start + 1)
    return None


class VitestAdapter(Adapter):
    name = "vitest"

    def _id_for(self, suite_path: str, full_name: str) -> str:
        abs_path = Path(suite_path)
        try:
            rel = os.path.relpath(abs_path, self.worktree)
        except ValueError:
            rel = suite_path
        return self.qualify(f"{rel} > {full_name}")

    def run(self, target: str | None = None) -> Verdict:
        verdict = Verdict(project=self.project.name, adapter=self.name, target=target)
        base = self.project.test_command or "npx vitest run"
        code, out, err = self._run_suite(f"{base} --reporter=json")
        report = _extract_json(out)
        if report is None:
            verdict.error = f"vitest produced no JSON output: {(err or out)[:500]}"
            return verdict

        verdict.duration_ms = int(report.get("duration") or 0)
        failed_suites: dict[str, str] = {}

        for suite in report.get("testResults", []):
            suite_path = suite.get("name", "")
            assertions = suite.get("assertionResults", [])
            if not assertions and suite.get("status") == "failed":
                failed_suites[suite_path] = str(suite.get("message", ""))[:1500]
            for t in assertions:
                qualified = self._id_for(suite_path, t["fullName"])
                if t["status"] == "passed":
                    verdict.passed.append(qualified)
                elif t["status"] == "failed":
                    verdict.failed.append(qualified)

        if target is None:
            verdict.target_outcome = NOT_FOUND
            return verdict

        if target in verdict.passed:
            verdict.target_outcome = PASSED
            return verdict
        if target in verdict.failed:
            verdict.target_outcome = FAILED
            for suite in report.get("testResults", []):
                for t in suite.get("assertionResults", []):
                    if self._id_for(suite.get("name", ""), t["fullName"]) == target:
                        verdict.target_failure = "\n".join(
                            m[:600] for m in t.get("failureMessages", [])[:3]
                        )
            return verdict

        target_file = self.strip(target).split(" > ", 1)[0]
        for suite_path, message in failed_suites.items():
            if suite_path.endswith(target_file):
                verdict.target_outcome = NOT_COLLECTED
                verdict.target_failure = message
                return verdict
        verdict.target_outcome = NOT_FOUND
        return verdict

    def _test_files(self) -> list[Path]:
        found: set[Path] = set()
        for pattern in self.project.test_paths or ["**/*.test.ts"]:
            pat = pattern.rstrip("/") + "/**/*" if pattern.endswith("/") else pattern
            for path in self.root.glob(pat):
                if path.is_file() and path.suffix in (".ts", ".tsx", ".js", ".jsx"):
                    if "node_modules" not in path.parts:
                        found.add(path)
        return sorted(found)

    def _parse_list_output(self, out: str, path: Path) -> set[str]:
        """Parse `vitest list` text output into ids matching those `run()` produces.

        `vitest list` ignores `--reporter=json` (checked against vitest 4.1.0) and
        emits one line per test:

            relative/file.test.ts > describe > nested describe > it name

        `run()` reports the same test with `fullName`, which is the ancestor titles
        and the title joined by a **space**. Splitting on " > " and rejoining the
        name parts with a space reproduces that exactly; keeping the arrows would
        yield ids that never match a verdict.
        """
        found: set[str] = set()
        for line in out.splitlines():
            line = line.strip()
            if " > " not in line:
                continue
            _, _, remainder = line.partition(" > ")
            full_name = " ".join(part.strip() for part in remainder.split(" > "))
            if full_name:
                found.add(self._id_for(str(path), full_name))
        return found

    def collectable(self) -> GateResult:
        """A single whole-suite probe, mirroring the pytest adapter's `--collect-only`
        (§10, cycle 15): `npx vitest list` at the project root rather than the
        per-file `collect()` loop below."""
        base = self.project.collect_command or "npx vitest list"
        code, out, err = run_command(base, self.root)
        return GateResult(ok=code == 0, output="" if code == 0 else (err or out).strip()[:2000])

    def collect(self) -> Collection:
        result = Collection()
        for path in self._test_files():
            rel = path.relative_to(self.root)
            base = self.project.collect_command or "npx vitest list"
            code, out, err = run_command(f"{base} {shlex.quote(str(rel))}", self.root)

            payload = _extract_json(out)
            if payload is not None:
                entries = payload if isinstance(payload, list) else payload.get("tests", [])
                for entry in entries or []:
                    name = entry.get("fullName") or entry.get("name")
                    if name:
                        result.tests.add(self._id_for(str(path), name))
                continue

            names = self._parse_list_output(out, path)
            if names:
                result.tests.update(names)
            else:
                # Zero tests from a file that exists is a tooling failure, not an
                # empty file — record it rather than silently collecting nothing.
                result.failed_files[str(rel)] = (
                    f"no tests parsed from `{base}` (exit {code}): "
                    + (err or out).strip()[:600]
                )
        return result
