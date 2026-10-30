"""Why each failing test failed (#105): the adapters work it out, the ledger keeps it
per invocation, and the friction log and `tdd invocation show` print it."""

from __future__ import annotations

import json
import textwrap
from unittest.mock import patch

from conftest import git, run_cli, write_plan
from tddcli import adapters, gitutil, render
from tddcli import config as config_mod
from tddcli.adapters.base import FailureDetail
from tddcli.adapters.cargo_adapter import CargoAdapter
from tddcli.ledger import Ledger
from test_baseline_integrity import PLAN, TEST_ADD, reach_refactor
from test_cargo_adapter import FULL_RUN, make_adapter
from test_evidence_extraction import (
    _exec_adapter,
    _gradle_adapter,
    _gradle_write_results,
    _vitest_adapter,
    _write_script,
    _xctest_adapter,
)


def _at(minute):
    return f"2026-09-01T10:{minute:02d}:00+00:00"


def _run(ledger):
    """One contract and one run on a fresh fixture ledger."""
    contract = ledger.insert(
        "plan_contract",
        plan_path="tasks/p.md",
        status="declared",
        declared_cycles=json.dumps([{"n": 1}]),
        annotation_keys="[]",
        registered_at=_at(0),
    )
    return ledger.insert(
        "run",
        plan_contract_id=contract,
        executor_model="m",
        executor_source="declared",
        worktree_path="/wt",
        started_at=_at(0),
        ended_at=_at(10),
        outcome="completed",
        preexisting_dirty="[]",
    )


def test_an_invocation_keeps_the_failure_details_it_was_recorded_with(tmp_path, ledger_home):
    ledger = Ledger(tmp_path / "somerepo")
    run_id = _run(ledger)
    inv = ledger.record_invocation(
        run_id,
        None,
        phase_at="CLOSE_SWEEP",
        project="p",
        adapter="pytest",
        target_test=None,
        target_outcome=None,
        target_failure="",
        total_passed=0,
        total_failed=2,
        other_failures=["p::b", "p::a"],
        duration_ms=1,
        tree_hash=None,
        failures={
            "p::b": {"phase": None, "message": "FAIL: b", "detail": "b out"},
            "p::a": {"phase": "teardown", "message": "RuntimeError: a", "detail": "a out"},
        },
    )
    assert [dict(r) for r in ledger.failure_details(inv)] == [
        {"test_id": "p::a", "phase": "teardown", "message": "RuntimeError: a", "detail": "a out"},
        {"test_id": "p::b", "phase": None, "message": "FAIL: b", "detail": "b out"},
    ]


PHASES = textwrap.dedent(
    """\
    import pytest


    @pytest.fixture
    def broken_setup():
        raise RuntimeError("setup boom")


    @pytest.fixture
    def broken_teardown():
        yield
        raise RuntimeError("teardown boom")


    def test_passes():
        pass


    def test_fails_in_call():
        assert 1 == 2, "values differ"


    def test_fails_in_setup(broken_setup):
        pass


    def test_fails_in_teardown(broken_teardown):
        pass


    def test_fails_in_call_and_teardown(broken_teardown):
        raise ValueError("call boom")


    @pytest.mark.xfail(strict=True)
    def test_passes_unexpectedly():
        pass
    """
)


def test_pytest_reports_each_failure_with_the_phase_that_failed(tmp_path):
    (tmp_path / "tdd.toml").write_text(
        '[project.backend]\nroot = "backend"\nadapter = "pytest"\ntest_paths = ["tests/"]\n'
    )
    (tmp_path / "backend" / "tests").mkdir(parents=True)
    (tmp_path / "backend" / "tests" / "test_phases.py").write_text(PHASES)

    v = adapters.build(config_mod.load(tmp_path).project("backend"), tmp_path).run(None)

    prefix = "backend::tests/test_phases.py::"
    assert {
        tid: (d.phase, d.message, d.message in d.detail) for tid, d in v.failure_details.items()
    } == {
        prefix + "test_fails_in_call": ("call", "AssertionError: values differ", True),
        prefix + "test_fails_in_setup": ("setup", "RuntimeError: setup boom", True),
        prefix + "test_fails_in_teardown": ("teardown", "RuntimeError: teardown boom", True),
        prefix + "test_fails_in_call_and_teardown": ("call", "ValueError: call boom", True),
        prefix + "test_passes_unexpectedly": ("call", "[XPASS(strict)]", True),
    }


SMOKE_BROKE = 'def test_smoke():\n    assert 1 == 2, "smoke broke"\n'


def _invocations(repo, phase):
    """Every invocation of the repo's latest run in `phase`, in order."""
    ledger = Ledger(gitutil.repo_identity(repo))
    run = ledger.latest_run(str(repo))
    rows = [inv for c in ledger.cycles(run["id"]) for inv in ledger.invocations(c["id"], phase)]
    return ledger, rows


def test_a_green_run_records_why_its_other_failures_failed(repo):
    (repo / "backend" / "tests" / "test_flaky.py").write_text(
        "def test_flaky():\n    assert False\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "a baseline failure")
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    run_cli(repo, "advance")
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    (repo / "backend" / "tests" / "test_smoke.py").write_text(SMOKE_BROKE)
    run_cli(repo, "advance")

    ledger, rows = _invocations(repo, "AWAITING_IMPL")
    inv = next(r for r in rows if json.loads(r["other_failures"]))
    assert [
        (r["test_id"], r["phase"], r["message"]) for r in ledger.failure_details(inv["id"])
    ] == [("backend::tests/test_smoke.py::test_smoke", "call", "AssertionError: smoke broke")]


def test_a_close_sweep_records_why_its_failures_failed(repo):
    reach_refactor(repo)
    (repo / "backend" / "tests" / "test_smoke.py").write_text(SMOKE_BROKE)
    run_cli(repo, "advance")

    ledger, rows = _invocations(repo, "CLOSE_SWEEP")
    sweep = rows[-1]
    assert [
        (r["test_id"], r["phase"], r["message"]) for r in ledger.failure_details(sweep["id"])
    ] == [("backend::tests/test_smoke.py::test_smoke", "call", "AssertionError: smoke broke")]


def test_vitest_reports_each_failure_with_its_first_message_line(tmp_path):
    adapter = _vitest_adapter(tmp_path)
    message = (
        "AssertionError: expected 2 to be 3 // Object.is equality\n"
        "    at Object.<anonymous> (calc.test.ts:5:14)\n"
    )
    report = {
        "testResults": [
            {
                "name": str(tmp_path / "frontend" / "calc.test.ts"),
                "status": "failed",
                "assertionResults": [
                    {
                        "fullName": "calc add returns the sum",
                        "status": "failed",
                        "failureMessages": [message],
                    },
                    {"fullName": "calc add is pure", "status": "passed", "failureMessages": []},
                ],
            }
        ],
    }
    with patch.object(type(adapter), "_run_suite", return_value=(1, json.dumps(report), "")):
        verdict = adapter.run(None)
    assert verdict.failure_details == {
        "frontend::calc.test.ts > calc add returns the sum": FailureDetail(
            phase=None,
            message="AssertionError: expected 2 to be 3 // Object.is equality",
            detail=message,
        )
    }


def test_cargo_reports_each_failure_with_its_panic_line(tmp_path):
    adapter = make_adapter(tmp_path)
    with patch.object(CargoAdapter, "_run_suite", return_value=(101, FULL_RUN, "")):
        verdict = adapter.run(None)
    panic = "thread 'layout::tests::fails_on_purpose' (173172849) panicked at src/lib.rs:7:41:"
    assert verdict.failure_details == {
        "kernel::lib::layout::tests::fails_on_purpose": FailureDetail(
            phase=None,
            message=panic,
            detail=panic + "\nassertion `left == right` failed: expected width mismatch\n"
            "  left: 2\n right: 3\n"
            "note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace",
        )
    }


def test_gradle_reports_each_failure_with_its_failure_message(tmp_path):
    adapter = _gradle_adapter(tmp_path)
    junit_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<testsuite name="com.example.CalcTest" tests="2" failures="1">\n'
        '  <testcase name="add" classname="com.example.CalcTest" time="0.010">\n'
        '    <failure message="expected:&lt;1000&gt; but was:&lt;500&gt;"'
        ' type="org.opentest4j.AssertionFailedError">'
        "org.opentest4j.AssertionFailedError: expected:&lt;1000&gt; but was:&lt;500&gt;\n"
        "\tat com.example.CalcTest.add(CalcTest.kt:10)\n"
        "</failure>\n"
        "  </testcase>\n"
        '<testcase name="sub" classname="com.example.CalcTest" time="0.010"/>'
        "</testsuite>\n"
    )

    def side_effect(cmd, env=None):
        _gradle_write_results(adapter, junit_xml)
        return (1, "", "")

    with patch.object(type(adapter), "_run_suite", side_effect=side_effect):
        verdict = adapter.run(None)
    assert verdict.failure_details == {
        "android-app::com.example.CalcTest/add": FailureDetail(
            phase=None,
            message="expected:<1000> but was:<500>",
            detail="expected:<1000> but was:<500>\n"
            "org.opentest4j.AssertionFailedError: expected:<1000> but was:<500>\n"
            "\tat com.example.CalcTest.add(CalcTest.kt:10)",
        )
    }


def test_xctest_reports_each_failure_with_its_error_line(tmp_path):
    adapter = _xctest_adapter(tmp_path)
    error = (
        "/Users/x/RecTests.swift:42: error: -[AppTests.RecTests testStopsRecording] :"
        ' XCTAssertEqual failed: ("recording") is not equal to ("stopped")'
    )
    noise = "2026-08-27 10:00:00.001 AppTests[1234:5678] Socket SO_ERROR [61: Connection refused]"
    canned = (
        "Test Suite 'All tests' started at 2026-08-27 10:00:00.000.\n"
        "Test Case '-[AppTests.RecTests testStopsRecording]' started.\n"
        f"{noise}\n"
        f"{error}\n"
        "Test Case '-[AppTests.RecTests testStopsRecording]' failed (0.002 seconds).\n"
        "Test Case '-[AppTests.RecTests testStarts]' started.\n"
        "Test Case '-[AppTests.RecTests testStarts]' passed (0.001 seconds).\n"
        "Test Suite 'All tests' failed at 2026-08-27 10:00:00.003.\n"
        "** TEST FAILED **\n"
    )
    with patch.object(type(adapter), "_run_suite", return_value=(1, canned, "")):
        verdict = adapter.run(None)
    assert verdict.failure_details == {
        "native-ios::AppTests/RecTests/testStopsRecording": FailureDetail(
            phase=None, message=error, detail=f"{noise}\n{error}"
        )
    }


def test_exec_reports_each_failing_script_with_its_last_output_line(tmp_path):
    adapter = _exec_adapter(tmp_path)
    scripts = tmp_path / "gates" / "scripts"
    _write_script(
        scripts / "check-deploy.sh",
        'echo "INFO: starting deployment"\necho "FAIL: expected exit 0, got 1"; exit 1',
    )
    _write_script(scripts / "check-ok.sh", "exit 0")
    verdict = adapter.run(None)
    assert verdict.failure_details == {
        "gates::scripts/check-deploy.sh": FailureDetail(
            phase=None,
            message="FAIL: expected exit 0, got 1",
            detail="INFO: starting deployment\nFAIL: expected exit 0, got 1",
        )
    }


def test_the_friction_log_lists_each_invocations_failures(tmp_path, ledger_home):
    ledger = Ledger(tmp_path / "somerepo")
    run_id = _run(ledger)
    cycle_id = ledger.insert(
        "cycle",
        run_id=run_id,
        ordinal=1,
        kind="standard",
        projects='["p"]',
        declared_tests="[]",
        target_tests="[]",
        phase="CLOSED",
        head_at_open="0" * 40,
        opened_at=_at(0),
        closed_at=_at(4),
    )
    ledger.record_invocation(
        run_id,
        cycle_id,
        phase_at="CLOSE_SWEEP",
        project="p",
        adapter="pytest",
        target_test=None,
        target_outcome=None,
        target_failure="",
        total_passed=0,
        total_failed=2,
        other_failures=["p::tests/test_a.py::test_a", "p::tests/test_b.py::test_b"],
        duration_ms=1,
        tree_hash=None,
        failures={
            "p::tests/test_a.py::test_a": {
                "phase": "teardown",
                "message": "RuntimeError: session teardown boom",
                "detail": "x",
            },
            "p::tests/test_b.py::test_b": {
                "phase": None,
                "message": "FAIL: expected exit 0",
                "detail": "y",
            },
        },
    )
    block = [
        "- **Failures — invocation 1 (CLOSE_SWEEP, p):**",
        "  - `p::tests/test_a.py::test_a` [teardown]: RuntimeError: session teardown boom",
        "  - `p::tests/test_b.py::test_b`: FAIL: expected exit 0",
    ]
    assert "\n".join(block) in render.friction_log(ledger, ledger.run(run_id))
