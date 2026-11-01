"""A plan's reference_paths are read-only to its run: changing one blocks it (#235)."""

from __future__ import annotations

import shutil

from conftest import git, run_cli, write_plan
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

PLAN_PIN = """---
cycles:
  - n: 1
    project: backend
    pin_cycle: true
    title: "smoke still passes"
    test: "tests/test_pin.py::test_pin"
reference_paths: ["backend/tests/expected/out.txt"]
---

# Plan
"""


def _commit_reference(repo):
    (repo / "backend" / "tests" / "expected").mkdir(parents=True)
    (repo / REFERENCE).write_text("reference\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "an independently produced reference file")


def _start(repo, plan_text):
    plan = write_plan(repo, plan_text)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    started = run_cli(repo, "run", "start", "--plan", plan)
    assert started["ok"], started
    return started


def _red(repo):
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text(STUB)


def _touch(repo):
    (repo / REFERENCE).write_text("overwritten by the run\n")


def _advance_expecting(repo, verb):
    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == verb, out


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


def _drive_red(repo):
    _start(repo, PLAN_ADD)
    _red(repo)
    _touch(repo)


def _drive_green(repo):
    _start(repo, PLAN_ADD)
    _red(repo)
    _advance_expecting(repo, "write_implementation")
    (repo / "backend" / "app" / "calc.py").write_text(REAL)
    _touch(repo)


def _drive_refactor(repo):
    _start(repo, PLAN_ADD)
    _red(repo)
    _advance_expecting(repo, "write_implementation")
    (repo / "backend" / "app" / "calc.py").write_text(REAL)
    _advance_expecting(repo, "refactor_or_advance")
    _touch(repo)


def _drive_pin(repo):
    _start(repo, PLAN_PIN)
    (repo / "backend" / "tests" / "test_pin.py").write_text("def test_pin():\n    assert True\n")
    _touch(repo)


def test_touching_a_reference_path_blocks_the_run_in_every_phase(repo, tmp_path):
    _commit_reference(repo)
    drives = {
        "red": _drive_red,
        "green": _drive_green,
        "refactor": _drive_refactor,
        "pin": _drive_pin,
    }
    seen = {}
    for name, drive in drives.items():
        copy = tmp_path / name
        shutil.copytree(repo, copy, symlinks=True)
        drive(copy)
        head = git(copy, "rev-parse", "HEAD")
        out = run_cli(copy, "advance")
        seen[name] = (
            out["next_action"]["verb"],
            out["result"].get("kind"),
            out["result"].get("paths"),
            git(copy, "rev-parse", "HEAD") == head,
            run_cli(copy, "metrics")["result"]["runs"][0]["outcome"],
        )
    blocked = ("blocked", "reference_path_touched", [REFERENCE], True, "blocked")
    assert seen == {"red": blocked, "green": blocked, "refactor": blocked, "pin": blocked}


def test_a_reference_path_committed_behind_the_tool_blocks_the_next_advance(repo):
    _commit_reference(repo)
    _start(repo, PLAN_ADD)
    _red(repo)
    _advance_expecting(repo, "write_implementation")
    _touch(repo)
    git(repo, "add", REFERENCE)
    git(repo, "commit", "-q", "-m", "regenerate the golden from the producer")
    (repo / "backend" / "app" / "calc.py").write_text(REAL)
    out = run_cli(repo, "advance")
    assert (
        out["next_action"]["verb"],
        out["result"].get("kind"),
        out["result"].get("paths"),
    ) == ("blocked", "reference_path_touched", [REFERENCE])
