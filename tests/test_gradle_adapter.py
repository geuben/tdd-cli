"""gradle adapter — pinned against real Gradle JUnit XML and console output.

All tests run without a JDK, Gradle, or the Android SDK installed: they
exercise the XML parsing, id namespacing and command construction against
captured output strings, exactly as test_xctest_adapter.py tests xctest
parsing against captured xcodebuild output. `_run_suite` is mocked; its
side-effect writes the JUnit XML a real Gradle run would leave behind.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from tddcli import config as config_mod
from tddcli.adapters.base import FAILED, NOT_COLLECTED, NOT_FOUND, PASSED
from tddcli.adapters.gradle_adapter import _METHOD_RE, GradleAdapter

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

TOML = """
[project.android-app]
root         = "android-app"
adapter      = "gradle"
test_paths   = ["src/test/"]
test_command = "./gradlew testDebugUnitTest"
"""

TOML_DEFAULT_CMD = """
[project.android-app]
root       = "android-app"
adapter    = "gradle"
test_paths = ["src/test/"]
"""

# Verbatim Gradle JUnit XML for one class: one test passes, one fails.
JUNIT_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="com.example.PollCadenceTest" tests="2" skipped="0" failures="1" errors="0" timestamp="2026-08-18T09:48:00" hostname="mac" time="0.031">
  <properties/>
  <testcase name="scalesOnlyUnderE2E" classname="com.example.PollCadenceTest" time="0.012"/>
  <testcase name="flooredAtOneSecond" classname="com.example.PollCadenceTest" time="0.019">
    <failure message="expected:&lt;1000&gt; but was:&lt;500&gt;" type="org.opentest4j.AssertionFailedError">org.opentest4j.AssertionFailedError: expected:&lt;1000&gt; but was:&lt;500&gt;
\tat com.example.PollCadenceTest.flooredAtOneSecond(PollCadenceTest.kt:24)
</failure>
  </testcase>
  <system-out><![CDATA[]]></system-out>
</testsuite>
"""

# `> Task :compileTestKotlin FAILED` — a compile error, no tests ran.
COMPILE_FAILED_OUTPUT = """\
> Task :compileTestKotlin FAILED
e: /android-app/src/main/kotlin/PollCadence.kt:12:20: unresolved reference: pollNanos

FAILURE: Build failed with an exception.
* What went wrong:
Execution failed for task ':compileTestKotlin'.
BUILD FAILED in 2s
"""

# `--tests` filter matched nothing — the target does not exist.
NO_TESTS_OUTPUT = """\
> Task :testDebugUnitTest FAILED
FAILURE: Build failed with an exception.
* What went wrong:
Execution failed for task ':testDebugUnitTest'.
> No tests found for given includes: [com.example.PollCadenceTest.doesNotExist](--tests filter)
BUILD FAILED in 1s
"""

# A run where a test failed: Gradle exits non-zero and prints BUILD FAILED, but
# the XML was still written and is authoritative.
TEST_FAILED_OUTPUT = """\
> Task :testDebugUnitTest FAILED
FAILURE: Build failed with an exception.
* What went wrong:
Execution failed for task ':testDebugUnitTest'.
> There were failing tests.
BUILD FAILED in 3s
"""

PASS = "android-app::com.example.PollCadenceTest/scalesOnlyUnderE2E"
FAIL = "android-app::com.example.PollCadenceTest/flooredAtOneSecond"


def make_adapter(tmp_path: Path, toml: str = TOML) -> GradleAdapter:
    (tmp_path / "tdd.toml").write_text(toml)
    (tmp_path / "android-app" / "src" / "test").mkdir(parents=True)
    cfg = config_mod.load(tmp_path)
    return GradleAdapter(cfg.project("android-app"), tmp_path)


def write_results(adapter: GradleAdapter, xml: str, task: str = "testDebugUnitTest") -> Path:
    """Write JUnit XML where Gradle would, under the project root."""
    out = adapter.root / "build" / "test-results" / task / "TEST-com.example.PollCadenceTest.xml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(xml)
    return out


def suite_writing(adapter: GradleAdapter, xml: str, code: int = 0, out: str = "", err: str = ""):
    """A `_run_suite` side-effect that writes the given XML, like a real run."""

    def _side_effect(cmd, env=None):
        write_results(adapter, xml)
        return (code, out, err)

    return _side_effect


def write_kotlin(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


# ---------------------------------------------------------------------------
# Regex — @Test method extraction
# ---------------------------------------------------------------------------


def test_method_re_matches_kotlin_fun():
    m = _METHOD_RE.search("@Test\n    fun scalesOnlyUnderE2E() {")
    assert m is not None
    assert (m.group("id") or m.group("bt")) == "scalesOnlyUnderE2E"


def test_method_re_matches_backtick_name():
    m = _METHOD_RE.search("@Test\n    fun `interval is floored at one second`() {")
    assert m is not None
    assert (m.group("bt") or m.group("id")) == "interval is floored at one second"


def test_method_re_matches_java_void():
    m = _METHOD_RE.search("@Test\n    public void flooredAtOneSecond() {")
    assert m is not None
    assert (m.group("id") or m.group("bt")) == "flooredAtOneSecond"


# ---------------------------------------------------------------------------
# Test id format
# ---------------------------------------------------------------------------


def test_run_output_produces_project_namespaced_ids(tmp_path):
    adapter = make_adapter(tmp_path)
    with patch.object(
        type(adapter), "_run_suite", side_effect=suite_writing(adapter, JUNIT_XML, 1)
    ):
        verdict = adapter.run()
    assert PASS in verdict.passed
    assert FAIL in verdict.failed


def test_ids_are_project_prefixed(tmp_path):
    adapter = make_adapter(tmp_path)
    with patch.object(
        type(adapter), "_run_suite", side_effect=suite_writing(adapter, JUNIT_XML, 1)
    ):
        verdict = adapter.run()
    for id_ in verdict.passed + verdict.failed:
        assert id_.startswith("android-app::")


# ---------------------------------------------------------------------------
# run() — verdict parsing from JUnit XML
# ---------------------------------------------------------------------------


def test_passed_and_failed_counts(tmp_path):
    adapter = make_adapter(tmp_path)
    with patch.object(
        type(adapter), "_run_suite", side_effect=suite_writing(adapter, JUNIT_XML, 1)
    ):
        verdict = adapter.run()
    assert len(verdict.passed) == 1
    assert len(verdict.failed) == 1


def test_failed_test_output_is_captured(tmp_path):
    adapter = make_adapter(tmp_path)
    with patch.object(
        type(adapter),
        "_run_suite",
        side_effect=suite_writing(adapter, JUNIT_XML, 1, TEST_FAILED_OUTPUT),
    ):
        verdict = adapter.run(FAIL)
    assert verdict.target_outcome == FAILED
    assert "expected:<1000> but was:<500>" in verdict.target_failure


def test_passing_targeted_run_sets_passed(tmp_path):
    adapter = make_adapter(tmp_path)
    with patch.object(
        type(adapter), "_run_suite", side_effect=suite_writing(adapter, JUNIT_XML, 1)
    ):
        verdict = adapter.run(PASS)
    assert verdict.target_outcome == PASSED


def test_skipped_test_is_neither_passed_nor_failed(tmp_path):
    adapter = make_adapter(tmp_path)
    xml = """\
<testsuite name="com.example.SkipTest" tests="1" skipped="1" failures="0">
  <testcase name="ignored" classname="com.example.SkipTest"><skipped/></testcase>
</testsuite>
"""
    with patch.object(type(adapter), "_run_suite", side_effect=suite_writing(adapter, xml)):
        verdict = adapter.run()
    assert verdict.passed == []
    assert verdict.failed == []


# ---------------------------------------------------------------------------
# run() — compile failure maps to not_collected (not failed)
# ---------------------------------------------------------------------------


def test_compile_failure_with_target_returns_not_collected(tmp_path):
    adapter = make_adapter(tmp_path)
    # No XML written: a compile error produced no test results.
    with patch.object(type(adapter), "_run_suite", return_value=(1, COMPILE_FAILED_OUTPUT, "")):
        verdict = adapter.run(PASS)
    assert verdict.target_outcome == NOT_COLLECTED
    assert "pollNanos" in verdict.target_failure or "BUILD FAILED" in verdict.target_failure


def test_compile_failure_without_target_sets_error(tmp_path):
    adapter = make_adapter(tmp_path)
    with patch.object(type(adapter), "_run_suite", return_value=(1, COMPILE_FAILED_OUTPUT, "")):
        verdict = adapter.run()
    assert verdict.error is not None
    assert verdict.passed == []
    assert verdict.failed == []


def test_compile_failure_includes_error_lines(tmp_path):
    adapter = make_adapter(tmp_path)
    with patch.object(type(adapter), "_run_suite", return_value=(1, COMPILE_FAILED_OUTPUT, "")):
        verdict = adapter.run()
    assert "e: " in verdict.error or "unresolved reference" in verdict.error


def test_test_failure_is_failed_not_not_collected(tmp_path):
    """BUILD FAILED with XML present is a test failure, not a compile error."""
    adapter = make_adapter(tmp_path)
    with patch.object(
        type(adapter),
        "_run_suite",
        side_effect=suite_writing(adapter, JUNIT_XML, 1, TEST_FAILED_OUTPUT),
    ):
        verdict = adapter.run(FAIL)
    assert verdict.target_outcome == FAILED


# ---------------------------------------------------------------------------
# run() — filter matched nothing → not_found
# ---------------------------------------------------------------------------


def test_absent_target_returns_not_found(tmp_path):
    adapter = make_adapter(tmp_path)
    target = "android-app::com.example.PollCadenceTest/doesNotExist"
    with patch.object(type(adapter), "_run_suite", return_value=(1, NO_TESTS_OUTPUT, "")):
        verdict = adapter.run(target)
    assert verdict.target_outcome == NOT_FOUND
    assert verdict.error is None


# ---------------------------------------------------------------------------
# run() — targeted command construction
# ---------------------------------------------------------------------------


def test_targeted_run_appends_tests_filter(tmp_path):
    adapter = make_adapter(tmp_path)
    commands_run = []

    def capture(cmd, env=None):
        commands_run.append(cmd)
        write_results(adapter, JUNIT_XML)
        return (0, "", "")

    with patch.object(type(adapter), "_run_suite", side_effect=capture):
        adapter.run(PASS)

    assert len(commands_run) == 1
    assert "--tests com.example.PollCadenceTest.scalesOnlyUnderE2E" in commands_run[0]


def test_full_suite_run_has_no_tests_filter(tmp_path):
    adapter = make_adapter(tmp_path)
    commands_run = []

    def capture(cmd, env=None):
        commands_run.append(cmd)
        write_results(adapter, JUNIT_XML)
        return (0, "", "")

    with patch.object(type(adapter), "_run_suite", side_effect=capture):
        adapter.run()

    assert len(commands_run) == 1
    assert "--tests" not in commands_run[0]


def test_gradle_filter_translates_slash_to_dot(tmp_path):
    adapter = make_adapter(tmp_path)
    assert (
        adapter._gradle_filter("com.example.PollCadenceTest/scalesOnlyUnderE2E")
        == "com.example.PollCadenceTest.scalesOnlyUnderE2E"
    )


def test_default_command_is_gradlew_test(tmp_path):
    adapter = make_adapter(tmp_path, TOML_DEFAULT_CMD)
    assert adapter._test_cmd() == "./gradlew test"


# ---------------------------------------------------------------------------
# Stale-result handling
# ---------------------------------------------------------------------------


def test_stale_results_are_cleared_before_run(tmp_path):
    adapter = make_adapter(tmp_path)
    # A previous run left XML for a test that is not run this time.
    stale = """\
<testsuite name="com.example.OldTest" tests="1" failures="0">
  <testcase name="staleCase" classname="com.example.OldTest"/>
</testsuite>
"""
    write_results(adapter, stale, task="oldTask")

    with patch.object(
        type(adapter), "_run_suite", side_effect=suite_writing(adapter, JUNIT_XML, 1)
    ):
        verdict = adapter.run()

    ids = verdict.passed + verdict.failed
    assert not any("OldTest" in i for i in ids)


def test_result_files_finds_instrumented_xml(tmp_path):
    adapter = make_adapter(tmp_path)
    inst = (
        adapter.root
        / "build"
        / "outputs"
        / "androidTest-results"
        / "connected"
        / "TEST-emulator.xml"
    )
    inst.parent.mkdir(parents=True, exist_ok=True)
    inst.write_text(JUNIT_XML)
    assert inst in adapter._result_files()


# ---------------------------------------------------------------------------
# collect() — per-file grep fallback
# ---------------------------------------------------------------------------


def test_grep_extracts_ids_from_kotlin_file(tmp_path):
    adapter = make_adapter(tmp_path)
    kt = write_kotlin(
        tmp_path / "android-app" / "src" / "test" / "PollCadenceTest.kt",
        """\
package com.example

import org.junit.Test

class PollCadenceTest {
    @Test
    fun scalesOnlyUnderE2E() { }

    @Test
    fun flooredAtOneSecond() { }
}
""",
    )
    ids = adapter._grep_tests(kt)
    assert PASS in ids
    assert FAIL in ids


def test_collect_walks_test_files(tmp_path):
    adapter = make_adapter(tmp_path)
    write_kotlin(
        tmp_path / "android-app" / "src" / "test" / "PollCadenceTest.kt",
        """\
package com.example

import org.junit.Test

class PollCadenceTest {
    @Test fun scalesOnlyUnderE2E() { }
}
""",
    )
    collection = adapter.collect()
    assert PASS in collection.tests


def test_collect_records_failed_file_on_read_error(tmp_path, monkeypatch):
    adapter = make_adapter(tmp_path)
    bad = tmp_path / "android-app" / "src" / "test" / "Broken.kt"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("package com.example\nclass BrokenTest { @Test fun x() {} }")

    def boom(path, *a, **kw):
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "read_text", boom)
    collection = adapter.collect()
    assert any("Broken.kt" in k for k in collection.failed_files)


def test_grep_qualifies_with_package(tmp_path):
    adapter = make_adapter(tmp_path)
    kt = write_kotlin(
        tmp_path / "android-app" / "src" / "test" / "NoPkgTest.kt",
        """\
import org.junit.Test

class NoPkgTest {
    @Test fun works() { }
}
""",
    )
    ids = adapter._grep_tests(kt)
    # No package declaration → id is Class/method with no package prefix.
    assert "android-app::NoPkgTest/works" in ids


# ---------------------------------------------------------------------------
# Doctor gate + stub_hint
# ---------------------------------------------------------------------------


def test_collectable_is_ok(tmp_path):
    adapter = make_adapter(tmp_path)
    assert adapter.collectable().ok is True


def test_stub_hint_mentions_compile_and_not_collected(tmp_path):
    adapter = make_adapter(tmp_path)
    hint = adapter.stub_hint()
    assert "compile" in hint.lower()
    assert "not_collected" in hint
