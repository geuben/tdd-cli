"""Per-pattern suite overrides (R7.13).

Some tests intentionally live outside the project's default runner config —
contract tests that need a live backend being the motivating case. Before
overrides existed, the only way to make such a test collectable was to widen the
default config, which broke CI (the plain suite suddenly made real network
calls) and polluted target adoption with the other suite's tests. The registry
now declares the alternate command per pattern, and collection and runs union
the default suite with every override suite.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest as pytest_framework

from conftest import git, run_cli, write_plan
from tddcli import adapters
from tddcli import config as config_mod
from tddcli.config import ConfigError


def project_with(tmp_path: Path, extra: str, adapter: str = "pytest"):
    (tmp_path / "tdd.toml").write_text(
        "[project.backend]\n"
        'root       = "backend"\n'
        f'adapter    = "{adapter}"\n'
        'test_paths = ["tests/"]\n' + extra
    )
    return config_mod.load(tmp_path).project("backend")


OVERRIDE_BLOCK = (
    "[[project.backend.override]]\n"
    'pattern         = "contract/"\n'
    'test_command    = "pytest contract"\n'
    'collect_command = "pytest contract -p no:cacheprovider"\n'
    "env             = { API_URL = \"http://localhost:${TDD_TEST_PORT}\" }\n"
)


# -- registry ------------------------------------------------------------


def test_override_is_parsed_from_the_registry(tmp_path):
    project = project_with(tmp_path, OVERRIDE_BLOCK)
    (ov,) = project.overrides
    assert ov.pattern == "contract/"
    assert ov.test_command == "pytest contract"
    assert ov.collect_command == "pytest contract -p no:cacheprovider"
    assert ov.env == {"API_URL": "http://localhost:${TDD_TEST_PORT}"}


def test_override_without_pattern_or_command_is_refused(tmp_path):
    with pytest_framework.raises(ConfigError, match="has no pattern"):
        project_with(
            tmp_path, '[[project.backend.override]]\ntest_command = "pytest x"\n'
        )
    with pytest_framework.raises(ConfigError, match="has no test_command"):
        project_with(tmp_path, '[[project.backend.override]]\npattern = "x/"\n')


def test_override_env_must_be_string_valued(tmp_path):
    with pytest_framework.raises(ConfigError, match="env must be a table"):
        project_with(
            tmp_path,
            "[[project.backend.override]]\n"
            'pattern      = "x/"\n'
            'test_command = "pytest x"\n'
            "env          = { PORT = 9600 }\n",
        )


def test_override_for_matches_like_test_paths_first_declared_wins(tmp_path):
    project = project_with(
        tmp_path,
        "[[project.backend.override]]\n"
        'pattern      = "contract/smoke/**"\n'
        'test_command = "pytest contract/smoke"\n'
        "[[project.backend.override]]\n"
        'pattern      = "contract/"\n'
        'test_command = "pytest contract"\n'
        "[[project.backend.override]]\n"
        'pattern      = "legacy"\n'
        'test_command = "pytest legacy"\n',
    )
    assert project.override_for("contract/smoke/test_a.py").test_command == (
        "pytest contract/smoke"
    )
    assert project.override_for("contract/test_b.py").test_command == "pytest contract"
    assert project.override_for("legacy/test_old.py").test_command == "pytest legacy"
    assert project.override_for("tests/test_c.py") is None


def test_override_files_classify_as_tests_without_repeating_test_paths(tmp_path):
    """Staging classification must see override files as tests: otherwise a RED
    commit containing only the new contract test is flagged as implementation
    written during RED."""
    project = project_with(tmp_path, OVERRIDE_BLOCK)
    assert project.is_test_file("backend/contract/test_api.py")
    assert not project.is_test_file("backend/app/api.py")


# -- pytest adapter ------------------------------------------------------


def _fake_pytest_run(reports_by_prefix: dict[str, dict], seen: list):
    """A run_command double that answers each suite command with its own report,
    keyed by command prefix, writing the JSON where the real plugin would."""

    def fake(command, cwd, timeout=1800, extra_env=None, label=None):
        seen.append((command, extra_env))
        for prefix, report in reports_by_prefix.items():
            if command.startswith(prefix):
                marker = "--json-report-file="
                if marker in command:
                    path = command.split(marker, 1)[1].split(" --", 1)[0]
                    Path(path.strip("'\"")).write_text(json.dumps(report))
                return 1 if report.get("tests") else 0, "", ""
        raise AssertionError(f"unexpected command: {command}")

    return fake


def test_pytest_run_unions_default_and_override_suites(tmp_path, monkeypatch):
    project = project_with(
        tmp_path,
        'test_command = "pytest tests"\n' + OVERRIDE_BLOCK,
    )
    adapter = adapters.build(project, tmp_path)
    seen: list = []
    monkeypatch.setattr(
        adapters.base,
        "run_command",
        _fake_pytest_run(
            {
                "pytest tests": {
                    "duration": 1.0,
                    "tests": [{"nodeid": "tests/test_a.py::test_a", "outcome": "passed"}],
                },
                "pytest contract": {
                    "duration": 2.0,
                    "tests": [
                        {
                            "nodeid": "contract/test_api.py::test_ping",
                            "outcome": "failed",
                            "call": {"longrepr": "boom"},
                        }
                    ],
                },
            },
            seen,
        ),
    )
    verdict = adapter.run("backend::contract/test_api.py::test_ping")
    assert verdict.error is None
    assert verdict.target_outcome == "failed"
    assert verdict.target_failure == "boom"
    assert verdict.passed == ["backend::tests/test_a.py::test_a"]
    assert verdict.failed == ["backend::contract/test_api.py::test_ping"]
    assert verdict.duration_ms == 3000
    assert [c.split(" --json-report", 1)[0] for c, _ in seen] == [
        "pytest tests",
        "pytest contract",
    ]


def test_pytest_override_env_reaches_the_suite_with_vars_expanded(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("TDD_TEST_PORT", "9600")
    project = project_with(tmp_path, 'test_command = "pytest tests"\n' + OVERRIDE_BLOCK)
    adapter = adapters.build(project, tmp_path)
    seen: list = []
    monkeypatch.setattr(
        adapters.base,
        "run_command",
        _fake_pytest_run(
            {"pytest tests": {"tests": []}, "pytest contract": {"tests": []}}, seen
        ),
    )
    adapter.run(None)
    (_, default_env), (_, override_env) = seen
    assert "API_URL" not in default_env
    assert override_env["API_URL"] == "http://localhost:9600"


def test_pytest_broken_override_suite_is_a_loud_error_not_a_silent_gap(
    tmp_path, monkeypatch
):
    """Swallowing a report-less override run would resolve a target living in that
    suite as `not_found`, sending the agent to rewrite a perfectly good test."""
    project = project_with(tmp_path, 'test_command = "pytest tests"\n' + OVERRIDE_BLOCK)
    adapter = adapters.build(project, tmp_path)

    def fake(command, cwd, timeout=1800, extra_env=None, label=None):
        if command.startswith("pytest contract"):
            return 4, "", "ERROR: file or directory not found: contract"
        marker = "--json-report-file="
        path = command.split(marker, 1)[1].split(" --", 1)[0]
        Path(path.strip("'\"")).write_text(json.dumps({"tests": []}))
        return 0, "", ""

    monkeypatch.setattr(adapters.base, "run_command", fake)
    verdict = adapter.run("backend::contract/test_api.py::test_ping")
    assert verdict.error is not None
    assert "pytest contract" in verdict.error


def test_pytest_collection_routes_override_files_to_the_override_command(
    tmp_path, monkeypatch
):
    project = project_with(tmp_path, OVERRIDE_BLOCK)
    (tmp_path / "backend" / "tests").mkdir(parents=True)
    (tmp_path / "backend" / "contract").mkdir()
    (tmp_path / "backend" / "tests" / "test_a.py").write_text("def test_a(): pass\n")
    (tmp_path / "backend" / "contract" / "test_api.py").write_text(
        "def test_ping(): pass\n"
    )
    adapter = adapters.build(project, tmp_path)
    seen: list = []

    def fake(command, cwd, timeout=1800, extra_env=None, label=None):
        seen.append((command, extra_env))
        name = "test_api.py::test_ping" if "contract" in command else "test_a.py::test_a"
        return 0, name, ""

    monkeypatch.setattr(adapters.pytest_adapter, "run_command", fake)
    collection = adapter.collect()
    assert collection.tests == {
        "backend::test_a.py::test_a",
        "backend::test_api.py::test_ping",
    }
    contract_calls = [c for c, _ in seen if "contract/test_api.py" in c]
    assert contract_calls and contract_calls[0].startswith(
        "pytest contract -p no:cacheprovider --collect-only -q"
    )


# -- vitest adapter ------------------------------------------------------


VITEST_OVERRIDE = (
    'test_command    = "npx vitest run"\n'
    "[[project.backend.override]]\n"
    'pattern         = "contract/"\n'
    'test_command    = "npx vitest run --config vitest.contract.config.ts"\n'
    'collect_command = "npx vitest list --config vitest.contract.config.ts"\n'
)


def _vitest_report(file_path: str, full_name: str, status: str) -> dict:
    return {
        "duration": 5,
        "testResults": [
            {
                "name": file_path,
                "status": status,
                "assertionResults": [
                    {"fullName": full_name, "status": status, "failureMessages": ["nope"]}
                ],
            }
        ],
    }


def test_vitest_run_finds_a_target_that_only_the_override_config_reaches(
    tmp_path, monkeypatch
):
    project = project_with(tmp_path, VITEST_OVERRIDE, adapter="vitest")
    adapter = adapters.build(project, tmp_path)

    def fake(command, cwd, timeout=1800, extra_env=None, label=None):
        if "--config vitest.contract.config.ts" in command:
            report = _vitest_report(
                str(tmp_path / "backend" / "contract" / "api.contract.test.ts"),
                "pings the api",
                "failed",
            )
        else:
            report = _vitest_report(
                str(tmp_path / "backend" / "unit.test.ts"), "adds", "passed"
            )
        return 1, json.dumps(report), ""

    monkeypatch.setattr(adapters.base, "run_command", fake)
    target = "backend::contract/api.contract.test.ts > pings the api"
    verdict = adapter.run(target)
    assert verdict.error is None
    assert verdict.target_outcome == "failed"
    assert verdict.target_failure == "nope"
    assert verdict.passed == ["backend::unit.test.ts > adds"]


def test_vitest_override_without_collect_command_fails_the_collectable_gate(
    tmp_path, monkeypatch
):
    """Fail at run start, not per-file mid-cycle: `vitest list` knows nothing of
    the override config, and falling back to the override's *run* command would
    execute the suite — against a live backend — just to enumerate it."""
    project = project_with(
        tmp_path,
        "[[project.backend.override]]\n"
        'pattern      = "contract/"\n'
        'test_command = "npx vitest run --config vitest.contract.config.ts"\n',
        adapter="vitest",
    )
    adapter = adapters.build(project, tmp_path)
    monkeypatch.setattr(
        adapters.vitest_adapter, "run_command", lambda *a, **k: (0, "", "")
    )
    gate = adapter.collectable()
    assert not gate.ok
    assert "collect_command" in gate.output

    (tmp_path / "backend" / "contract").mkdir(parents=True)
    (tmp_path / "backend" / "contract" / "api.contract.test.ts").write_text("")
    collection = adapter.collect()
    assert "contract/api.contract.test.ts" in collection.failed_files


def test_vitest_collection_routes_override_files_to_the_override_command(
    tmp_path, monkeypatch
):
    project = project_with(tmp_path, VITEST_OVERRIDE, adapter="vitest")
    (tmp_path / "backend" / "contract").mkdir(parents=True)
    contract_file = tmp_path / "backend" / "contract" / "api.contract.test.ts"
    contract_file.write_text("")
    adapter = adapters.build(project, tmp_path)
    seen: list = []

    def fake(command, cwd, timeout=1800, extra_env=None, label=None):
        seen.append(command)
        return 0, "contract/api.contract.test.ts > pings the api", ""

    monkeypatch.setattr(adapters.vitest_adapter, "run_command", fake)
    collection = adapter.collect()
    assert collection.tests == {
        "backend::contract/api.contract.test.ts > pings the api"
    }
    # R7.13's requirement is that the override's own command enumerates its files —
    # not that it does so one file at a time. Collection batches per declared suite
    # (issue #27), so the override's command is one of the invocations rather than
    # the first, and carries no file argument.
    assert any(
        c.startswith("npx vitest list --config vitest.contract.config.ts") for c in seen
    ), seen

    # With every suite listable the gate passes: the probe must not manufacture a
    # failure out of a healthy override.
    assert adapter.collectable().ok


# -- end to end ----------------------------------------------------------


PLAN = """---
cycles:
  - n: 1
    project: backend
    test: "contract/test_api.py::test_add_via_api"
---
"""


def test_a_cycle_can_target_a_test_only_an_override_suite_reaches(repo):
    """The full RED → GREEN path for a target the default command never runs.

    The default suite is pinned to `pytest tests`, so nothing under `contract/`
    is reachable by it; before overrides this cycle could not reach RED at all.
    """
    (repo / "backend" / "contract").mkdir()
    (repo / "backend" / "contract" / "test_ping.py").write_text(
        "def test_ping():\n    assert True\n"
    )
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    (repo / "tdd.toml").write_text(
        "[project.backend]\n"
        'root         = "backend"\n'
        'adapter      = "pytest"\n'
        'test_paths   = ["tests/"]\n'
        'test_command = "pytest tests"\n'
        "lint         = []\n"
        "typecheck    = []\n"
        "[[project.backend.override]]\n"
        'pattern      = "contract/"\n'
        'test_command = "pytest contract"\n'
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "declare the contract-suite override")

    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    start = run_cli(repo, "run", "start", "--plan", plan)
    assert start["ok"], start

    (repo / "backend" / "contract" / "test_api.py").write_text(
        "from app.calc import add\n\n\n"
        "def test_add_via_api():\n    assert add(2, 2) == 4\n"
    )
    red = run_cli(repo, "advance")
    assert red["next_action"]["verb"] == "write_implementation", red

    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    return a + b\n"
    )
    green = run_cli(repo, "advance")
    assert green["next_action"]["verb"] == "refactor_or_advance", green


# -- overlap between the default suite and an override suite -------------
#
# The feature's premise is "files the default runner config cannot reach". A
# bare default command (plain `pytest`) quietly breaks that premise: its own
# discovery sweeps the override directories, the union then holds the same test
# twice — once observed without the override's command/env — and target
# matching judged the target by whichever suite reported it first. That failure
# is opaque (the test fails on some downstream assertion, nothing names the
# overlap), so it must be a loud typed error instead.


def test_pytest_duplicate_nodeid_across_suites_is_a_loud_error(
    tmp_path, monkeypatch
):
    project = project_with(
        tmp_path, 'test_command = "pytest"\n' + OVERRIDE_BLOCK
    )
    adapter = adapters.build(project, tmp_path)
    duplicated = {
        "nodeid": "contract/test_api.py::test_ping",
        "outcome": "failed",
        "call": {"longrepr": "assert None == '1'"},
    }
    monkeypatch.setattr(
        adapters.base,
        "run_command",
        _fake_pytest_run(
            {
                # Bare default discovery sweeps contract/ too.
                "pytest --json-report": {"duration": 1.0, "tests": [duplicated]},
                "pytest contract": {
                    "duration": 2.0,
                    "tests": [dict(duplicated, outcome="passed")],
                },
            },
            [],
        ),
    )
    verdict = adapter.run("backend::contract/test_api.py::test_ping")
    assert verdict.error is not None
    assert "contract/test_api.py::test_ping" in verdict.error
    assert "more than one suite" in verdict.error
    assert "test_command" in verdict.error


def test_vitest_duplicate_test_id_across_suites_is_a_loud_error(
    tmp_path, monkeypatch
):
    project = project_with(
        tmp_path,
        'test_command = "npx vitest run"\n'
        "[[project.backend.override]]\n"
        'pattern         = "contract/"\n'
        'test_command    = "npx vitest run --config vitest.contract.config.ts"\n'
        'collect_command = "npx vitest list --config vitest.contract.config.ts"\n',
        adapter="vitest",
    )
    adapter = adapters.build(project, tmp_path)
    suite_path = str(tmp_path / "backend" / "contract" / "api.test.ts")

    def result(status):
        return {
            "testResults": [
                {
                    "name": suite_path,
                    "status": status,
                    "assertionResults": [
                        {"fullName": "pings", "status": status}
                    ],
                }
            ]
        }

    def fake(command, cwd, timeout=1800, extra_env=None, label=None):
        if "--config" in command:
            return 0, json.dumps(result("passed")), ""
        return 1, json.dumps(result("failed")), ""

    monkeypatch.setattr(adapters.base, "run_command", fake)
    verdict = adapter.run("backend::contract/api.test.ts > pings")
    assert verdict.error is not None
    assert "contract/api.test.ts > pings" in verdict.error
    assert "more than one suite" in verdict.error


def test_pytest_isolation_probe_flags_default_reach_into_override_files(
    tmp_path, monkeypatch
):
    project = project_with(
        tmp_path, 'test_command = "pytest -n {workers}"\n' + OVERRIDE_BLOCK
    )
    adapter = adapters.build(project, tmp_path)
    seen: list = []

    def fake(command, cwd, timeout=1800, extra_env=None, label=None):
        seen.append(command)
        return 0, (
            "tests/test_a.py::test_a\n"
            "contract/test_api.py::test_ping\n"
            "2 tests collected in 0.01s\n"
        ), ""

    monkeypatch.setattr(adapters.pytest_adapter, "run_command", fake)
    gate = adapter.override_isolation()
    assert gate.ok is False
    assert "contract/test_api.py" in gate.output
    assert "test_command" in gate.output
    # The probe asks the *test* command what it would discover — that is the
    # command whose reach matters at run time — with parallelism disabled.
    assert seen == ["pytest -n 0 --collect-only -q"]


def test_pytest_isolation_probe_passes_when_the_default_suite_is_scoped(
    tmp_path, monkeypatch
):
    project = project_with(
        tmp_path, 'test_command = "pytest tests"\n' + OVERRIDE_BLOCK
    )
    adapter = adapters.build(project, tmp_path)
    monkeypatch.setattr(
        adapters.pytest_adapter,
        "run_command",
        lambda command, cwd, timeout=1800, extra_env=None, label=None: (
            0, "tests/test_a.py::test_a\n", ""
        ),
    )
    gate = adapter.override_isolation()
    assert gate.ok is True


def test_vitest_isolation_probe_flags_default_reach_into_override_files(
    tmp_path, monkeypatch
):
    project = project_with(
        tmp_path,
        "[[project.backend.override]]\n"
        'pattern         = "contract/"\n'
        'test_command    = "npx vitest run --config vitest.contract.config.ts"\n'
        'collect_command = "npx vitest list --config vitest.contract.config.ts"\n',
        adapter="vitest",
    )
    adapter = adapters.build(project, tmp_path)
    seen: list = []

    def fake(command, cwd, timeout=1800, extra_env=None, label=None):
        seen.append(command)
        return 0, (
            "src/__tests__/a.test.ts > adds\n"
            "contract/api.test.ts > pings\n"
        ), ""

    monkeypatch.setattr(adapters.vitest_adapter, "run_command", fake)
    gate = adapter.override_isolation()
    assert gate.ok is False
    assert "contract/api.test.ts" in gate.output
    assert seen == ["npx vitest list"]


def test_isolation_probe_is_free_when_a_project_declares_no_overrides(
    tmp_path, monkeypatch
):
    project = project_with(tmp_path, 'test_command = "pytest tests"\n')
    adapter = adapters.build(project, tmp_path)

    def explode(command, cwd, timeout=1800, extra_env=None, label=None):
        raise AssertionError("no probe should run without overrides")

    monkeypatch.setattr(adapters.pytest_adapter, "run_command", explode)
    assert adapter.override_isolation().ok is True


def test_overlap_error_truncates_past_five_ids():
    ids = [f"contract/test_api.py::test_{i}" for i in range(7)]
    message = adapters.base._overlap_error(ids)
    assert "test_4" in message and "test_5" not in message
    assert "and 2 more" in message
    assert "test_command" in message
