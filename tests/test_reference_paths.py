"""A plan's reference_paths are read-only to its run: changing one blocks it (#235)."""

from __future__ import annotations

from conftest import run_cli, write_plan
from tddcli import gitutil
from tddcli.contract import ContractError, parse
from tddcli.ledger import Ledger

REFERENCE = "backend/tests/expected/out.txt"
TEST_ADD = "from app.calc import add\n\n\ndef test_add_two_numbers():\n    assert add(2, 3) == 5\n"
STUB = "def add(a, b):\n    raise NotImplementedError\n"
REAL = "def add(a, b):\n    return a + b\n"

PLAN_ADD = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    stub_expected: ["app/calc.py"]
reference_paths: ["backend/tests/expected/out.txt"]
---

# Plan
"""


def _contract_text(value: str | None) -> str:
    line = "" if value is None else f"reference_paths: {value}\n"
    return (
        "---\n"
        'cycles: [{n: 1, project: backend, test: "tests/test_a.py::test_a"}]\n'
        f"{line}"
        "---\n\n# Plan\n"
    )


def test_reference_paths_parse_as_a_list_of_strings_or_fail():
    cases = {
        "absent": None,
        "list": '["backend/tests/expected/out.txt", "docs/ref.bin"]',
        "string": '"docs/ref.bin"',
        "number": "[1]",
        "mapping": "{a: b}",
    }
    seen: dict[str, object] = {}
    for name, value in cases.items():
        try:
            seen[name] = parse(_contract_text(value), "tasks/plan.md").reference_paths
        except ContractError as exc:
            seen[name] = str(exc)
    assert seen == {
        "absent": [],
        "list": ["backend/tests/expected/out.txt", "docs/ref.bin"],
        "string": "reference_paths must be a list of strings",
        "number": "reference_paths must be a list of strings",
        "mapping": "reference_paths must be a list of strings",
    }


def test_plan_register_stores_reference_paths(repo):
    plan = write_plan(repo, PLAN_ADD)
    registered = run_cli(repo, "plan", "register", plan)
    assert Ledger(gitutil.repo_identity(repo)).reference_paths(
        registered["result"]["contract_id"]
    ) == [REFERENCE]
