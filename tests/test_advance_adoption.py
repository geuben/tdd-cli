from conftest import git, run_cli, write_plan

from tddcli import advance
from tddcli.adapters.base import Verdict

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
