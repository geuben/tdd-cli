from pathlib import Path

from conftest import run_cli, write_plan
from tddcli import advance
from tddcli import config as config_mod
from tddcli.adapters.base import Verdict
from tddcli.adapters.vitest_adapter import VitestAdapter

VITEST_TOML = """
[project.frontend]
root       = "frontend"
adapter    = "vitest"
test_paths = ["**/*.test.ts"]
"""


def _vitest_adapter(tmp_path: Path) -> VitestAdapter:
    (tmp_path / "tdd.toml").write_text(VITEST_TOML)
    (tmp_path / "frontend").mkdir()
    cfg = config_mod.load(tmp_path)
    return VitestAdapter(cfg.project("frontend"), tmp_path)

PLAN_SINGLE_CANDIDATE = """---
cycles:
  - n: 1
    project: backend
    title: "add two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    commit_red: "test: add two numbers"
    commit_green: "feat: add()"
---
"""

TEST_ADDING = """\
from app.calc import add


def test_adding():
    assert add(2, 3) == 5
"""

CALC_STUB = """\
def add(a, b):
    raise NotImplementedError
"""


def test_outcome_lookup_returns_none_for_unexecuted_id():
    verdicts = [
        Verdict("p1", "pytest", passed=["p1::tests/test_x.py::test_a"], failed=[]),
        Verdict("p2", "pytest", passed=[], failed=["p2::tests/test_y.py::test_b"]),
    ]
    assert advance._outcome_from_verdicts(verdicts, "backend::tests/test_x.py::test_y") is None


def test_single_new_test_is_adopted_and_evaluated_in_one_advance(repo):
    plan = write_plan(repo, PLAN_SINGLE_CANDIDATE)
    run_cli(repo, "plan", "register", plan)
    run_cli(repo, "run", "start", "--plan", plan)

    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADDING)
    (repo / "backend" / "app" / "calc.py").write_text(CALC_STUB)

    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "write_implementation", out
    assert out["run"]["phase"] == "AWAITING_IMPL"


def test_disambiguate_picks_the_normalisation_match(tmp_path):
    adapter = _vitest_adapter(tmp_path)
    candidates = [
        "frontend::a.test.ts > helper formats a value",
        "frontend::b.test.ts > other case",
    ]
    declared = "frontend::a.test.ts > helper > formats a value"
    assert advance._disambiguate(candidates, declared, adapter) == candidates[0]


def test_unique_same_file_candidate_is_adopted_and_evaluated(repo):
    plan = write_plan(repo, PLAN_SINGLE_CANDIDATE)
    run_cli(repo, "plan", "register", plan)
    run_cli(repo, "run", "start", "--plan", plan)

    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADDING)
    (repo / "backend" / "app" / "calc.py").write_text(CALC_STUB)
    (repo / "backend" / "tests" / "test_other.py").write_text("def test_other_thing():\n    assert True\n")

    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "write_implementation", out
    assert out["run"]["phase"] == "AWAITING_IMPL"


def test_ambiguous_new_tests_still_ask_the_agent(repo):
    plan = write_plan(repo, PLAN_SINGLE_CANDIDATE)
    run_cli(repo, "plan", "register", plan)
    run_cli(repo, "run", "start", "--plan", plan)

    two_tests = """\
from app.calc import add


def test_adding_two():
    assert add(2, 3) == 5


def test_adding_three():
    assert add(1, 2) == 3
"""
    (repo / "backend" / "tests" / "test_add.py").write_text(two_tests)
    (repo / "backend" / "app" / "calc.py").write_text(CALC_STUB)

    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "name_target_test", out
    assert len(out["result"]["candidates"]) == 2


def test_adopted_passing_test_demands_sensitivity_in_one_advance(repo):
    plan = write_plan(repo, PLAN_SINGLE_CANDIDATE)
    run_cli(repo, "plan", "register", plan)
    run_cli(repo, "run", "start", "--plan", plan)

    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADDING)
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")

    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "run_sensitivity_check", out
