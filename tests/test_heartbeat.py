"""Baseline and sweep heartbeats to stderr (issue #1).

PRD §8: "Every command emits JSON on stdout with a common envelope" — `run_cli` does
`json.loads(stdout)`. Prepending NDJSON there breaks the envelope contract and every
existing test, so the heartbeat goes to stderr instead; nothing in `src/` writes
there today. `run_cli`/`run_cli_text` redirect stdout only, so these tests capture
stderr with `capsys` (P6 confirmed this works).

See tasks/multi-agent-feedback.md Part B.
"""

from __future__ import annotations

import json

from conftest import run_cli, write_plan
from tddcli import adapters, gitutil
from tddcli.ledger import Ledger

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


def register(repo):
    plan = write_plan(repo, PLAN)
    reg = run_cli(repo, "plan", "register", plan)
    assert reg["ok"], reg
    return plan


def _heartbeat_lines(stderr: str) -> list[dict]:
    lines = []
    for line in stderr.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            lines.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return lines


def test_baseline_captured_line_is_written_per_project(repo, capsys):
    plan = register(repo)
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out

    captured = capsys.readouterr()
    lines = [
        line for line in _heartbeat_lines(captured.err)
        if line.get("event") == "baseline_captured"
    ]
    assert lines, "no baseline_captured line in stderr"
    backend = next((line for line in lines if line.get("project") == "backend"), None)
    assert backend is not None, lines
    assert isinstance(backend["test_count"], int)


def test_baseline_heartbeat_reports_elapsed_seconds(repo, capsys):
    plan = register(repo)
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out

    captured = capsys.readouterr()
    lines = [
        line for line in _heartbeat_lines(captured.err)
        if line.get("event") == "baseline_captured"
    ]
    backend = next((line for line in lines if line.get("project") == "backend"), None)
    assert backend is not None, lines
    assert isinstance(backend["elapsed_s"], (int, float))


def test_claim_records_projects_done_as_each_completes(repo_multi, monkeypatch):
    """Seam, proven by P6: `monkeypatch.setattr(adapters, "build", spy)`. `build` is
    called once per project in `tdd.toml` order (`['backend', 'frontend']`), so the
    row seen on the second call reports `projects_done == 1` and
    `projects_total == 2`."""
    plan = register(repo_multi)
    real_build = adapters.build
    seen: list[dict | None] = []

    def spy(project, worktree):
        led = Ledger(gitutil.repo_identity(worktree))
        claim = led.active_claim(str(worktree))
        seen.append(claim)
        return real_build(project, worktree)

    monkeypatch.setattr(adapters, "build", spy)

    out = run_cli(repo_multi, "run", "start", "--plan", plan)
    assert out["ok"], out

    assert len(seen) == 2, seen
    second = seen[1]
    assert second is not None
    assert second["projects_done"] == 1, second
