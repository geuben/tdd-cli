"""xctest adapter — pinned against real xcodebuild stdout patterns.

All tests run without Xcode installed: they exercise the parsing and
command-construction logic against fake output strings, exactly as
test_vitest_adapter.py tests vitest parsing with captured vitest output.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from tddcli import config as config_mod
from tddcli.adapters.base import FAILED, NOT_COLLECTED, NOT_FOUND, PASSED
from tddcli.adapters.xctest_adapter import _CASE_RE, _ENUMERATE_LINE_RE, XCTestAdapter

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

TOML = """
[project.native-ios]
root         = "native-ios"
adapter      = "xctest"
test_paths   = ["CoParentTests/"]
test_command = "xcodebuild test -project CoParent.xcodeproj -scheme CoParentTests -destination 'platform=iOS Simulator,name=CoParent-Unit'"
"""

TOML_NO_CMD = """
[project.native-ios]
root       = "native-ios"
adapter    = "xctest"
test_paths = ["CoParentTests/"]
"""

# Verbatim xcodebuild stdout for a two-test run: one passes, one fails
XCODEBUILD_OUTPUT = """\
Test Suite 'All tests' started at 2026-08-17 09:48:00.000.
Test Suite 'CoParentTests.xctest' started at 2026-08-17 09:48:00.001.
Test Suite 'PollCadenceTests' started at 2026-08-17 09:48:00.002.
Test Case '-[CoParentTests.PollCadenceTests testPollIntervalScalesOnlyUnderE2E]' started.
Test Case '-[CoParentTests.PollCadenceTests testPollIntervalScalesOnlyUnderE2E]' passed (0.001 seconds).
Test Case '-[CoParentTests.PollCadenceTests testScaledIntervalIsFlooredAtOneSecond]' started.
/path/to/test.swift:42: error: -[CoParentTests.PollCadenceTests testScaledIntervalIsFlooredAtOneSecond] : XCTAssertEqual failed: ("500000000") is not equal to ("1000000000") -
Test Case '-[CoParentTests.PollCadenceTests testScaledIntervalIsFlooredAtOneSecond]' failed (0.002 seconds).
Test Suite 'PollCadenceTests' failed at 2026-08-17 09:48:00.004.
Test Suite 'CoParentTests.xctest' failed at 2026-08-17 09:48:00.005.
Test Suite 'All tests' failed at 2026-08-17 09:48:00.006.
** TEST FAILED **
"""

BUILD_FAILED_OUTPUT = """\
/path/to/Transport.swift:99: error: use of unresolved identifier 'pollNanos'
** BUILD FAILED **
"""

ENUMERATE_OUTPUT = """\
CoParentTests/PollCadenceTests/testPollIntervalScalesOnlyUnderE2E
CoParentTests/PollCadenceTests/testScaledIntervalIsFlooredAtOneSecond
CoParentTests/E2ESeamTests/testE2EFlagIsDisabledByDefault
"""


def make_adapter(tmp_path: Path, toml: str = TOML) -> XCTestAdapter:
    (tmp_path / "tdd.toml").write_text(toml)
    (tmp_path / "native-ios" / "CoParentTests").mkdir(parents=True)
    cfg = config_mod.load(tmp_path)
    return XCTestAdapter(cfg.project("native-ios"), tmp_path)


def write_swift(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


# ---------------------------------------------------------------------------
# Regex patterns — pin against real xcodebuild output shapes
# ---------------------------------------------------------------------------


def test_case_re_matches_passed_line():
    m = _CASE_RE.search(
        "Test Case '-[CoParentTests.PollCadenceTests testPollIntervalScalesOnlyUnderE2E]'"
        " passed (0.001 seconds)."
    )
    assert m is not None
    bundle, class_, method, outcome = m.groups()
    assert bundle == "CoParentTests"
    assert class_ == "PollCadenceTests"
    assert method == "testPollIntervalScalesOnlyUnderE2E"
    assert outcome == "passed"


def test_case_re_matches_failed_line():
    m = _CASE_RE.search(
        "Test Case '-[CoParentTests.PollCadenceTests testScaledIntervalIsFlooredAtOneSecond]'"
        " failed (0.002 seconds)."
    )
    assert m is not None
    assert m.group(4) == "failed"


def test_enumerate_line_re_matches_three_part_id():
    m = _ENUMERATE_LINE_RE.search(
        "CoParentTests/PollCadenceTests/testPollIntervalScalesOnlyUnderE2E"
    )
    assert m is not None
    assert (m.group(1), m.group(2), m.group(3)) == (
        "CoParentTests",
        "PollCadenceTests",
        "testPollIntervalScalesOnlyUnderE2E",
    )


def test_enumerate_line_re_ignores_non_test_lines():
    assert _ENUMERATE_LINE_RE.search("** BUILD FAILED **") is None
    assert _ENUMERATE_LINE_RE.search("Test Suite 'All tests' started") is None


# ---------------------------------------------------------------------------
# Test id format
# ---------------------------------------------------------------------------


def test_run_output_produces_project_namespaced_ids(tmp_path):
    adapter = make_adapter(tmp_path)
    with patch.object(type(adapter), "_run_suite", return_value=(1, XCODEBUILD_OUTPUT, "")):
        verdict = adapter.run()
    assert (
        "native-ios::CoParentTests/PollCadenceTests/testPollIntervalScalesOnlyUnderE2E"
        in verdict.passed
    )
    assert (
        "native-ios::CoParentTests/PollCadenceTests/testScaledIntervalIsFlooredAtOneSecond"
        in verdict.failed
    )


def test_ids_are_project_prefixed_and_root_relative(tmp_path):
    adapter = make_adapter(tmp_path)
    with patch.object(type(adapter), "_run_suite", return_value=(0, XCODEBUILD_OUTPUT, "")):
        verdict = adapter.run()
    for id_ in verdict.passed + verdict.failed:
        assert id_.startswith("native-ios::")


# ---------------------------------------------------------------------------
# run() — verdict parsing
# ---------------------------------------------------------------------------


def test_passed_test_appears_in_passed(tmp_path):
    adapter = make_adapter(tmp_path)
    with patch.object(type(adapter), "_run_suite", return_value=(0, XCODEBUILD_OUTPUT, "")):
        verdict = adapter.run()
    assert len(verdict.passed) == 1
    assert len(verdict.failed) == 1


def test_failed_test_output_is_captured(tmp_path):
    adapter = make_adapter(tmp_path)
    target = "native-ios::CoParentTests/PollCadenceTests/testScaledIntervalIsFlooredAtOneSecond"
    with patch.object(type(adapter), "_run_suite", return_value=(1, XCODEBUILD_OUTPUT, "")):
        verdict = adapter.run(target)
    assert verdict.target_outcome == FAILED
    assert "XCTAssertEqual failed" in verdict.target_failure


def test_passing_targeted_run_sets_passed(tmp_path):
    adapter = make_adapter(tmp_path)
    target = "native-ios::CoParentTests/PollCadenceTests/testPollIntervalScalesOnlyUnderE2E"
    with patch.object(type(adapter), "_run_suite", return_value=(0, XCODEBUILD_OUTPUT, "")):
        verdict = adapter.run(target)
    assert verdict.target_outcome == PASSED


def test_absent_target_returns_not_found(tmp_path):
    adapter = make_adapter(tmp_path)
    target = "native-ios::CoParentTests/PollCadenceTests/testDoesNotExist"
    with patch.object(type(adapter), "_run_suite", return_value=(0, XCODEBUILD_OUTPUT, "")):
        verdict = adapter.run(target)
    assert verdict.target_outcome == NOT_FOUND


# ---------------------------------------------------------------------------
# run() — build failure maps to not_collected
# ---------------------------------------------------------------------------


def test_build_failure_with_target_returns_not_collected(tmp_path):
    adapter = make_adapter(tmp_path)
    target = "native-ios::CoParentTests/PollCadenceTests/testPollIntervalScalesOnlyUnderE2E"
    with patch.object(type(adapter), "_run_suite", return_value=(65, BUILD_FAILED_OUTPUT, "")):
        verdict = adapter.run(target)
    assert verdict.target_outcome == NOT_COLLECTED
    assert "pollNanos" in verdict.target_failure or "BUILD FAILED" in verdict.target_failure


def test_build_failure_without_target_sets_error(tmp_path):
    adapter = make_adapter(tmp_path)
    with patch.object(type(adapter), "_run_suite", return_value=(65, BUILD_FAILED_OUTPUT, "")):
        verdict = adapter.run()
    assert verdict.error is not None
    assert verdict.passed == []
    assert verdict.failed == []


def test_build_failure_includes_compiler_error_lines(tmp_path):
    adapter = make_adapter(tmp_path)
    with patch.object(type(adapter), "_run_suite", return_value=(65, BUILD_FAILED_OUTPUT, "")):
        verdict = adapter.run()
    assert "error:" in verdict.error


# ---------------------------------------------------------------------------
# run() — targeted command construction
# ---------------------------------------------------------------------------


def test_targeted_run_appends_only_testing_flag(tmp_path):
    adapter = make_adapter(tmp_path)
    target = "native-ios::CoParentTests/PollCadenceTests/testFoo"
    commands_run = []

    def capture_suite(cmd, env=None):
        commands_run.append(cmd)
        return (0, XCODEBUILD_OUTPUT, "")

    with patch.object(type(adapter), "_run_suite", side_effect=capture_suite):
        adapter.run(target)

    assert len(commands_run) == 1
    assert "-only-testing:CoParentTests/PollCadenceTests/testFoo" in commands_run[0]


def test_full_suite_run_does_not_add_only_testing(tmp_path):
    adapter = make_adapter(tmp_path)
    commands_run = []

    def capture_suite(cmd, env=None):
        commands_run.append(cmd)
        return (0, XCODEBUILD_OUTPUT, "")

    with patch.object(type(adapter), "_run_suite", side_effect=capture_suite):
        adapter.run()

    assert len(commands_run) == 1
    assert "-only-testing:" not in commands_run[0]


# ---------------------------------------------------------------------------
# collect() — enumerate-tests batch path
# ---------------------------------------------------------------------------


def test_enumerate_tests_batch_parses_ids(tmp_path):
    adapter = make_adapter(tmp_path)
    with patch.object(
        type(adapter),
        "_enumerate_tests",
        return_value={
            "native-ios::CoParentTests/PollCadenceTests/testPollIntervalScalesOnlyUnderE2E",
            "native-ios::CoParentTests/PollCadenceTests/testScaledIntervalIsFlooredAtOneSecond",
            "native-ios::CoParentTests/E2ESeamTests/testE2EFlagIsDisabledByDefault",
        },
    ):
        collection = adapter.collect()
    assert len(collection.tests) == 3
    assert (
        "native-ios::CoParentTests/E2ESeamTests/testE2EFlagIsDisabledByDefault" in collection.tests
    )


def test_enumerate_tests_appends_flag_to_command(tmp_path):
    adapter = make_adapter(tmp_path)
    commands_run = []

    def fake_run(cmd, cwd, extra_env=None, label=None):
        commands_run.append(cmd)
        return (0, ENUMERATE_OUTPUT, "")

    with patch("tddcli.adapters.xctest_adapter.run_command", side_effect=fake_run):
        adapter._enumerate_tests()

    assert len(commands_run) == 1
    assert commands_run[0].endswith("-enumerate-tests")


def test_enumerate_tests_returns_none_on_failure(tmp_path):
    adapter = make_adapter(tmp_path)
    with patch(
        "tddcli.adapters.xctest_adapter.run_command", return_value=(1, "", "xcodebuild error")
    ):
        result = adapter._enumerate_tests()
    assert result is None


def test_enumerate_tests_returns_none_when_no_ids_parsed(tmp_path):
    adapter = make_adapter(tmp_path)
    with patch(
        "tddcli.adapters.xctest_adapter.run_command",
        return_value=(0, "some non-matching output\n", ""),
    ):
        result = adapter._enumerate_tests()
    assert result is None


# ---------------------------------------------------------------------------
# collect() — per-file Swift grep fallback
# ---------------------------------------------------------------------------


def test_grep_extracts_ids_from_swift_file(tmp_path):
    adapter = make_adapter(tmp_path)
    swift = write_swift(
        tmp_path / "native-ios" / "CoParentTests" / "PollCadenceTests.swift",
        """\
import XCTest

class PollCadenceTests: XCTestCase {
    func testPollIntervalScalesOnlyUnderE2E() {
        XCTAssertEqual(1, 1)
    }
    func testScaledIntervalIsFlooredAtOneSecond() {
        XCTAssertEqual(2, 2)
    }
}
""",
    )
    ids = adapter._grep_swift_tests(swift, "CoParentTests")
    assert "native-ios::CoParentTests/PollCadenceTests/testPollIntervalScalesOnlyUnderE2E" in ids
    assert (
        "native-ios::CoParentTests/PollCadenceTests/testScaledIntervalIsFlooredAtOneSecond" in ids
    )


def test_grep_fallback_used_when_enumerate_fails(tmp_path):
    adapter = make_adapter(tmp_path)
    write_swift(
        tmp_path / "native-ios" / "CoParentTests" / "E2ESeamTests.swift",
        """\
import XCTest

class E2ESeamTests: XCTestCase {
    func testE2EFlagIsDisabledByDefault() { }
}
""",
    )
    with patch.object(type(adapter), "_enumerate_tests", return_value=None):
        collection = adapter.collect()
    assert (
        "native-ios::CoParentTests/E2ESeamTests/testE2EFlagIsDisabledByDefault" in collection.tests
    )


def test_bundle_extracted_from_scheme_flag(tmp_path):
    adapter = make_adapter(tmp_path)
    assert adapter._bundle_from_test_command() == "CoParentTests"


def test_bundle_falls_back_to_unknown_without_scheme(tmp_path):
    adapter = make_adapter(tmp_path, TOML_NO_CMD)
    assert adapter._bundle_from_test_command() == "Unknown"


def test_per_file_failed_file_recorded_on_read_error(tmp_path, monkeypatch):
    adapter = make_adapter(tmp_path)
    bad = tmp_path / "native-ios" / "CoParentTests" / "Broken.swift"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("class BrokenTests: XCTestCase { }")

    def boom(path, *a, **kw):
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "read_text", boom)

    with patch.object(type(adapter), "_enumerate_tests", return_value=None):
        collection = adapter.collect()

    assert any("Broken.swift" in k for k in collection.failed_files)


# ---------------------------------------------------------------------------
# Doctor gate — collectable()
# ---------------------------------------------------------------------------


def test_collectable_ok_when_test_command_set(tmp_path):
    adapter = make_adapter(tmp_path)
    result = adapter.collectable()
    assert result.ok is True


def test_collectable_fails_when_no_test_command(tmp_path):
    adapter = make_adapter(tmp_path, TOML_NO_CMD)
    result = adapter.collectable()
    assert result.ok is False
    assert "test_command" in result.output
    assert "xcodebuild test" in result.output


# ---------------------------------------------------------------------------
# stub_hint
# ---------------------------------------------------------------------------


def test_stub_hint_mentions_build_and_compile(tmp_path):
    adapter = make_adapter(tmp_path)
    hint = adapter.stub_hint()
    assert "build" in hint.lower() or "compil" in hint.lower()
    assert "not_collected" in hint or "not RED" in hint


# ---------------------------------------------------------------------------
# _failure_for — isolates one test's assertion lines
# ---------------------------------------------------------------------------


def test_failure_for_extracts_assertion_lines(tmp_path):
    adapter = make_adapter(tmp_path)
    detail = adapter._failure_for(
        XCODEBUILD_OUTPUT, "CoParentTests/PollCadenceTests/testScaledIntervalIsFlooredAtOneSecond"
    )
    assert "XCTAssertEqual failed" in detail
    # Should not contain lines from the other test
    assert "testPollIntervalScalesOnlyUnderE2E" not in detail


def test_failure_for_with_bad_id_returns_clipped_combined(tmp_path):
    adapter = make_adapter(tmp_path)
    # A two-part id (no bundle) falls back to returning the full output
    detail = adapter._failure_for(XCODEBUILD_OUTPUT, "PollCadenceTests/testFoo")
    assert len(detail) > 0
