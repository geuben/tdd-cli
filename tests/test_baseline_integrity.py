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


TEST_ADD = """from app.calc import add


def test_add_two_numbers():
    assert add(2, 3) == 5
"""


def reach_refactor(repo):
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    run_cli(repo, "advance")
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    out = run_cli(repo, "advance")
    assert out["run"]["phase"] == "AWAITING_REFACTOR", out


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


def test_a_failure_the_baseline_missed_has_its_own_blocker_kind(repo):
    """Filing it as `regression` is the only option today, which mislabels the run's
    integrity record as a defect the agent caused."""
    reach_refactor(repo)
    (repo / "backend" / "tests" / "test_smoke.py").write_text(
        "def test_smoke():\n    assert False\n"
    )
    assert run_cli(repo, "advance")["next_action"]["verb"] == "fix_regression"

    out = run_cli(repo, "blocker", "--kind", "pre_existing_failure", "--detail", "flaky")
    assert out["ok"], out
    assert out["result"]["kind"] == "pre_existing_failure"


def test_unblocking_can_accept_the_failures_into_the_baseline(repo):
    """Without this the run cannot recover: unblock returns to AWAITING_REFACTOR, the
    next advance re-runs the same sweep, finds the same failure, and blocks again."""
    reach_refactor(repo)
    (repo / "backend" / "tests" / "test_smoke.py").write_text(
        "def test_smoke():\n    assert False\n"
    )
    run_cli(repo, "advance")
    run_cli(repo, "blocker", "--kind", "pre_existing_failure", "--detail", "flaky")

    resumed = run_cli(
        repo, "resume", "--unblock", "--note", "verified against main", "--accept-failures"
    )
    assert resumed["ok"], resumed
    accepted = resumed["result"]["accepted_into_baseline"]
    assert accepted == {"backend": ["backend::tests/test_smoke.py::test_smoke"]}, resumed

    closed = run_cli(repo, "advance")
    assert closed["next_action"]["verb"] == "complete", closed


def test_unblocking_without_accept_failures_leaves_the_baseline_alone(repo):
    """The escape hatch is explicit, or every unblock quietly launders a regression."""
    reach_refactor(repo)
    (repo / "backend" / "tests" / "test_smoke.py").write_text(
        "def test_smoke():\n    assert False\n"
    )
    run_cli(repo, "advance")
    run_cli(repo, "blocker", "--kind", "pre_existing_failure", "--detail", "flaky")

    resumed = run_cli(repo, "resume", "--unblock", "--note", "looking into it")
    assert resumed["ok"], resumed
    assert "accepted_into_baseline" not in resumed["result"]
    assert run_cli(repo, "advance")["next_action"]["verb"] == "fix_regression"
