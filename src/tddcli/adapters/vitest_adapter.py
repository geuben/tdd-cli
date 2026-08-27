"""vitest adapter.

Test ids are `<project-root-relative file> > <fullName>`, where fullName is the
space-joined ancestorTitles plus the test title. Root-relative matches the pytest
adapter's nodeids and — decisively — `Engine._qualify`, which strips the project
root from plan declarations; a worktree-relative id here can never equal a
declared target. vitest may prefix its JSON with non-JSON lines, so the payload
is located rather than assumed (R10.2).
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
    _overlap_error,
    _suite_overlap,
    clip_failure,
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

    def stub_hint(self) -> str:
        return '`throw new Error("not implemented")` in every body'

    def normalise_id(self, test_id: str) -> str:
        """Canonicalise the describe/test separator for target matching.

        vitest's `fullName` joins ancestor titles and the test title with a space,
        so collected ids look like `frontend::a.test.ts > someHelper formats a value`.
        A planner naturally writes ` > ` at each nesting level. Treating both as
        equivalent prevents a formatting-only difference from producing NOT_FOUND.

        The structural ` > ` between the file and the name is preserved; only the
        ` > ` separators inside the name part are collapsed to a space.
        """
        raw = self.strip(test_id)
        file_part, sep, remainder = raw.partition(" > ")
        if not sep:
            return test_id
        name = " ".join(part.strip() for part in remainder.split(" > "))
        return self.qualify(f"{file_part} > {name}")

    def _id_for(self, suite_path: str, full_name: str) -> str:
        abs_path = Path(suite_path)
        try:
            rel = os.path.relpath(abs_path, self.root)
        except ValueError:
            rel = suite_path
        return self.qualify(f"{rel} > {full_name}")

    def _test_cmd(self) -> str:
        return self.project.test_command or "npx vitest run"

    def _collect_cmd(self) -> str:
        return self.project.collect_command or "npx vitest list"

    def run(self, target: str | None = None) -> Verdict:
        verdict = Verdict(project=self.project.name, adapter=self.name, target=target)
        # Union across the default suite and every override suite (R7.13). A suite
        # producing no JSON is a loud error, not a silent gap: swallowing it would
        # report a target living in that suite as `not_found`.
        suites: list[dict] = []
        suite_ids: list[set[str]] = []
        for base, extra_env in self._suite_invocations():
            code, out, err = self._run_suite(f"{base} --reporter=json", extra_env)
            report = _extract_json(out)
            if report is None:
                verdict.error = f"`{base}` produced no JSON output: {(err or out)[:500]}"
                return verdict
            verdict.duration_ms += int(report.get("duration") or 0)
            results = report.get("testResults", [])
            suites.extend(results)
            suite_ids.append(
                {
                    self._id_for(s.get("name", ""), t["fullName"])
                    for s in results
                    for t in s.get("assertionResults", [])
                }
            )

        overlap = _suite_overlap(suite_ids)
        if overlap:
            verdict.error = _overlap_error(overlap)
            return verdict

        failed_suites: dict[str, str] = {}

        for suite in suites:
            suite_path = suite.get("name", "")
            assertions = suite.get("assertionResults", [])
            if not assertions and suite.get("status") == "failed":
                failed_suites[suite_path] = clip_failure(str(suite.get("message", "")))
            for t in assertions:
                qualified = self._id_for(suite_path, t["fullName"])
                if t["status"] == "passed":
                    verdict.passed.append(qualified)
                elif t["status"] == "failed":
                    verdict.failed.append(qualified)

        if target is None:
            verdict.target_outcome = NOT_FOUND
            return verdict

        ntarget = self.normalise_id(target)
        passed_norm = {self.normalise_id(t): t for t in verdict.passed}
        failed_norm = {self.normalise_id(t): t for t in verdict.failed}

        if ntarget in passed_norm:
            verdict.target_outcome = PASSED
            return verdict
        if ntarget in failed_norm:
            verdict.target_outcome = FAILED
            for suite in suites:
                for t in suite.get("assertionResults", []):
                    if (
                        self.normalise_id(self._id_for(suite.get("name", ""), t["fullName"]))
                        == ntarget
                    ):
                        verdict.target_failure = "\n".join(
                            clip_failure(m, 600) for m in t.get("failureMessages", [])[:3]
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
        for pattern in self.project.test_patterns or ["**/*.test.ts"]:
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
        """One whole-suite probe per declared suite, mirroring the pytest adapter's
        `--collect-only` (§10): `npx vitest list` at the project root rather than
        the per-file `collect()` loop below.

        An override without a `collect_command` fails here, at run start, not
        per-file during a cycle: `vitest list` knows nothing of the override's
        config, and falling back to the override's *run* command would execute the
        suite — against a live backend — just to enumerate it.
        """
        chunks = []
        code, out, err = run_command(
            self._collect_cmd(), self.root, extra_env=self._suite_env(None), label="doctor"
        )
        if code != 0:
            chunks.append((err or out).strip())
        for ov in self.project.overrides:
            if not ov.collect_command:
                chunks.append(
                    f"override {ov.pattern!r}: a vitest override needs an explicit"
                    ' collect_command (e.g. "npx vitest list --config'
                    ' vitest.other.config.ts")'
                )
                continue
            code, out, err = run_command(
                ov.collect_command, self.root, extra_env=self._suite_env(ov), label="doctor"
            )
            if code != 0:
                chunks.append((err or out).strip())
        return GateResult(ok=not chunks, output="\n\n".join(chunks)[:2000])

    def override_isolation(self) -> GateResult:
        """Probes with the default `vitest list` — the same stand-in for the
        default run config that `collectable()` already relies on (`vitest run`
        has no listing mode, and running the suite just to enumerate it would
        execute against whatever the tests need live)."""
        if not self.project.overrides:
            return GateResult(ok=True)
        code, out, err = run_command(
            self._collect_cmd(), self.root, extra_env=self._suite_env(None), label="doctor"
        )
        reached = sorted(
            {
                f
                for f in (
                    line.strip().partition(" > ")[0] for line in out.splitlines() if " > " in line
                )
                if self.project.override_for(f)
            }
        )
        if not reached:
            return GateResult(ok=True)
        return GateResult(
            ok=False,
            output=(
                "the default config's discovery reaches files an override owns, so"
                " suite runs would observe them without the override's command/env:"
                f" {', '.join(reached[:5])}. Exclude them from the default vitest"
                " config (test.exclude) or scope its include globs."
            ),
        )

    def _collect_invocations(self) -> list[tuple[str, dict[str, str] | None]]:
        """An override with no `collect_command` gets no batch — `vitest list` knows
        nothing of its config, and its files fall to the loop, which records the
        missing `collect_command` against each of them as before."""
        return [(self._collect_cmd(), self._suite_env(None))] + [
            (ov.collect_command, self._suite_env(ov))
            for ov in self.project.overrides
            if ov.collect_command
        ]

    def _collect_batch(
        self, command: str, env: dict[str, str] | None
    ) -> tuple[set[str], set[str]] | None:
        """Unlike `_parse_list_output`, which pins every id to the one file it was
        given, a whole-suite listing must read the file from each line — the same
        `file > describe > name` shape, one file per line rather than one per run."""
        code, out, err = run_command(command, self.root, extra_env=env, label="collect")
        if code != 0:
            return None
        tests: set[str] = set()
        files: set[str] = set()
        for line in out.splitlines():
            line = line.strip()
            if " > " not in line:
                continue
            rel, _, remainder = line.partition(" > ")
            full_name = " ".join(part.strip() for part in remainder.split(" > "))
            if rel and full_name:
                tests.add(self.qualify(f"{rel.strip()} > {full_name}"))
                files.add(rel.strip())
        # An empty result needs no special case: it accounts for no files, so every
        # file falls to the loop exactly as a failure would.
        return tests, files

    def _collect_per_file(self, rels: set[str], result: Collection) -> Collection:
        for rel_str in sorted(rels):
            path = self.root / rel_str
            rel = Path(rel_str)
            ov = self.project.override_for(str(rel))
            if ov is not None and not ov.collect_command:
                result.failed_files[str(rel)] = (
                    f"override {ov.pattern!r} declares no collect_command; vitest"
                    " cannot list these tests under the default config"
                )
                continue
            base = ov.collect_command if ov else self._collect_cmd()
            env = self._suite_env(ov)
            code, out, err = run_command(
                f"{base} {shlex.quote(str(rel))}",
                self.root,
                extra_env=env,
                label="collect",
            )

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
                    f"no tests parsed from `{base}` (exit {code}): " + (err or out).strip()[:600]
                )
        return result
