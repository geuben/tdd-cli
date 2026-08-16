"""Where a slow command actually spent its time.

A `run start` took 23 minutes and reported one number per project — `elapsed_s`,
covering `run()` and `collect()` together. Answering "which of the two?" required
measuring the projects by hand, outside the tool, in a different checkout; the
warm numbers that produced did not match the cold ones and the first diagnosis
drawn from them was wrong.

The tool already holds both timings at the moment it discards them. Two seams
make them visible:

* `baseline_captured` reports `run_s` and `collect_s` separately, so the split is
  in the output the agent already prints.
* `run_command` — the single choke point every subprocess passes through — emits a
  `command_timing` line under `TDD_TIMING=1`, which attributes cost per command:
  per-file collection, gates, doctor probes, artifact hooks. Off by default,
  because the per-file loop would otherwise emit one line per test file on every
  invocation.
"""

from __future__ import annotations

import json

from conftest import run_cli, write_plan
from tddcli.adapters import base

PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    stub_expected: ["app/calc.py"]
    commit_red: "test: adding two numbers"
    commit_green: "feat: add()"
---

# Plan
"""


def _lines(stderr: str, event: str) -> list[dict]:
    found = []
    for line in stderr.splitlines():
        try:
            payload = json.loads(line.strip())
        except json.JSONDecodeError:
            continue
        if payload.get("event") == event:
            found.append(payload)
    return found


def _start(repo):
    plan = write_plan(repo, PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    return run_cli(repo, "run", "start", "--plan", plan)


def test_baseline_reports_run_and_collect_separately(repo, capsys):
    out = _start(repo)
    assert out["ok"], out

    backend = next(
        line for line in _lines(capsys.readouterr().err, "baseline_captured")
        if line["project"] == "backend"
    )
    assert isinstance(backend["run_s"], (int, float)), backend
    assert isinstance(backend["collect_s"], (int, float)), backend


def test_the_split_still_adds_up_to_the_reported_total(repo, capsys):
    """`elapsed_s` stays, so existing consumers keep working — and it must remain
    the sum of the parts, or the split is describing a different thing."""
    out = _start(repo)
    assert out["ok"], out

    backend = next(
        line for line in _lines(capsys.readouterr().err, "baseline_captured")
        if line["project"] == "backend"
    )
    assert backend["run_s"] + backend["collect_s"] <= backend["elapsed_s"] + 0.05
    assert backend["elapsed_s"] - (backend["run_s"] + backend["collect_s"]) < 0.5


def test_command_timing_is_silent_unless_asked_for(repo, capsys, monkeypatch):
    monkeypatch.delenv(base.TIMING_ENV, raising=False)
    assert _start(repo)["ok"]
    assert _lines(capsys.readouterr().err, "command_timing") == []


def test_command_timing_names_the_command_and_its_cost(repo, capsys, monkeypatch):
    monkeypatch.setenv(base.TIMING_ENV, "1")
    assert _start(repo)["ok"]

    timings = _lines(capsys.readouterr().err, "command_timing")
    assert timings, "TDD_TIMING=1 produced no command_timing lines"
    for entry in timings:
        assert isinstance(entry["duration_ms"], int)
        assert entry["command"]
        assert isinstance(entry["exit_code"], int)


def test_a_timed_command_is_attributed_to_its_caller(repo, capsys, monkeypatch):
    """Without a label the rows are readable but not groupable: `run_command` sees
    a command string and a cwd, not which project or phase asked for it."""
    monkeypatch.setenv(base.TIMING_ENV, "1")
    assert _start(repo)["ok"]

    timings = _lines(capsys.readouterr().err, "command_timing")
    labels = {entry.get("label") for entry in timings}
    assert "suite" in labels, labels
    assert "collect" in labels, labels


def test_the_per_file_collect_loop_is_attributed_per_file(repo, capsys, monkeypatch):
    """The loop's cost is per file, so its timing has to be too — a single total
    cannot say which file is slow."""
    monkeypatch.setenv(base.TIMING_ENV, "1")
    assert _start(repo)["ok"]

    collects = [
        entry for entry in _lines(capsys.readouterr().err, "command_timing")
        if entry.get("label") == "collect"
    ]
    assert collects, "no collect timings"
    assert any("test_smoke.py" in entry["command"] for entry in collects), collects


def test_timing_does_not_disturb_the_command_result(repo, monkeypatch):
    """The wrapper returns exactly what the subprocess returned."""
    monkeypatch.setenv(base.TIMING_ENV, "1")
    code, out, err = base.run_command("echo hello", repo)
    assert code == 0
    assert out.strip() == "hello"
