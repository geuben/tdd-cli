"""Per-project `env` for the default suite (#16).

Override suites gained an `env` mapping in 0.2.0 because suite commands
sometimes need environment the invoking shell doesn't have. That need is not
specific to override suites: a default suite that reads an infrastructure
endpoint from a variable (a database port varying per worktree being the
motivating shape) previously had no registry-level way to receive it — the
workarounds were baking values into `test_command`, teaching the suite's own
bootstrap to hunt for env files, or exporting variables invisibly in whatever
shell runs `tdd advance`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest as pytest_framework

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


def test_project_env_is_parsed_from_the_registry(tmp_path):
    project = project_with(
        tmp_path, 'env = { TEST_DB_PORT = "${DB_PORT}" }\n'
    )
    assert project.env == {"TEST_DB_PORT": "${DB_PORT}"}


def test_project_env_must_be_string_valued(tmp_path):
    with pytest_framework.raises(ConfigError, match="env must be a table"):
        project_with(tmp_path, "env = { PORT = 6032 }\n")


def test_default_suite_runs_with_the_project_env_expanded(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PORT", "6032")
    project = project_with(
        tmp_path,
        'test_command = "pytest tests"\n'
        'env = { TEST_DB_PORT = "${DB_PORT}" }\n',
    )
    adapter = adapters.build(project, tmp_path)
    seen: list = []

    def fake(command, cwd, timeout=1800, extra_env=None, **_):
        seen.append((command, extra_env))
        marker = "--json-report-file="
        path = command.split(marker, 1)[1].split(" --", 1)[0]
        Path(path.strip("'\"")).write_text(json.dumps({"tests": []}))
        return 0, "", ""

    monkeypatch.setattr(adapters.base, "run_command", fake)
    adapter.run(None)
    ((_, env),) = seen
    assert env["TEST_DB_PORT"] == "6032"


def test_override_env_layers_on_top_of_the_project_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PORT", "6032")
    project = project_with(
        tmp_path,
        'test_command = "pytest tests"\n'
        'env = { TEST_DB_PORT = "${DB_PORT}", SHARED = "from-project" }\n'
        "[[project.backend.override]]\n"
        'pattern      = "contract/"\n'
        'test_command = "pytest contract"\n'
        'env          = { SHARED = "from-override" }\n',
    )
    adapter = adapters.build(project, tmp_path)
    invocations = adapter._suite_invocations()
    assert invocations[0][1] == {"TEST_DB_PORT": "6032", "SHARED": "from-project"}
    assert invocations[1][1] == {"TEST_DB_PORT": "6032", "SHARED": "from-override"}


def test_pytest_collection_of_default_files_carries_the_project_env(
    tmp_path, monkeypatch
):
    project = project_with(tmp_path, 'env = { TEST_DB_PORT = "6032" }\n')
    (tmp_path / "backend" / "tests").mkdir(parents=True)
    (tmp_path / "backend" / "tests" / "test_a.py").write_text(
        "def test_a(): pass\n"
    )
    adapter = adapters.build(project, tmp_path)
    seen: list = []

    def fake(command, cwd, timeout=1800, extra_env=None, **_):
        seen.append((command, extra_env))
        return 0, "tests/test_a.py::test_a\n", ""

    monkeypatch.setattr(adapters.pytest_adapter, "run_command", fake)
    adapter.collect()
    assert seen and all(env == {"TEST_DB_PORT": "6032"} for _, env in seen)


def test_vitest_default_suite_runs_with_the_project_env(tmp_path, monkeypatch):
    project = project_with(
        tmp_path,
        'test_command = "npx vitest run"\n'
        'env = { API_URL = "http://localhost:6032" }\n',
        adapter="vitest",
    )
    adapter = adapters.build(project, tmp_path)
    seen: list = []

    def fake(command, cwd, timeout=1800, extra_env=None, **_):
        seen.append((command, extra_env))
        return 0, json.dumps({"testResults": []}), ""

    monkeypatch.setattr(adapters.base, "run_command", fake)
    adapter.run(None)
    ((_, env),) = seen
    assert env["API_URL"] == "http://localhost:6032"
