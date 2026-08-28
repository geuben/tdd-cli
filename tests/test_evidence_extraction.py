"""Per-adapter evidence line extraction (issue #68).

Each adapter extracts a single plausible assertion/failure line from its
runner output, stored as Verdict.target_evidence, so that the sensitivity
check's observed: line is auditable even under xdist headers or console noise.
"""

from __future__ import annotations

import json
from pathlib import Path

import tddcli.adapters.base as adapters_base
from tddcli import adapters
from tddcli import config as config_mod


def _pytest_adapter(tmp_path):
    (tmp_path / "tdd.toml").write_text(
        "[project.backend]\n"
        'root         = "backend"\n'
        'adapter      = "pytest"\n'
        'test_paths   = ["tests/"]\n'
        'test_command = "pytest tests"\n'
    )
    return adapters.build(config_mod.load(tmp_path).project("backend"), tmp_path)


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
