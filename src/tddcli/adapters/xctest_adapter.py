"""xctest adapter — XCTest/xcodebuild driver for Swift and Objective-C projects.

Test ids use the xcodebuild `-only-testing:` flag's own format so targeted runs
compose without translation:

    BundleName/ClassName/testMethodName

e.g.  AppTests/PollCadenceTests/testPollIntervalScalesOnlyUnderE2E

A xcodebuild build failure maps to `not_collected` rather than `failed`.
Swift has no separate collection phase — a test referencing a missing symbol
fails the *build*, not the run.  Mapping that to `not_collected` gives Swift
the same "stub before RED" discipline the tool already enforces for Python
(import error) and TypeScript (suite compile error): write a compiling stub,
then observe an assertion failure; the compile error is *not* the RED.

Collection strategy (R10.3):
  Batch — `xcodebuild test -enumerate-tests` (Xcode 16+), parsing
           `BundleName/ClassName/testMethodName` lines from its output.
  Per-file fallback — grep `class Foo: XCTestCase` and `func testBar()` from
           Swift source files, deriving the bundle name from `-scheme` in
           `test_command`.  One uncollectable file is recorded against itself
           and cannot destroy the rest of the set.

Config (`tdd.toml`):

    [project.native-ios]
    root         = "native-ios"
    adapter      = "xctest"
    test_paths   = ["AppTests/"]           # Swift source directories
    test_command = "xcodebuild test \\
      -project App.xcodeproj \\
      -scheme AppTests \\
      -destination 'platform=iOS Simulator,name=App-Unit' \\
      -derivedDataPath /tmp/app-unit-dd"

`test_command` is required — the adapter cannot know the scheme, destination,
or derived-data path otherwise.  The adapter appends `-only-testing:` for
targeted runs and `-enumerate-tests` for collection; nothing else.
"""

from __future__ import annotations

import re
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

# ---------------------------------------------------------------------------
# Patterns applied to xcodebuild stdout
# ---------------------------------------------------------------------------

# "Test Case '-[AppTests.PollCadenceTests testPollIntervalScalesOnlyUnderE2E]' passed (0.001 seconds)."
_CASE_RE = re.compile(r"Test Case '-\[(\w+)\.(\w+) (\w+)\]' (passed|failed)")

# End-of-build marker for a failed build (no tests ran)
_BUILD_FAILED_RE = re.compile(r"\*\* BUILD FAILED \*\*")

# Lines emitted by xcodebuild test -enumerate-tests (Xcode 16+):
#   AppTests/PollCadenceTests/testPollIntervalScalesOnlyUnderE2E
_ENUMERATE_LINE_RE = re.compile(r"^[ \t]*(\w+)/(\w+)/(test\w+)[ \t]*$", re.MULTILINE)

# Swift source patterns for the per-file grep fallback
_CLASS_RE = re.compile(r"class\s+(\w+)\s*:\s*\w*XCTestCase\b")
_METHOD_RE = re.compile(r"\bfunc\s+(test\w+)\s*\(")

# Extract `-scheme SomeName` from test_command
_SCHEME_RE = re.compile(r"-scheme[ \t]+(\S+)")


def _id_from_run_match(m: re.Match) -> str:
    """Build a `Bundle/Class/method` string from a _CASE_RE match."""
    bundle, class_, method, _ = m.groups()
    return f"{bundle}/{class_}/{method}"


class XCTestAdapter(Adapter):
    name = "xctest"

    def stub_hint(self) -> str:
        return (
            "a method body that compiles but fails its assertion — a missing symbol"
            " is a *build* failure (not_collected), not RED; write a stub that"
            " compiles first, then observe the assertion failure"
        )

    # ------------------------------------------------------------------
    # Core command
    # ------------------------------------------------------------------

    def _test_cmd(self) -> str:
        return self.project.test_command or "xcodebuild test"

    def _bundle_from_test_command(self) -> str:
        """Best-effort: extract the test bundle name from `-scheme <Name>`.

        xcodebuild schemes typically share a name with their test bundle
        (e.g. `-scheme AppTests` → bundle `AppTests`).  When the
        scheme cannot be parsed, fall back to `"Unknown"` — per-file ids will
        still be formed, just unaddressable by `-only-testing:` without the
        real bundle name.
        """
        m = _SCHEME_RE.search(self._test_cmd())
        return m.group(1) if m else "Unknown"

    # ------------------------------------------------------------------
    # Discovery — Swift source files
    # ------------------------------------------------------------------

    def _test_files(self) -> list[Path]:
        found: set[Path] = set()
        for pattern in self.project.test_patterns or []:
            if pattern.endswith("/"):
                base = self.root / pattern
                if base.is_dir():
                    found.update(p for p in base.rglob("*.swift") if p.is_file())
            else:
                found.update(p for p in self.root.glob(pattern) if p.is_file())
        return sorted(found)

    # ------------------------------------------------------------------
    # Collection
    # ------------------------------------------------------------------

    def collect(self) -> Collection:
        result = Collection()

        # Batch: try xcodebuild test -enumerate-tests (Xcode 16+)
        batch = self._enumerate_tests()
        if batch is not None:
            result.tests = batch
            return result

        # Per-file fallback: grep Swift source files
        bundle = self._bundle_from_test_command()
        for path in self._test_files():
            rel = str(path.relative_to(self.root))
            try:
                ids = self._grep_swift_tests(path, bundle)
                result.tests |= ids
            except OSError as exc:
                result.failed_files[rel] = str(exc)

        return result

    def _enumerate_tests(self) -> set[str] | None:
        """Run `xcodebuild test -enumerate-tests` and parse `Bundle/Class/method` lines.

        Returns the set of qualified ids, or None when the command fails or
        produces no parseable output (triggering the per-file fallback).
        """
        env = self._suite_env(None)
        code, out, err = run_command(
            f"{self._test_cmd()} -enumerate-tests",
            self.root,
            extra_env=env,
            label="collect",
        )
        if code != 0:
            return None
        ids = {
            self.qualify(f"{m.group(1)}/{m.group(2)}/{m.group(3)}")
            for m in _ENUMERATE_LINE_RE.finditer(out)
        }
        return ids if ids else None

    def _grep_swift_tests(self, path: Path, bundle: str) -> set[str]:
        """Extract test ids from a Swift source file without running xcodebuild.

        Finds every `class Foo: XCTestCase` block and every `func testBar()`
        inside it, forming `bundle/Foo/testBar` ids.  Matches are file-order,
        not scope-aware — a `func testHelper()` defined outside a test class
        may be included.  The batch path is authoritative; this is a fallback.
        """
        text = path.read_text(encoding="utf-8", errors="replace")
        ids: set[str] = set()
        classes = _CLASS_RE.findall(text)
        methods = _METHOD_RE.findall(text)
        for class_ in classes:
            for method in methods:
                ids.add(self.qualify(f"{bundle}/{class_}/{method}"))
        return ids

    # The base collect() calls these three; xctest overrides collect() entirely.
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
        """Fail fast when no test_command is configured.

        Without it the adapter cannot know the scheme, destination, or
        derived-data path; `xcodebuild test` alone is rarely runnable as-is.
        """
        if not self.project.test_command:
            return GateResult(
                ok=False,
                output=(
                    "xctest adapter requires test_command — add the full"
                    " `xcodebuild test -project … -scheme … -destination …`"
                    " invocation to tdd.toml so the adapter can append"
                    " -only-testing: and -enumerate-tests flags"
                ),
            )
        return GateResult(ok=True)

    # ------------------------------------------------------------------
    # Suite run
    # ------------------------------------------------------------------

    def run(self, target: str | None = None) -> Verdict:
        verdict = Verdict(project=self.project.name, adapter=self.name, target=target)
        env = self._suite_env(None)

        cmd = self._test_cmd()
        if target is not None:
            native = self.strip(target)
            cmd = f"{cmd} -only-testing:{native}"

        code, out, err = self._run_suite(cmd, env)
        combined = out + "\n" + err

        if _BUILD_FAILED_RE.search(combined):
            build_errors = self._build_errors(combined)
            if target is not None:
                verdict.target_outcome = NOT_COLLECTED
                verdict.target_failure = clip_failure(build_errors)
            else:
                verdict.error = clip_failure(build_errors)
            return verdict

        for m in _CASE_RE.finditer(combined):
            bundle, class_, method, outcome = m.groups()
            qualified = self.qualify(f"{bundle}/{class_}/{method}")
            if outcome == "passed":
                verdict.passed.append(qualified)
            else:
                verdict.failed.append(qualified)

        if target is None:
            return verdict

        if target in verdict.passed:
            verdict.target_outcome = PASSED
        elif target in verdict.failed:
            verdict.target_outcome = FAILED
            verdict.target_failure = self._failure_for(combined, self.strip(target))
        # else NOT_FOUND (default)

        return verdict

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------

    def _build_errors(self, combined: str) -> str:
        """Extract lines that look like compiler or linker errors."""
        return "\n".join(
            line
            for line in combined.splitlines()
            if ": error:" in line or "** BUILD FAILED **" in line
        )

    def _failure_for(self, combined: str, native_id: str) -> str:
        """Capture the assertion lines between 'started' and 'failed' for one test.

        xcodebuild interleaves test output like:
            Test Case '-[AppTests.PollCadenceTests testSomething]' started.
            /path/test.swift:42: error: … XCTAssertEqual failed: …
            Test Case '-[AppTests.PollCadenceTests testSomething]' failed (0.001 seconds).
        """
        parts = native_id.split("/")
        if len(parts) != 3:
            return clip_failure(combined)
        bundle, class_, method = parts
        bracket = f"[{bundle}.{class_} {method}]"
        start_marker = f"Test Case '-{bracket}' started."
        fail_marker = f"Test Case '-{bracket}' failed"

        capturing, captured = False, []
        for line in combined.splitlines():
            if start_marker in line:
                capturing, captured = True, []
            elif capturing:
                if fail_marker in line:
                    break
                captured.append(line)
        return clip_failure("\n".join(captured)) if captured else clip_failure(combined)
