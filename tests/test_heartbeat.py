"""Baseline and sweep heartbeats to stderr.

A multi-minute silent baseline reads as a hang: harness Bash calls time out and
agents re-run the command. PRD §8: "Every command emits JSON on stdout with a common
envelope" — `run_cli` does `json.loads(stdout)`. Prepending NDJSON there breaks the
envelope contract and every existing test, so the heartbeat goes to stderr instead;
nothing else in `src/` writes there. `run_cli`/`run_cli_text` redirect stdout only,
so these tests capture stderr with `capsys`.
"""

from __future__ import annotations

import json

from conftest import run_cli, write_plan
from tddcli import adapters, gitutil
from tddcli.adapters.base import Collection, Verdict
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

PLAN_MULTI = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    stub_expected: ["app/calc.py"]
    commit_red: "test: adding two numbers"
    commit_green: "feat: add()"
  - n: 2
    project: frontend
    refactor_cycle: true
    commit_refactor: "refactor: frontend structure"
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
    plan = write_plan(repo_multi, PLAN_MULTI)
    run_cli(repo_multi, "plan", "register", plan)
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
    assert second["projects_total"] == 2, second


TEST_ADD = """from app.calc import add


def test_add_two_numbers():
    assert add(2, 3) == 5
"""


def test_sweep_emits_a_project_completed_line(repo, capsys):
    plan = register(repo)
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out

    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    capsys.readouterr()  # discard the run-start heartbeats

    red = run_cli(repo, "advance")
    assert red["next_action"]["verb"] == "write_implementation", red

    captured = capsys.readouterr()
    lines = [
        line for line in _heartbeat_lines(captured.err)
        if line.get("event") == "project_completed"
    ]
    assert lines, "no project_completed line in stderr"
    backend = next((line for line in lines if line.get("project") == "backend"), None)
    assert backend is not None, lines
    assert isinstance(backend["elapsed_s"], (int, float))


def test_close_sweep_emits_a_project_completed_line(repo, capsys):
    """The close sweep is exactly the kind of slow, silent operation the
    heartbeat exists for.

    `Engine.sweep` is a separate method from `Engine.run_projects` and does not
    route through it, so the baseline heartbeat never reached it. The `phase` field
    is what distinguishes the two on a shared channel.
    """
    plan = register(repo)
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]

    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    run_cli(repo, "advance")  # -> AWAITING_IMPL
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    return a + b\n"
    )
    run_cli(repo, "advance")  # -> green, then the close sweep
    capsys.readouterr()

    run_cli(repo, "advance")  # the close sweep itself

    lines = [
        line for line in _heartbeat_lines(capsys.readouterr().err)
        if line.get("event") == "project_completed"
        and line.get("phase") == "CLOSE_SWEEP"
    ]
    assert lines, "no CLOSE_SWEEP project_completed line in stderr"
    assert isinstance(lines[0]["elapsed_s"], (int, float))


THREE_PROJECT_PLAN = """---
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


def test_baseline_captured_lines_emitted_under_concurrency(repo_three, capsys, monkeypatch):
    class FakeAdapter:
        def __init__(self, name):
            self.name = name

        def run(self, target=None):
            return Verdict(project=self.name, adapter="pytest", passed=["t::a"])

        def collect(self):
            return Collection(tests={"t::a", "t::b"})

    def fake_build(project, worktree):
        return FakeAdapter(project.name)

    monkeypatch.setattr(adapters, "build", fake_build)

    plan = write_plan(repo_three, THREE_PROJECT_PLAN)
    run_cli(repo_three, "plan", "register", plan)
    out = run_cli(repo_three, "run", "start", "--plan", plan, "--baseline-jobs", "2")
    assert out["ok"], out

    captured = capsys.readouterr()
    hb_lines = [
        line for line in _heartbeat_lines(captured.err)
        if line.get("event") == "baseline_captured"
    ]
    probed_projects = {line["project"] for line in hb_lines}
    assert probed_projects == {"backend", "svc"}, probed_projects
    for line in hb_lines:
        assert isinstance(line["test_count"], int), line
        assert isinstance(line["elapsed_s"], (int, float)), line
