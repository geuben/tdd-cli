"""gradle adapter — Gradle driver for Kotlin/JVM and Android projects (§10).

Runs the project's Gradle test task (`./gradlew test`, `testDebugUnitTest`,
`connectedDebugAndroidTest`, …) and reads the per-test verdicts from the
JUnit XML Gradle always writes.  Console output is *not* parsed: Gradle's
console is a task-level summary, not a reliable per-test log, whereas the XML
under `build/test-results/` (unit) and `build/outputs/.../androidTest-results/`
(instrumented) carries an exact `classname` / `name` / `failure` for every
case.  Both unit and instrumented tasks write the same JUnit shape, so one
parser serves both — the task is a config choice (`test_command`), not a code
path.

Test ids use `FQCN/method` so a targeted run composes to Gradle's own filter
without translation:

    com.example.PollCadenceTest/scalesOnlyUnderE2E

The adapter appends `--tests com.example.PollCadenceTest.scalesOnlyUnderE2E`
for a targeted run; nothing else.

A *compile* failure maps to `not_collected`, not `failed`.  Kotlin has no
separate collection phase — a test referencing a missing symbol fails
`compileTestKotlin`, not the run — so a compile error is treated like Python's
import error and Swift's build failure: write a compiling stub, then observe
the assertion failure.  The discriminator is not "BUILD FAILED" (a *test*
failure prints that too) but *whether any fresh JUnit XML was produced*: tests
that ran leave results, a compile error leaves none.

Stale results (R10.3): Gradle leaves the previous run's XML on disk and skips
up-to-date tasks, so a targeted `--tests` run could otherwise be scored against
another test's old XML.  The adapter deletes the result files before each run —
which also invalidates Gradle's up-to-date check, forcing the task to actually
re-run — so whatever XML exists afterward belongs to this invocation alone.

Collection is a per-file grep of Kotlin/Java sources (R10.3's fallback):
Gradle has no cheap whole-suite test enumerator, so there is no batch path.
One uncollectable file is recorded against itself and cannot destroy the set.

Config (`tdd.toml`):

    [project.android-app]
    root         = "android-app"
    adapter      = "gradle"
    test_paths   = ["src/test/"]                 # Kotlin/Java test sources
    test_command = "./gradlew testDebugUnitTest"  # JVM unit tests (fast)

Instrumented tests run the same way through a different task; give them a
longer timeout and a `lease` so only one run touches a device at a time:

    [project.android-e2e]
    root         = "android-app"
    adapter      = "gradle"
    test_paths   = ["src/androidTest/"]
    test_command = "./gradlew connectedDebugAndroidTest"
    lease        = "android-emulator"
    timeout      = 1200
    in_close_sweep = false                        # too slow per cycle
"""

from __future__ import annotations

import re
import shlex
import time
from pathlib import Path
from xml.etree import ElementTree

from .base import (
    FAILED,
    NOT_COLLECTED,
    PASSED,
    Adapter,
    Collection,
    GateResult,
    Verdict,
    clip_failure,
)

# ---------------------------------------------------------------------------
# Patterns applied to gradle console output (only to classify a run that
# produced no test results — the XML is authoritative for everything else)
# ---------------------------------------------------------------------------

_BUILD_FAILED_RE = re.compile(r"BUILD FAILED")

# A --tests filter that matched nothing: the target is not_found, not a failure.
#   > No tests found for given includes: [com.example.FooTest.bar](--tests filter)
_NO_TESTS_RE = re.compile(r"No tests found for given includes")

# Kotlin compiler errors ("e: file:line:col: message") and javac errors.
_KOTLIN_ERROR_RE = re.compile(r"^e: .*$", re.MULTILINE)

# Kotlin/Java source patterns for the per-file grep fallback.
_PACKAGE_RE = re.compile(r"^\s*package\s+([\w.]+)", re.MULTILINE)
_CLASS_RE = re.compile(r"\bclass\s+(\w+)")
# `@Test` (JUnit 4/5) followed by the annotated function/method name. Handles
# Kotlin `fun name`, Kotlin backtick names (`fun \`does the thing\`()`), and
# Java `void name()`.  Cross-class attribution within a file is not scope-aware
# — the batch (a real run) is authoritative; this is the fallback.
_METHOD_RE = re.compile(
    r"@Test\b.*?\b(?:fun|void)\s+(?:`(?P<bt>[^`]+)`|(?P<id>\w+))",
    re.DOTALL,
)


class GradleAdapter(Adapter):
    name = "gradle"

    def stub_hint(self) -> str:
        return (
            "a test method body that compiles but fails its assertion — a missing"
            " symbol is a *compile* failure (not_collected), not RED; write a stub"
            ' that compiles first (e.g. `fail("not implemented")`), then observe the'
            " assertion failure"
        )

    # ------------------------------------------------------------------
    # Core command
    # ------------------------------------------------------------------

    def _test_cmd(self) -> str:
        return self.project.test_command or "./gradlew test"

    def _gradle_filter(self, native_id: str) -> str:
        """Translate an `FQCN/method` id into Gradle's `--tests FQCN.method` form.

        A bare class id (no `/`) is passed through, targeting the whole class.
        """
        if "/" in native_id:
            cls, method = native_id.rsplit("/", 1)
            return f"{cls}.{method}"
        return native_id

    # ------------------------------------------------------------------
    # Discovery — Kotlin / Java source files
    # ------------------------------------------------------------------

    def _test_files(self) -> list[Path]:
        found: set[Path] = set()
        for pattern in self.project.test_patterns or []:
            if pattern.endswith("/"):
                base = self.root / pattern
                if base.is_dir():
                    for suffix in ("*.kt", "*.java"):
                        found.update(p for p in base.rglob(suffix) if p.is_file())
            else:
                found.update(p for p in self.root.glob(pattern) if p.is_file())
        return sorted(found)

    # ------------------------------------------------------------------
    # Collection — per-file grep (no cheap whole-suite enumerator exists)
    # ------------------------------------------------------------------

    def collect(self) -> Collection:
        result = Collection()
        for path in self._test_files():
            rel = str(path.relative_to(self.root))
            try:
                result.tests |= self._grep_tests(path)
            except OSError as exc:
                result.failed_files[rel] = str(exc)
        return result

    def _grep_tests(self, path: Path) -> set[str]:
        """Extract `pkg.Class/method` ids from one Kotlin/Java source file.

        Finds every `@Test`-annotated method and every declared class, forming
        `pkg.Class/method` ids qualified by the package declaration.  Matches
        are file-order, not scope-aware — a file with two classes attributes
        each test method to both.  The batch path is authoritative; this is the
        fallback that keeps one unreadable file from destroying the whole set.
        """
        text = path.read_text(encoding="utf-8", errors="replace")
        pkg_match = _PACKAGE_RE.search(text)
        pkg = f"{pkg_match.group(1)}." if pkg_match else ""
        classes = _CLASS_RE.findall(text)
        methods = [m.group("bt") or m.group("id") for m in _METHOD_RE.finditer(text)]
        ids: set[str] = set()
        for class_ in classes:
            for method in methods:
                ids.add(self.qualify(f"{pkg}{class_}/{method}"))
        return ids

    # The base collect() calls these three; gradle overrides collect() entirely
    # so they are never reached.  Trivial bodies avoid surprising a direct caller.
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
        """Collection is a source grep — it needs no toolchain, so enumeration is
        always possible.  Whether Gradle itself can run is checked by the
        `gradle wrapper present` branch in `tdd doctor` (§8.1)."""
        return GateResult(ok=True)

    # ------------------------------------------------------------------
    # JUnit XML results
    # ------------------------------------------------------------------

    def _result_files(self) -> list[Path]:
        """Every JUnit XML file Gradle writes for this project's tests.

        Covers both JVM unit tasks (`build/test-results/<task>/TEST-*.xml`) and
        Android instrumented tasks (`build/outputs/.../androidTest-results/`),
        across every module under the project root.
        """
        found: set[Path] = set()
        found.update(self.root.glob("**/build/test-results/**/*.xml"))
        found.update(self.root.glob("**/build/outputs/**/androidTest-results/**/*.xml"))
        return sorted(found)

    def _clear_results(self) -> None:
        """Delete stale JUnit XML before a run.

        Two problems in one: Gradle leaves the previous run's XML on disk, and
        it skips up-to-date tasks (so no fresh XML is written).  Removing the
        result files fixes both — a targeted run is scored only against the XML
        it produced, and deleting a task's output invalidates its up-to-date
        check so the task actually re-runs.
        """
        for path in self._result_files():
            try:
                path.unlink()
            except OSError:
                pass

    def _parse_results(self) -> tuple[set[str], set[str], dict[str, str]]:
        """Parse every JUnit XML file into `(passed, failed, failures)`.

        A `<testcase>` with a `<failure>`/`<error>` child failed; with a
        `<skipped>` child it is neither (excluded); otherwise it passed. Ids are
        qualified. `failures` maps a failed id to its message + stack trace.
        """
        passed: set[str] = set()
        failed: set[str] = set()
        failures: dict[str, str] = {}
        for path in self._result_files():
            try:
                tree = ElementTree.parse(path)
            except ElementTree.ParseError:
                continue
            for case in tree.iter("testcase"):
                classname = case.get("classname") or ""
                method = case.get("name") or ""
                raw = f"{classname}/{method}" if classname else method
                qualified = self.qualify(raw)
                failure = case.find("failure")
                if failure is None:
                    failure = case.find("error")
                if failure is not None:
                    failed.add(qualified)
                    failures[qualified] = self._failure_text(failure)
                elif case.find("skipped") is None:
                    passed.add(qualified)
        return passed, failed, failures

    @staticmethod
    def _failure_text(failure: ElementTree.Element) -> str:
        message = failure.get("message") or ""
        body = (failure.text or "").strip()
        combined = "\n".join(part for part in (message, body) if part)
        return clip_failure(combined) if combined else "test failed"

    def _build_errors(self, combined: str) -> str:
        """Lines that explain why a run produced no tests: compiler errors and
        Gradle's own failure report."""
        wanted = ("e: ", ": error:", "FAILED", "FAILURE:", "What went wrong", "Execution failed")
        lines = [line for line in combined.splitlines() if any(w in line for w in wanted)]
        return clip_failure("\n".join(lines)) if lines else clip_failure(combined)

    # ------------------------------------------------------------------
    # Suite run
    # ------------------------------------------------------------------

    def run(self, target: str | None = None) -> Verdict:
        verdict = Verdict(project=self.project.name, adapter=self.name, target=target)
        env = self._suite_env(None)

        cmd = self._test_cmd()
        if target is not None:
            native = self.strip(target)
            cmd = f"{cmd} --tests {shlex.quote(self._gradle_filter(native))}"

        started = time.monotonic()
        self._clear_results()
        code, out, err = self._run_suite(cmd, env)
        verdict.duration_ms = int((time.monotonic() - started) * 1000)
        combined = out + "\n" + err

        passed, failed, failures = self._parse_results()
        verdict.passed = sorted(passed)
        verdict.failed = sorted(failed)

        # No test ran. Distinguish "filter matched nothing" (not_found) from a
        # compile/config failure (not_collected) from a genuinely empty suite.
        if not passed and not failed:
            if _NO_TESTS_RE.search(combined):
                return verdict  # target stays NOT_FOUND; empty full run is clean
            if code != 0 or _BUILD_FAILED_RE.search(combined):
                errors = self._build_errors(combined)
                if target is not None:
                    verdict.target_outcome = NOT_COLLECTED
                    verdict.target_failure = errors
                else:
                    verdict.error = errors
            return verdict

        if target is None:
            return verdict

        if target in passed:
            verdict.target_outcome = PASSED
        elif target in failed:
            verdict.target_outcome = FAILED
            failure_text = failures.get(target, "test failed")
            verdict.target_failure = failure_text
            verdict.target_evidence = next(
                (ln for ln in failure_text.splitlines() if ln.strip()), ""
            )
        # else NOT_FOUND (default): the suite ran but never produced this id

        return verdict
