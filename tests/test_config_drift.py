"""The registry is a reviewed file rather than ledger state — so the ledger pins it.

Config lives in git because it is branch-scoped, reviewable and needed to interpret
historical runs. The cost of that choice is that an agent can edit it mid-run, and one
edit is load-bearing: widening `test_paths` to match implementation files would
reclassify implementation as tests and silently disable the RED-commit detection.
"""

from __future__ import annotations

from conftest import run_cli, write_plan

PLAN = """---
cycles:
  - n: 1
    project: backend
    test: "tests/test_add.py::test_add"
    stub_expected: ["app/calc.py"]
---
"""

TEST = """from app.calc import add


def test_add():
    assert add(1, 1) == 2
"""


def start(repo):
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    return run_cli(repo, "run", "start", "--plan", plan)


def widen_test_paths(repo):
    (repo / "tdd.toml").write_text(
        '[project.backend]\n'
        'root       = "backend"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["**/*.py"]\n'   # everything is now "a test"
        "lint       = []\n"
        "typecheck  = []\n"
    )


def test_config_is_pinned_at_run_start(repo):
    started = start(repo)
    assert started["ok"], started
    metrics = run_cli(repo, "metrics")["result"]["runs"][0]
    assert "config_changed" not in metrics["integrity_events"]


def test_widening_test_paths_mid_run_is_recorded(repo):
    start(repo)
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    widen_test_paths(repo)

    run_cli(repo, "advance")
    metrics = run_cli(repo, "metrics")["result"]["runs"][0]
    assert metrics["integrity_events"]["config_changed"] == 1


def test_config_drift_is_recorded_once_per_distinct_change(repo):
    start(repo)
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    widen_test_paths(repo)

    run_cli(repo, "advance")
    run_cli(repo, "advance", "--retry")
    metrics = run_cli(repo, "metrics")["result"]["runs"][0]
    assert metrics["integrity_events"]["config_changed"] == 1


def test_drift_appears_in_the_friction_log(repo):
    start(repo)
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    widen_test_paths(repo)
    run_cli(repo, "advance")

    run_cli(repo, "log", "render", "--out", str(repo / "friction.md"))
    assert "config_changed" in (repo / "friction.md").read_text()
