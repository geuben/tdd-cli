"""`tdd progress` — the human's view. `status` remains the agent's machine view."""

from __future__ import annotations


from conftest import run_cli, run_cli_text, write_plan

PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add"
    stub_expected: ["app/calc.py"]
  - n: 2
    project: backend
    refactor_cycle: true
    title: "tidy the call sites"
    files: ["app/calc.py"]
  - n: 3
    project: backend
    title: "subtracting"
    test: "tests/test_sub.py::test_sub"
---
"""

TEST = "from app.calc import add\n\n\ndef test_add():\n    assert add(1, 1) == 2\n"


def start(repo):
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    return run_cli(repo, "run", "start", "--plan", plan)


def progress_text(repo):
    return run_cli_text(repo, "progress")


def test_progress_lists_every_declared_cycle_before_any_run(repo):
    start(repo)
    text = progress_text(repo)
    assert "3 cycles" in text
    for title in ("adding two numbers", "tidy the call sites", "subtracting"):
        assert title in text
    assert "0/3 closed" in text
    assert "no integrity events" in text


def test_progress_marks_the_current_cycle_and_its_phase(repo):
    start(repo)
    text = progress_text(repo)
    assert "▸  1" in text
    assert "NOW: writing test" in text


def test_progress_shows_closed_cycles_with_their_commits(repo):
    start(repo)
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    run_cli(repo, "advance")
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    run_cli(repo, "advance")
    run_cli(repo, "advance")

    text = progress_text(repo)
    assert "✓  1" in text
    assert "red:" in text and "green:" in text
    assert "1/3 closed" in text
    assert "▸  2" in text


def test_progress_reports_skips_with_the_reason(repo):
    start(repo)
    run_cli(repo, "cycle", "skip", "--reason", "the plan counted direct raises")
    text = progress_text(repo)
    assert "⊘  1" in text
    assert "the plan counted direct raises" in text
    assert "1 skipped" in text


def test_progress_surfaces_integrity_events(repo):
    start(repo)
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST)
    run_cli(repo, "advance")  # passes on arrival -> red_first_violation

    text = progress_text(repo)
    assert "! red_first_violation" in text
    assert "red_first_violation×1" in text


def test_progress_reports_a_blocker(repo):
    start(repo)
    run_cli(repo, "blocker", "--kind", "plan_defect", "--detail", "cycle 1 is void")
    text = progress_text(repo)
    assert "BLOCKED (plan_defect): cycle 1 is void" in text


def test_progress_emits_no_json_envelope(repo):
    start(repo)
    out = run_cli_text(repo, "progress")
    assert '"next_action"' not in out
    assert "cycles ·" in out


def test_progress_json_flag_returns_machine_output(repo):
    start(repo)
    out = run_cli_text(repo, "progress", "--json")
    assert '"next_action"' in out
