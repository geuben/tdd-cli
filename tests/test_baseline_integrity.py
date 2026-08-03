"""A baseline is subtracted from every later failure set (R9.2). An empty one that
merely *looks* clean turns every pre-existing failure into a permanent regression.
"""

from __future__ import annotations

from conftest import git, run_cli, write_plan

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


def set_test_command(repo, command: str) -> None:
    toml = (repo / "tdd.toml").read_text()
    (repo / "tdd.toml").write_text(toml + f'test_command = "{command}"\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "tdd.toml")


def test_run_start_refuses_when_nothing_could_be_collected(repo):
    """The motivating failure: node_modules were absent, so every frontend test file
    failed to collect, the baseline recorded no failures, and a real pre-existing
    failure was then read as a regression at every close sweep."""
    (repo / "backend" / "tests" / "test_smoke.py").write_text(
        "import a_module_that_does_not_exist\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "break collection")

    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)

    assert out["ok"] is False, out
    assert "backend" in out["error"]
    assert "collect" in out["error"]


def test_run_start_refuses_a_baseline_that_ran_no_tests(repo):
    """Collection found tests, so the suite exists; the runner executed none of them.
    Whatever the cause, nothing was observed and the baseline asserts nothing."""
    set_test_command(repo, "python -m pytest tests/ -k __matches_nothing__")

    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)

    assert out["ok"] is False, out
    assert "backend" in out["error"]
    assert "no tests" in out["error"]


def test_a_project_with_no_tests_at_all_is_not_an_error(repo):
    """Nothing collected and nothing failing to collect: the project simply has no
    suite yet. That is a fact about the project, not a broken environment."""
    (repo / "backend" / "tests" / "test_smoke.py").unlink()
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "no tests")

    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)

    assert out["ok"], out
    assert out["result"]["baselines"]["backend"] == 0
