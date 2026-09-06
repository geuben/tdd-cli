"""pytest-xdist `--dist loadgroup` node ids.

A test marked `@pytest.mark.xdist_group("<group>")` is reported by xdist's loadgroup
scheduler as `<nodeid>@<group>`, and pytest-json-report records that spelling. The
adapter must read the plain id back out, or every grouped target is `not_found` even
though it is collected and passes (geuben/coparenting run 187, 2026-09-06).
"""

from __future__ import annotations

import json
from pathlib import Path

from tddcli import adapters
from tddcli import config as config_mod


def _pytest_project(tmp_path: Path):
    (tmp_path / "tdd.toml").write_text(
        "[project.backend]\n"
        'root         = "backend"\n'
        'adapter      = "pytest"\n'
        'test_paths   = ["tests/"]\n'
        'test_command = "pytest tests"\n'
    )
    return config_mod.load(tmp_path).project("backend")


def _fake_pytest_run(report: dict):
    """A run_command double that writes `report` where pytest-json-report would."""

    def fake(command, cwd, timeout=1800, extra_env=None, label=None):
        marker = "--json-report-file="
        assert marker in command, command
        path = command.split(marker, 1)[1].split(" --", 1)[0]
        Path(path.strip("'\"")).write_text(json.dumps(report))
        return 0, "", ""

    return fake


def test_pytest_run_matches_target_reported_with_xdist_group_suffix(tmp_path, monkeypatch):
    adapter = adapters.build(_pytest_project(tmp_path), tmp_path)
    monkeypatch.setattr(
        adapters.base,
        "run_command",
        _fake_pytest_run(
            {
                "duration": 1.0,
                "tests": [
                    {
                        "nodeid": "tests/test_a.py::test_a@restate_workflows",
                        "outcome": "passed",
                    }
                ],
            }
        ),
    )

    verdict = adapter.run("backend::tests/test_a.py::test_a")

    assert verdict.error is None
    assert verdict.target_outcome == "passed"
    assert verdict.passed == ["backend::tests/test_a.py::test_a"]
