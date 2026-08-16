"""Failure text keeps the tail, where Python puts the error (#17).

`target_failure` was truncated to a fixed budget from the head. Deep tracebacks
(async frameworks, ORMs, HTTP stacks) exceed it easily, delivering frames of
framework internals and cutting exactly the line that says what went wrong —
forcing a manual re-run outside tdd to see an error the tool already had.
Both ends are kept: the head carries the assertion line for plain failures,
the tail carries the exception for deep ones.
"""

from __future__ import annotations

import json
from pathlib import Path

from tddcli import adapters
from tddcli import config as config_mod
from tddcli.adapters.base import clip_failure


def test_short_text_passes_through_unclipped():
    assert clip_failure("boom", 1500) == "boom"


def test_long_text_keeps_both_ends_and_marks_the_elision():
    text = "assert first line\n" + ("framework frame\n" * 200) + "ConnectionRefusedError: [Errno 61]"
    clipped = clip_failure(text, 1500)
    assert len(clipped) <= 1500 + 20   # the marker is the only overhead
    assert clipped.startswith("assert first line")
    assert clipped.endswith("ConnectionRefusedError: [Errno 61]")
    assert "…" in clipped


def _pytest_adapter(tmp_path):
    (tmp_path / "tdd.toml").write_text(
        "[project.backend]\n"
        'root         = "backend"\n'
        'adapter      = "pytest"\n'
        'test_paths   = ["tests/"]\n'
        'test_command = "pytest tests"\n'
    )
    return adapters.build(config_mod.load(tmp_path).project("backend"), tmp_path)


def test_pytest_target_failure_keeps_the_error_at_the_tail(tmp_path, monkeypatch):
    adapter = _pytest_adapter(tmp_path)
    longrepr = ("connector frame\n" * 300) + "ConnectionRefusedError: [Errno 61]"

    def fake(command, cwd, timeout=1800, extra_env=None, label=None):
        marker = "--json-report-file="
        path = command.split(marker, 1)[1].split(" --", 1)[0]
        Path(path.strip("'\"")).write_text(json.dumps({
            "tests": [{
                "nodeid": "tests/test_db.py::test_connects",
                "outcome": "failed",
                "call": {"longrepr": longrepr},
            }],
        }))
        return 1, "", ""

    monkeypatch.setattr(adapters.base, "run_command", fake)
    verdict = adapter.run("backend::tests/test_db.py::test_connects")
    assert verdict.target_failure.endswith("ConnectionRefusedError: [Errno 61]")
    assert len(verdict.target_failure) <= 1520
