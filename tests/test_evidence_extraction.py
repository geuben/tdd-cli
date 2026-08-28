"""Per-adapter evidence line extraction (issue #68).

Each adapter extracts a single plausible assertion/failure line from its
runner output, stored as Verdict.target_evidence, so that the sensitivity
check's observed: line is auditable even under xdist headers or console noise.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import tddcli.adapters.base as adapters_base
from tddcli import adapters
from tddcli import config as config_mod
from tddcli.adapters.xctest_adapter import XCTestAdapter


_XCTEST_TOML = (
    "[project.native-ios]\n"
    'root         = "native-ios"\n'
    'adapter      = "xctest"\n'
    'test_paths   = ["AppTests/"]\n'
    'test_command = "xcodebuild test -project App.xcodeproj -scheme AppTests"\n'
)


def _xctest_adapter(tmp_path):
    (tmp_path / "tdd.toml").write_text(_XCTEST_TOML)
    (tmp_path / "native-ios" / "AppTests").mkdir(parents=True)
    return XCTestAdapter(config_mod.load(tmp_path).project("native-ios"), tmp_path)


def _pytest_adapter(tmp_path):
    (tmp_path / "tdd.toml").write_text(
        "[project.backend]\n"
        'root         = "backend"\n'
        'adapter      = "pytest"\n'
        'test_paths   = ["tests/"]\n'
        'test_command = "pytest tests"\n'
    )
    return adapters.build(config_mod.load(tmp_path).project("backend"), tmp_path)


def test_pytest_evidence_is_empty_when_no_assertion_line_exists(tmp_path, monkeypatch):
    adapter = _pytest_adapter(tmp_path)
    longrepr = (
        "tests/test_calc.py:10: RecursionError\n"
        "RecursionError: maximum recursion depth exceeded\n"
    )

    def fake(command, cwd, timeout=1800, extra_env=None, label=None):
        marker = "--json-report-file="
        path = command.split(marker, 1)[1].split(" --", 1)[0]
        Path(path.strip("'\"")).write_text(json.dumps({
            "tests": [{
                "nodeid": "tests/test_calc.py::test_recurse",
                "outcome": "failed",
                "call": {"longrepr": longrepr},
            }],
        }))
        return 1, "", ""

    monkeypatch.setattr(adapters_base, "run_command", fake)
    verdict = adapter.run("backend::tests/test_calc.py::test_recurse")
    assert verdict.target_evidence == ""


def test_pytest_evidence_is_the_assertion_line_not_the_xdist_header(tmp_path, monkeypatch):
    adapter = _pytest_adapter(tmp_path)
    longrepr = (
        "[gw0] darwin -- Python 3.12.8 /tmp/x/bin/python\n"
        "\n"
        "tests/test_calc.py:10: in test_add\n"
        "    assert result == expected\n"
        "E       AssertionError: reversed mismatch\n"
        "E       assert [1, 2] == [2, 1]\n"
        "+   Where:\n"
        "    expected = [2, 1]\n"
    )

    def fake(command, cwd, timeout=1800, extra_env=None, label=None):
        marker = "--json-report-file="
        path = command.split(marker, 1)[1].split(" --", 1)[0]
        Path(path.strip("'\"")).write_text(json.dumps({
            "tests": [{
                "nodeid": "tests/test_calc.py::test_add",
                "outcome": "failed",
                "call": {"longrepr": longrepr},
            }],
        }))
        return 1, "", ""

    monkeypatch.setattr(adapters_base, "run_command", fake)
    verdict = adapter.run("backend::tests/test_calc.py::test_add")
    assert verdict.target_evidence == "AssertionError: reversed mismatch"


def test_xctest_evidence_is_the_error_line_not_console_noise(tmp_path):
    adapter = _xctest_adapter(tmp_path)
    target = "native-ios::AppTests/RecTests/testStopsRecording"
    canned = (
        "Test Suite 'All tests' started at 2026-08-27 10:00:00.000.\n"
        "Test Case '-[AppTests.RecTests testStopsRecording]' started.\n"
        "2026-08-27 10:00:00.001 AppTests[1234:5678] Socket SO_ERROR [61: Connection refused]\n"
        "/Users/x/RecTests.swift:42: error: -[AppTests.RecTests testStopsRecording] :"
        " XCTAssertEqual failed: (\"recording\") is not equal to (\"stopped\")\n"
        "Test Case '-[AppTests.RecTests testStopsRecording]' failed (0.002 seconds).\n"
        "Test Suite 'All tests' failed at 2026-08-27 10:00:00.003.\n"
        "** TEST FAILED **\n"
    )
    with patch.object(type(adapter), "_run_suite", return_value=(1, canned, "")):
        verdict = adapter.run(target)
    assert "XCTAssertEqual failed" in verdict.target_evidence
    assert "Socket SO_ERROR" not in verdict.target_evidence
